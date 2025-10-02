"""
Сервисы для работы с полетами БАС.
Максимально оптимизированная асинхронная версия.
"""

import asyncio
import logging
import re
from datetime import datetime, time, timedelta
from typing import TYPE_CHECKING, Any, Optional

import pytz

if TYPE_CHECKING:
    from .models import RussianRegion
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

import pandas as pd
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.utils import timezone

from .models import (
    ActualFlight,
    DroneOperator,
    DroneType,
    FlightPlan,
    FlightZone,
    RussianRegion,
    RussianRegionWithWater,
)

logger = logging.getLogger(__name__)


class FlightDataParser:
    """Максимально оптимизированный асинхронный парсер данных о полетах."""

    def __init__(self):
        self.errors = []
        self.processed_count = 0
        self.created_count = 0
        self.duplicates_count = 0
        self.skipped_count = 0
        self.duplicates_count = 0
        self.actual_flights_count = 0

        self.validation_stats = {
            "total_rows": 0,
            "valid_shr": 0,
            "valid_dep": 0,
            "valid_arr": 0,
            "complete_flights": 0,
            "incomplete_flights": 0,
            "parsing_errors": 0,
            "only_shr": 0,
            "partial_dep_arr": 0,
            "flights_with_actual": 0,
        }

        self._operator_cache = {}
        self._drone_type_cache = {}
        self._flight_zone_cache = {}
        self._region_timezone_cache = {}
        self._flight_plans_batch = []
        self._actual_flights_batch = []
        self._batch_size = 5000
        self._processing_batch_size = 500

        self._regex_cache = self._compile_regex_patterns()

        self.utc_tz = pytz.UTC

    def _compile_regex_patterns(self) -> dict[str, re.Pattern]:
        """Предкомпиляция всех регулярных выражений."""
        patterns = {
            "flight_id": re.compile(r"SHR-([A-Z0-9]+)"),
            "sid": re.compile(r"SID/(\d+)"),
            "zzzz_times": re.compile(r"-ZZZZ(\d{4})"),
            "altitude": re.compile(r"-M(\d{4})/M(\d{4})"),
            "dep_coord": re.compile(r"DEP/(\d{4}N\d{5}E)"),
            "dest_coord": re.compile(r"DEST/(\d{4}N\d{5}E)"),
            "zona_coord": re.compile(r"(\d{4}N\d{5}E)"),
            "date": re.compile(r"DOF/(\d{6})"),
            "operator": re.compile(r"OPR/(.+?)(?:REG/|TYP/|RMK/|SID/|$)", re.DOTALL),
            "drone_type": re.compile(r"TYP/([A-Z]+)"),
            "reg_number": re.compile(r"REG/([^,\s]+)"),
            "zona_matches": [
                re.compile(r"/ZONA\s+([A-Z0-9,.\s]+?)/"),
                re.compile(r"ZONA\s+([A-Z0-9,.\s]+)"),
                re.compile(r"WR(\d+)"),
            ],
            "purpose": re.compile(r"RMK/(.+?)(?:SID/|$)", re.DOTALL),
            "phone": re.compile(r"\+?7?\d{10,11}"),
            "coord_standard": re.compile(r"(\d{2})(\d{2})([NS])(\d{3})(\d{2})([EW])"),
            "coord_extended": re.compile(
                r"(\d{2})(\d{2})(\d{2})([NS])(\d{3})(\d{2})(\d{2})([EW])"
            ),
            # DEP/ARR паттерны
            "dep_date": re.compile(r"-ADD\s+(\d{6})"),
            "dep_time": re.compile(r"-ATD\s+(\d{4})"),
            "dep_coord_ext": re.compile(r"-ADEPZ\s+(\d{6}N\d{7}E)"),
            "arr_date": re.compile(r"-ADA\s+(\d{6})"),
            "arr_time": re.compile(r"-ATA\s+(\d{4})"),
            "arr_coord_ext": re.compile(r"-ADARRZ\s+(\d{6}N\d{7}E)"),
        }
        return patterns

    async def parse_excel_file_optimized(self, excel_file) -> dict[str, Any]:
        """
        Максимально оптимизированный асинхронный парсинг Excel файла.
        """
        self.errors = []
        self.processed_count = 0
        self.created_count = 0
        self.duplicates_count = 0

        self._operator_cache.clear()
        self._drone_type_cache.clear()
        self._flight_zone_cache.clear()
        self._flight_plans_batch.clear()
        self._actual_flights_batch.clear()

        self.skipped_count = 0
        self.actual_flights_count = 0
        self.validation_stats = {
            "total_rows": 0,
            "valid_shr": 0,
            "valid_dep": 0,
            "valid_arr": 0,
            "complete_flights": 0,
            "incomplete_flights": 0,
            "parsing_errors": 0,
            "only_shr": 0,
            "partial_dep_arr": 0,
            "invalid_dep_arr": 0,
        }

        try:

            logger.info("🚀 Начинаю стриминговую обработку большого Excel файла")

            total_rows = 0

            logger.info("📏 Подсчитываю общее количество строк...")
            df_temp = pd.read_excel(
                excel_file,
                sheet_name=0,
                usecols=["SHR"],
                dtype=str,
                engine="openpyxl",
            )
            total_rows = len(df_temp.dropna(subset=["SHR"]))
            del df_temp

            logger.info(f"📊 Обнаружено {total_rows} строк данных")

            if total_rows > 50000:
                logger.info("⚠️  БОЛЬШОЙ ФАЙЛ: активирован режим стриминговой обработки")
                result = await self._process_large_file_streaming(
                    excel_file, total_rows
                )
            else:
                logger.info("📂 Стандартная обработка")
                result = await self._process_standard_file(excel_file)

            return result

        except Exception as e:
            logger.error(f"Ошибка при оптимизированном парсинге: {e}")
            await self._enable_db_constraints()
            raise ValidationError(f"Ошибка при обработке файла: {str(e)}")

    async def _disable_db_constraints(self):
        """Агрессивная оптимизация БД для максимальной скорости."""
        from asgiref.sync import sync_to_async

        @sync_to_async
        def disable_constraints():
            with connection.cursor() as cursor:

                cursor.execute("SET autocommit = false;")

                cursor.execute("SET work_mem = '1GB';")
                cursor.execute("SET maintenance_work_mem = '1GB';")

                cursor.execute("SET synchronous_commit = off;")
                cursor.execute("SET fsync = off;")
                cursor.execute("SET checkpoint_segments = 32;")
                cursor.execute("SET wal_buffers = '16MB';")
                cursor.execute("SET shared_buffers = '512MB';")

                cursor.execute("SET full_page_writes = off;")

        try:
            await disable_constraints()
            logger.info("⚡ БД оптимизирована для максимальной скорости загрузки!")
        except Exception as e:
            logger.warning(f"Частичная оптимизация БД: {e}")

    async def _enable_db_constraints(self):
        """Полное восстановление безопасных настроек БД."""
        from asgiref.sync import sync_to_async

        @sync_to_async
        def enable_constraints():
            with connection.cursor() as cursor:
                cursor.execute("SET autocommit = true;")
                cursor.execute("SET work_mem = '4MB';")
                cursor.execute("SET maintenance_work_mem = '64MB';")
                cursor.execute("SET synchronous_commit = on;")
                cursor.execute("SET fsync = on;")
                cursor.execute("SET full_page_writes = on;")
                cursor.execute("SET shared_buffers = '128MB';")

        try:
            await enable_constraints()
            logger.info("🔒 БД настройки восстановлены в безопасный режим")
        except Exception as e:
            logger.warning(f"Частичное восстановление БД: {e}")

    async def _preload_caches_async(self):
        """Асинхронная предварительная загрузка кешей."""
        from asgiref.sync import sync_to_async

        @sync_to_async
        def load_caches():

            operators = list(DroneOperator.objects.all().values("id", "name"))
            for op in operators:
                self._operator_cache[op["name"].lower()[:100]] = op["id"]

            drone_types = list(DroneType.objects.all().values("id", "code"))
            for dt in drone_types:
                self._drone_type_cache[dt["code"]] = dt["id"]

            flight_zones = list(FlightZone.objects.all().values("id", "code"))
            for fz in flight_zones:
                self._flight_zone_cache[fz["code"]] = fz["id"]

            regions = list(
                RussianRegion.objects.exclude(timezone="").values("code", "timezone")
            )
            for region in regions:
                try:
                    timezone_obj = pytz.timezone(region["timezone"])
                    self._region_timezone_cache[region["code"]] = timezone_obj
                except pytz.exceptions.UnknownTimeZoneError:
                    logger.warning(
                        f"Некорректный часовой пояс {region['timezone']} для региона {region['code']}"
                    )
                    self._region_timezone_cache[region["code"]] = pytz.timezone(
                        "Europe/Moscow"
                    )

        await load_caches()
        logger.info(
            f"Асинхронные кеши загружены: операторы={len(self._operator_cache)}, "
            f"типы={len(self._drone_type_cache)}, зоны={len(self._flight_zone_cache)}, "
            f"часовые пояса регионов={len(self._region_timezone_cache)}"
        )

    async def _process_dataframe_super_async(self, df: pd.DataFrame) -> dict[str, Any]:
        """Супер-асинхронная обработка с максимальным параллелизмом."""

        chunk_size = 1000
        chunks = [df.iloc[i : i + chunk_size] for i in range(0, len(df), chunk_size)]

        logger.info(
            f"🔄 Запускаю параллельную обработку {len(chunks)} блоков данных..."
        )

        with ProcessPoolExecutor(max_workers=12) as process_executor:
            parse_futures = []
            for chunk_idx, chunk in enumerate(chunks):
                future = process_executor.submit(
                    self._process_chunk_in_process, chunk, chunk_idx, self._regex_cache
                )
                parse_futures.append(future)

            parsed_batches = []
            completed_chunks = 0
            total_chunks = len(parse_futures)

            for future in as_completed(parse_futures):
                try:
                    batch_result = future.result()
                    if batch_result["data"]:
                        parsed_batches.extend(batch_result["data"])
                    self.processed_count += batch_result["processed"]
                    self.errors.extend(batch_result["errors"])

                    completed_chunks += 1
                    progress = (completed_chunks / total_chunks) * 100
                    logger.info(
                        f"📊 Прогресс парсинга: {completed_chunks}/{total_chunks} блоков ({progress:.1f}%)"
                    )

                except Exception as e:
                    logger.error(f"Ошибка в процессе парсинга: {e}")
                    completed_chunks += 1

        if parsed_batches:
            logger.info(
                f"💾 Начинаю сохранение {len(parsed_batches)} записей в базу данных..."
            )
            await self._super_bulk_save(parsed_batches)
            logger.info("✅ Сохранение завершено успешно!")

        return {
            "processed": self.processed_count,
            "created": self.created_count,
            "actual_flights_created": self.actual_flights_count,
            "skipped": self.skipped_count,
            "duplicates": self.duplicates_count,
            "errors": len(self.errors),
            "error_messages": self.errors,
            "validation_stats": self.validation_stats,
        }

    @staticmethod
    def _process_chunk_in_process(
        chunk: pd.DataFrame, chunk_idx: int, regex_cache: dict
    ) -> dict[str, Any]:
        """Обработка чанка в отдельном процессе (статический метод)."""
        errors = []
        processed = 0
        parsed_data = []

        for index, row in chunk.iterrows():
            try:
                shr_data = str(row.get("SHR", ""))
                dep_data = str(row.get("DEP", ""))
                arr_data = str(row.get("ARR", ""))

                has_shr = shr_data and shr_data != "nan" and shr_data.strip()
                has_dep = dep_data and dep_data != "nan" and dep_data.strip()
                has_arr = arr_data and arr_data != "nan" and arr_data.strip()

                if not has_shr:
                    errors.append(f"Строка {index + 2}: Отсутствует SHR данные")
                    continue

                if not has_dep:
                    errors.append(f"Строка {index + 2}: Отсутствует DEP данные")
                    continue

                if not has_arr:
                    errors.append(f"Строка {index + 2}: Отсутствует ARR данные")
                    continue

                if not FlightDataParser._validate_shr_template(shr_data):
                    errors.append(
                        f"Строка {index + 2}: SHR данные не соответствуют шаблону (должны начинаться с SHR)"
                    )
                    continue

                if not FlightDataParser._validate_dep_template(dep_data):
                    errors.append(
                        f"Строка {index + 2}: DEP данные не соответствуют шаблону (должны начинаться с -TITLE)"
                    )
                    continue

                if not FlightDataParser._validate_arr_template(arr_data):
                    errors.append(
                        f"Строка {index + 2}: ARR данные не соответствуют шаблону (должны начинаться с -TITLE)"
                    )
                    continue

                flight_data = FlightDataParser._parse_shr_fast(shr_data, regex_cache)
                if not flight_data:
                    errors.append(f"Строка {index + 2}: Не удалось парсить SHR данные")
                    continue

                actual_data = FlightDataParser._parse_dep_arr_fast(
                    dep_data, arr_data, regex_cache
                )

                parsed_data.append(
                    {
                        "flight_data": flight_data,
                        "actual_data": actual_data,
                        "row_index": index,
                    }
                )
                processed += 1

            except Exception as e:
                error_msg = f"Строка {index + 2}: {str(e)}"
                errors.append(error_msg)
                logger.error(
                    f"ДЕТАЛЬНАЯ ОШИБКА быстрого парсинга строки {index + 2}: {e}"
                )
                logger.error(
                    f"SHR данные: {shr_data[:100] if 'shr_data' in locals() else 'N/A'}..."
                )
                logger.error(
                    f"DEP данные: {dep_data[:100] if 'dep_data' in locals() else 'N/A'}..."
                )
                logger.error(
                    f"ARR данные: {arr_data[:100] if 'arr_data' in locals() else 'N/A'}..."
                )

        logger.info(
            f"⚙️  Процесс {chunk_idx}: обработано {processed} строк, ошибок: {len(errors)}"
        )
        return {"data": parsed_data, "processed": processed, "errors": errors}

    @staticmethod
    def _validate_shr_template(shr_text: str) -> bool:
        """Валидация шаблона SHR данных."""
        if not shr_text or shr_text == "nan":
            return False

        cleaned_text = shr_text.strip()

        return cleaned_text.startswith("SHR")

    @staticmethod
    def _validate_dep_template(dep_text: str) -> bool:
        """Валидация шаблона DEP данных."""
        if not dep_text or dep_text == "nan":
            return False

        cleaned_text = dep_text.strip()

        return cleaned_text.startswith("-TITLE")

    @staticmethod
    def _validate_arr_template(arr_text: str) -> bool:
        """Валидация шаблона ARR данных."""
        if not arr_text or arr_text == "nan":
            return False

        cleaned_text = arr_text.strip()

        return cleaned_text.startswith("-TITLE")

    @staticmethod
    def _parse_shr_fast(shr_text: str, regex_cache: dict) -> dict[str, Any] | None:
        """Максимально быстрый парсинг SHR с предкомпилированными regex."""
        if not shr_text:
            return None

        cleaned_text = (
            shr_text.strip().replace("(", "").replace(")", "").replace('"', "")
        )
        data = {}

        try:

            match = regex_cache["flight_id"].search(cleaned_text)
            if match:
                flight_id = match.group(1)
                data["flight_id"] = (
                    flight_id[:47] + "..." if len(flight_id) > 50 else flight_id
                )

            match = regex_cache["sid"].search(cleaned_text)
            if match:
                sid = match.group(1)
                data["sid"] = sid[:17] + "..." if len(sid) > 20 else sid

            times = regex_cache["zzzz_times"].findall(cleaned_text)
            if len(times) >= 1:
                data["departure_time"] = times[0]
            if len(times) >= 2:
                data["duration"] = FlightDataParser._calc_duration_fast(
                    times[0], times[1]
                )

            match = regex_cache["altitude"].search(cleaned_text)
            if match:
                data["min_alt"] = int(match.group(1))
                data["max_alt"] = int(match.group(2))

            match = regex_cache["dep_coord"].search(cleaned_text)
            if match:
                data["dep_coords"] = match.group(1)

            match = regex_cache["dest_coord"].search(cleaned_text)
            if match:
                data["dest_coords"] = match.group(1)
            elif not data.get("dest_coords"):
                match = regex_cache["zona_coord"].search(cleaned_text)
                if match:
                    data["dep_coords"] = data.get("dep_coords", match.group(1))
                    data["dest_coords"] = match.group(1)

            match = regex_cache["date"].search(cleaned_text)
            if match:
                data["date"] = match.group(1)

            match = regex_cache["operator"].search(cleaned_text)
            if match:
                data["operator"] = match.group(1).strip()[:1000]

            match = regex_cache["drone_type"].search(cleaned_text)
            if match:
                data["drone_type"] = match.group(1)

            match = regex_cache["reg_number"].search(cleaned_text)
            if match:
                reg = match.group(1).strip()
                data["reg_number"] = reg[:47] + "..." if len(reg) > 50 else reg

            match = regex_cache["purpose"].search(cleaned_text)
            if match:
                data["purpose"] = match.group(1).strip()

            return data

        except Exception:
            return None

    @staticmethod
    def _parse_dep_arr_fast(
        dep_text: str, arr_text: str, regex_cache: dict
    ) -> dict[str, Any] | None:
        """Быстрый парсинг DEP/ARR."""
        data = {}

        try:
            if dep_text and dep_text != "nan":
                dep_clean = dep_text.strip().replace('"', "")

                match = regex_cache["dep_date"].search(dep_clean)
                if match:
                    data["dep_date"] = match.group(1)

                match = regex_cache["dep_time"].search(dep_clean)
                if match:
                    data["dep_time"] = match.group(1)

                match = regex_cache["dep_coord_ext"].search(dep_clean)
                if match:
                    data["dep_coords_ext"] = match.group(1)

            if arr_text and arr_text != "nan":
                arr_clean = arr_text.strip().replace('"', "")

                match = regex_cache["arr_date"].search(arr_clean)
                if match:
                    data["arr_date"] = match.group(1)

                match = regex_cache["arr_time"].search(arr_clean)
                if match:
                    data["arr_time"] = match.group(1)

                match = regex_cache["arr_coord_ext"].search(arr_clean)
                if match:
                    data["arr_coords_ext"] = match.group(1)

            result = {
                "raw_data": {
                    "dep": dep_text if dep_text and dep_text != "nan" else "",
                    "arr": arr_text if arr_text and arr_text != "nan" else "",
                }
            }
            result.update(data)
            return result

        except Exception:
            return {
                "raw_data": {
                    "dep": dep_text if dep_text and dep_text != "nan" else "",
                    "arr": arr_text if arr_text and arr_text != "nan" else "",
                }
            }

    @staticmethod
    def _validate_actual_flight_data(actual_data: dict[str, Any]) -> bool:
        """
        Гибкая валидация фактических данных полета.
        Требует наличия хотя бы одного фактического параметра.
        """
        if not actual_data:
            return False

        has_any_dep = (
            actual_data.get("actual_departure_date")
            or actual_data.get("actual_departure_time")
            or actual_data.get("actual_departure_point")
            or actual_data.get("dep_date")
            or actual_data.get("dep_time")
        )

        has_any_arr = (
            actual_data.get("actual_arrival_date")
            or actual_data.get("actual_arrival_time")
            or actual_data.get("actual_destination_point")
            or actual_data.get("arr_date")
            or actual_data.get("arr_time")
        )

        return has_any_dep or has_any_arr

    def _get_regional_timezone(
        self, departure_region_code: str = None, destination_region_code: str = None
    ) -> pytz.BaseTzInfo:
        """
        Получение часового пояса на основе регионов полета из базы данных.

        Args:
            departure_region_code: Код региона вылета
            destination_region_code: Код региона назначения

        Returns:
            Часовой пояс региона или московское время по умолчанию
        """

        region_code = departure_region_code or destination_region_code

        if region_code:

            if region_code in self._region_timezone_cache:
                return self._region_timezone_cache[region_code]

            try:

                region = RussianRegion.objects.filter(code=region_code).first()
                timezone_obj = None

                if region and region.timezone:
                    try:
                        timezone_obj = pytz.timezone(region.timezone)

                        self._region_timezone_cache[region_code] = timezone_obj
                        return timezone_obj
                    except pytz.exceptions.UnknownTimeZoneError:
                        logger.warning(
                            f"Неизвестный часовой пояс из БД: {region.timezone} для региона {region_code}"
                        )
                elif region:
                    logger.debug(
                        f"У региона {region_code} ({region.name}) не указан часовой пояс"
                    )
                else:
                    logger.debug(f"Регион с кодом {region_code} не найден в БД")

            except Exception as e:
                logger.error(
                    f"Ошибка при получении часового пояса для региона {region_code}: {e}"
                )

            moscow_tz = pytz.timezone("Europe/Moscow")
            self._region_timezone_cache[region_code] = moscow_tz
            return moscow_tz

        return pytz.timezone("Europe/Moscow")

    def _convert_utc_to_regional(
        self, utc_datetime: datetime, region_code: str = None
    ) -> datetime:
        """
        Конвертация времени из UTC в региональное время.

        Args:
            utc_datetime: Datetime в UTC
            region_code: Код региона для определения часового пояса

        Returns:
            Datetime в региональном времени
        """
        if not utc_datetime:
            return utc_datetime

        try:

            if utc_datetime.tzinfo is not None:
                utc_dt = utc_datetime.astimezone(self.utc_tz)
            else:

                utc_dt = self.utc_tz.localize(utc_datetime)

            regional_tz = self._get_regional_timezone(region_code)

            regional_dt = utc_dt.astimezone(regional_tz)

            logger.debug(
                f"Конвертация времени: {utc_datetime} UTC -> {regional_dt.replace(tzinfo=None)} {regional_tz} (регион: {region_code})"
            )

            return regional_dt.replace(tzinfo=None)

        except Exception as e:
            logger.error(
                f"Ошибка конвертации времени UTC->Regional для региона {region_code}: {e}"
            )
            logger.debug(f"UTC datetime: {utc_datetime}, region_code: {region_code}")
            return utc_datetime

    def _parse_time_with_timezone_conversion(
        self, time_str: str, date_obj: datetime.date = None, region_code: str = None
    ) -> time:
        """
        Парсинг времени с конвертацией из UTC в региональное время.

        Args:
            time_str: Строка времени в формате HHMM
            date_obj: Дата для создания полного datetime
            region_code: Код региона для часового пояса

        Returns:
            time объект в региональном времени
        """
        if not time_str or len(time_str) != 4:
            return time(0, 0)

        try:
            hours = int(time_str[:2])
            minutes = int(time_str[2:])

            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                return time(0, 0)

            if date_obj and region_code:
                utc_datetime = datetime.combine(date_obj, time(hours, minutes))
                regional_datetime = self._convert_utc_to_regional(
                    utc_datetime, region_code
                )
                return regional_datetime.time()
            else:

                return time(hours, minutes)

        except ValueError:
            return time(0, 0)

    def _calculate_actual_flight_duration(self, dep_date, dep_time, arr_date, arr_time):
        """
        Расчет фактической продолжительности полета.

        Args:
            dep_date: Дата вылета (datetime.date)
            dep_time: Время вылета (datetime.time)
            arr_date: Дата прилета (datetime.date)
            arr_time: Время прилета (datetime.time)

        Returns:
            timedelta или None
        """
        try:

            departure_datetime = datetime.combine(dep_date, dep_time)
            arrival_datetime = datetime.combine(arr_date, arr_time)

            duration = arrival_datetime - departure_datetime

            if timedelta(minutes=1) <= duration <= timedelta(hours=24):
                return duration
            else:
                logger.warning(f"Неразумная продолжительность полета: {duration}")
                return None

        except Exception as e:
            logger.error(f"Ошибка расчета продолжительности полета: {e}")
            return None

    @staticmethod
    def _calc_duration_fast(start: str, end: str) -> int:
        """Быстрый расчет продолжительности в минутах."""
        try:
            start_mins = int(start[:2]) * 60 + int(start[2:])
            end_mins = int(end[:2]) * 60 + int(end[2:])

            if end_mins < start_mins:
                end_mins += 24 * 60

            return max(60, min(24 * 60, end_mins - start_mins))
        except:
            return 60

    async def _super_bulk_save(self, parsed_batches: list[dict[str, Any]]):
        """Супер-быстрое массовое сохранение."""
        logger.info(f"Начинаю супер-bulk сохранение {len(parsed_batches)} записей")

        super_batch_size = 10000
        total_created = 0

        for i in range(0, len(parsed_batches), super_batch_size):
            batch = parsed_batches[i : i + super_batch_size]

            try:
                result = await self._save_super_batch(batch)
                if isinstance(result, dict):
                    created_count = result["created"]
                    duplicates_count = result["duplicates"]
                    total_created += created_count
                    self.duplicates_count += duplicates_count
                else:

                    created_count = result
                    total_created += created_count
                logger.info(
                    f"Супер-батч сохранен: {created_count} записей, пропущено дубликатов: {duplicates_count if isinstance(result, dict) else 0}"
                )

            except Exception as e:
                logger.error(f"Ошибка супер-батча: {e}")

                for j in range(0, len(batch), 100):
                    small_batch = batch[j : j + 100]
                    try:
                        result = await self._save_super_batch(small_batch)
                        if isinstance(result, dict):
                            created = result["created"]
                            duplicates_count = result["duplicates"]
                            total_created += created
                            self.duplicates_count += duplicates_count
                        else:

                            created = result
                            total_created += created
                    except Exception as e2:
                        logger.error(f"Ошибка малого батча: {e2}")

        self.created_count = total_created
        logger.info(f"Супер-bulk завершен: {total_created} записей")

    async def _save_super_batch(self, batch: list[dict[str, Any]]) -> int:
        """Сохранение супер-батча с максимальной оптимизацией."""
        from asgiref.sync import sync_to_async

        @sync_to_async
        def save_batch_optimized():
            from django.db import connection

            with connection.cursor() as cursor:

                flight_plans_data = []

                for item in batch:
                    flight_data = item["flight_data"]

                    operator_id = self._get_operator_id_fast(
                        flight_data.get("operator", "")
                    )
                    drone_type_id = self._get_drone_type_id_fast(
                        flight_data.get("drone_type", "BLA")
                    )

                    flight_plan_data = {
                        "flight_id": flight_data.get(
                            "flight_id", f"UK_{len(flight_plans_data)}"
                        ),
                        "sid": flight_data.get("sid", ""),
                        "reg_number": flight_data.get("reg_number", ""),
                        "operator_id": operator_id,
                        "drone_type_id": drone_type_id,
                    }
                    flight_plans_data.append(flight_plan_data)

                flight_plans = []
                for data in flight_plans_data:
                    fp = FlightPlan(**data)
                    flight_plans.append(fp)

                filtered_flight_plans = []
                sids_to_check = [fp.sid for fp in flight_plans if fp.sid]
                duplicates_found = 0

                if sids_to_check:

                    existing_sids = set(
                        FlightPlan.objects.filter(sid__in=sids_to_check).values_list(
                            "sid", flat=True
                        )
                    )

                    for fp in flight_plans:
                        if not fp.sid or fp.sid not in existing_sids:
                            filtered_flight_plans.append(fp)
                        else:
                            duplicates_found += 1
                            logger.debug(
                                f"Пропускаем дублирующий план полета с SID: {fp.sid}"
                            )
                else:
                    filtered_flight_plans = flight_plans

                created = FlightPlan.objects.bulk_create(
                    filtered_flight_plans, batch_size=10000, ignore_conflicts=True
                )

                return {"created": len(created), "duplicates": duplicates_found}

        return await save_batch_optimized()

    def _get_operator_id_fast(self, operator_info: str) -> str:
        """Быстрое получение ID оператора из кеша."""
        if not operator_info:
            return self._drone_type_cache.get("DEFAULT_OPERATOR")

        normalized = operator_info.lower()[:100]
        return self._operator_cache.get(
            normalized, self._create_operator_fast(operator_info)
        )

    def _get_drone_type_id_fast(self, code: str) -> str:
        """Быстрое получение ID типа БАС."""
        return self._drone_type_cache.get(code, self._drone_type_cache.get("BLA"))

    def _create_operator_fast(self, operator_info: str) -> str:
        """Быстрое создание оператора."""
        try:
            operator = DroneOperator.objects.create(
                name=operator_info[:500], organization_type="Прочие"
            )
            return operator.id
        except:
            return self._drone_type_cache.get("DEFAULT_OPERATOR")

    async def _process_large_file_streaming(
        self, excel_file, total_rows: int
    ) -> dict[str, Any]:
        """Стриминговая обработка очень больших файлов (76k+ записей)."""

        logger.info("⚡ Активирован режим стриминговой обработки для больших файлов")

        await self._disable_db_constraints()
        await self._preload_caches_async()

        chunk_size = 1000
        processed_total = 0

        try:

            for chunk_start in range(0, total_rows, chunk_size):
                chunk_end = min(chunk_start + chunk_size, total_rows)
                logger.info(
                    f"📦 Обрабатываю чанк {chunk_start // chunk_size + 1}/{(total_rows + chunk_size - 1) // chunk_size}: строки {chunk_start}-{chunk_end}"
                )

                df_chunk = pd.read_excel(
                    excel_file,
                    sheet_name=0,
                    usecols=["SHR", "DEP", "ARR"],
                    dtype=str,
                    engine="openpyxl",
                    skiprows=range(1, chunk_start + 1),
                    nrows=chunk_end - chunk_start,
                )

                df_chunk = df_chunk.dropna(subset=["SHR"])
                df_chunk = df_chunk[df_chunk["SHR"] != "nan"]

                if len(df_chunk) == 0:
                    continue

                await self._process_dataframe_super_async(df_chunk)
                processed_total += len(df_chunk)

                del df_chunk

                progress = (processed_total / total_rows) * 100
                logger.info(
                    f"🎯 Общий прогресс: {processed_total}/{total_rows} ({progress:.1f}%)"
                )

                await asyncio.sleep(0.1)

        finally:
            await self._enable_db_constraints()

        return {
            "processed": self.processed_count,
            "created": self.created_count,
            "actual_flights_created": self.actual_flights_count,
            "skipped": self.skipped_count,
            "duplicates": self.duplicates_count,
            "errors": len(self.errors),
            "error_messages": self.errors,
            "validation_stats": self.validation_stats,
        }

    async def _process_standard_file(self, excel_file) -> dict[str, Any]:
        """Стандартная обработка для файлов < 50k записей."""

        df = pd.read_excel(
            excel_file,
            sheet_name=0,
            usecols=["SHR", "DEP", "ARR"],
            dtype=str,
            engine="openpyxl",
        )

        df = df.dropna(subset=["SHR"])
        df = df[df["SHR"] != "nan"]

        logger.info(
            f"⚙️  Настройки: батчи по {self._batch_size}, параллельная обработка {self._processing_batch_size} строк"
        )

        await self._disable_db_constraints()

        await self._preload_caches_async()

        result = await self._process_dataframe_super_async(df)

        await self._enable_db_constraints()

        return result

    parse_excel_file = parse_excel_file_optimized

    def parse_excel_file(self, excel_file) -> dict[str, Any]:
        """
        Синхронный парсинг Excel файла с данными о полетах.

        Args:
            excel_file: Загруженный Excel файл

        Returns:
            Dict с результатами парсинга
        """
        self.errors = []
        self.processed_count = 0
        self.created_count = 0
        self.duplicates_count = 0

        self._operator_cache.clear()
        self._drone_type_cache.clear()
        self._flight_zone_cache.clear()
        self._flight_plans_batch.clear()
        self._actual_flights_batch.clear()

        self.skipped_count = 0
        self.actual_flights_count = 0
        self.validation_stats = {
            "total_rows": 0,
            "valid_shr": 0,
            "valid_dep": 0,
            "valid_arr": 0,
            "complete_flights": 0,
            "incomplete_flights": 0,
            "parsing_errors": 0,
            "only_shr": 0,
            "partial_dep_arr": 0,
            "invalid_dep_arr": 0,
        }

        try:

            df = pd.read_excel(excel_file, sheet_name=0)
            logger.info(f"Начинаю асинхронную обработку {len(df)} строк")

            self._preload_caches()

            return asyncio.run(self._process_dataframe_async(df))

        except Exception as e:
            logger.error(f"Ошибка при парсинге Excel файла: {e}")
            raise ValidationError(f"Ошибка при обработке файла: {str(e)}")

    def _preload_caches(self):
        """Предварительная загрузка кешей для быстрого доступа."""

        for operator in DroneOperator.objects.all():
            self._operator_cache[operator.name.lower()[:100]] = operator

        for drone_type in DroneType.objects.all():
            self._drone_type_cache[drone_type.code] = drone_type

        for flight_zone in FlightZone.objects.all():
            self._flight_zone_cache[flight_zone.code] = flight_zone

        logger.info(
            f"Кеши загружены: операторы={len(self._operator_cache)}, "
            f"типы БАС={len(self._drone_type_cache)}, "
            f"зоны={len(self._flight_zone_cache)}"
        )

    async def _process_dataframe_async(self, df: pd.DataFrame) -> dict[str, Any]:
        """Асинхронная обработка DataFrame с батчами."""

        batch_size = 500
        batches = [df.iloc[i : i + batch_size] for i in range(0, len(df), batch_size)]

        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = [
                executor.submit(self._process_batch_sync, batch, batch_idx)
                for batch_idx, batch in enumerate(batches)
            ]

            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    self.processed_count += batch_results["processed"]
                    self.errors.extend(batch_results["errors"])
                except Exception as e:
                    logger.error(f"Ошибка при обработке батча: {e}")
                    self.errors.append(f"Ошибка батча: {str(e)}")

        await self._bulk_save_data()

        return {
            "processed": self.processed_count,
            "created": self.created_count,
            "actual_flights_created": self.actual_flights_count,
            "skipped": self.skipped_count,
            "duplicates": self.duplicates_count,
            "errors": len(self.errors),
            "error_messages": self.errors,
            "validation_stats": self.validation_stats,
        }

    def _process_batch_sync(
        self, batch: pd.DataFrame, batch_idx: int
    ) -> dict[str, Any]:
        """Синхронная обработка одного батча строк."""
        batch_errors = []
        processed = 0

        for index, row in batch.iterrows():
            try:

                shr_data = str(row.get("SHR", ""))
                dep_data = str(row.get("DEP", ""))
                arr_data = str(row.get("ARR", ""))

                if not shr_data or shr_data == "nan":
                    batch_errors.append(f"Строка {index + 2}: Отсутствует SHR данные")
                    continue

                has_dep = dep_data and dep_data != "nan" and dep_data.strip()
                has_arr = arr_data and arr_data != "nan" and arr_data.strip()

                if not has_dep:
                    batch_errors.append(f"Строка {index + 2}: Отсутствует DEP данные")
                    continue

                if not has_arr:
                    batch_errors.append(f"Строка {index + 2}: Отсутствует ARR данные")
                    continue

                flight_plan_data = self._parse_shr_data(shr_data)
                if not flight_plan_data:
                    batch_errors.append(
                        f"Строка {index + 2}: Не удалось извлечь данные плана полета из SHR"
                    )
                    continue

                actual_flight_data = self._parse_dep_arr_data(
                    dep_data, arr_data, flight_plan_data
                )

                self._add_to_batch(flight_plan_data, actual_flight_data, index)
                processed += 1

            except Exception as e:
                error_msg = f"Строка {index + 2}: {str(e)}"
                batch_errors.append(error_msg)
                logger.error(f"ДЕТАЛЬНАЯ ОШИБКА обработки строки {index + 2}: {e}")
                logger.error(
                    f"SHR данные: {shr_data[:100] if 'shr_data' in locals() else 'N/A'}..."
                )
                logger.error(
                    f"DEP данные: {dep_data[:100] if 'dep_data' in locals() else 'N/A'}..."
                )
                logger.error(
                    f"ARR данные: {arr_data[:100] if 'arr_data' in locals() else 'N/A'}..."
                )

        logger.info(
            f"Батч {batch_idx} обработан: {processed} строк, {len(batch_errors)} ошибок"
        )
        return {"processed": processed, "errors": batch_errors}

    def _add_to_batch(
        self,
        flight_plan_data: dict[str, Any],
        actual_flight_data: dict[str, Any],
        row_index: int,
    ):
        """Добавление данных в батчи для bulk операций."""

        operator = self._get_or_create_operator_cached(
            flight_plan_data.get("operator_info", "")
        )
        drone_type = self._get_or_create_drone_type_cached(
            flight_plan_data.get("drone_type_code", "BLA")
        )
        flight_zone = None
        if flight_plan_data.get("flight_zone_code"):
            flight_zone = self._get_or_create_flight_zone_cached(
                flight_plan_data["flight_zone_code"]
            )

        departure_region = None
        destination_region = None

        departure_point = flight_plan_data.get("departure_point", Point(0, 0))
        destination_point = flight_plan_data.get("destination_point", Point(0, 0))

        if departure_point and departure_point.x != 0 and departure_point.y != 0:
            departure_region = self._assign_region_by_coordinates(departure_point)

        if destination_point and destination_point.x != 0 and destination_point.y != 0:
            destination_region = self._assign_region_by_coordinates(destination_point)

        departure_region_code = departure_region.code if departure_region else None
        destination_region_code = (
            destination_region.code if destination_region else None
        )

        planned_departure_time_utc = flight_plan_data.get("planned_departure_time")
        if isinstance(planned_departure_time_utc, time) and flight_plan_data.get(
            "planned_date"
        ):

            utc_dt = datetime.combine(
                flight_plan_data["planned_date"], planned_departure_time_utc
            )
            regional_dt = self._convert_utc_to_regional(utc_dt, departure_region_code)
            planned_departure_time = regional_dt.time()
        else:
            planned_departure_time = planned_departure_time_utc or time(0, 0)

        flight_plan_obj = FlightPlan(
            flight_id=flight_plan_data.get(
                "flight_id",
                f"UNKNOWN_{timezone.now().strftime('%Y%m%d%H%M%S')}_{row_index}",
            ),
            sid=flight_plan_data.get("sid", ""),
            reg_number=flight_plan_data.get("reg_number", ""),
            planned_date=flight_plan_data.get("planned_date", timezone.now().date()),
            planned_departure_time=planned_departure_time,
            planned_duration=flight_plan_data.get(
                "planned_duration", timedelta(hours=1)
            ),
            min_altitude=flight_plan_data.get("min_altitude", 0),
            max_altitude=flight_plan_data.get("max_altitude", 100),
            departure_point=departure_point,
            destination_point=destination_point,
            departure_region=departure_region,
            destination_region=destination_region,
            operator=operator,
            drone_type=drone_type,
            flight_zone=flight_zone,
            purpose=flight_plan_data.get("purpose", ""),
            raw_data=flight_plan_data.get("raw_data", {}),
        )

        self._flight_plans_batch.append(
            {
                "flight_plan": flight_plan_obj,
                "actual_flight_data": actual_flight_data,
                "row_index": row_index,
                "temp_id": f"{row_index}_{flight_plan_obj.flight_id}",
            }
        )

    async def _bulk_save_data(self):
        """Массовое сохранение данных в базу."""
        if not self._flight_plans_batch:
            return

        logger.info(
            f"Начинаю bulk сохранение {len(self._flight_plans_batch)} планов полетов"
        )

        batch_size = self._batch_size
        total_created = 0

        for i in range(0, len(self._flight_plans_batch), batch_size):
            batch = self._flight_plans_batch[i : i + batch_size]

            try:

                batch_result = await self._save_batch_sync(batch, batch_size)
                if isinstance(batch_result, dict):
                    created_count = batch_result["created"]
                    duplicates_count = batch_result["duplicates"]
                    total_created += created_count
                    self.duplicates_count += duplicates_count
                else:

                    total_created += batch_result

            except Exception as e:
                logger.error(f"Ошибка при bulk сохранении батча: {e}")

                await self._fallback_single_save(batch)

        self.created_count = total_created
        logger.info(
            f"Bulk сохранение завершено: создано {total_created} планов полетов"
        )

    async def _save_batch_sync(
        self, batch: list[dict[str, Any]], batch_size: int
    ) -> int:
        """Синхронное сохранение батча в отдельном потоке."""
        from asgiref.sync import sync_to_async

        @sync_to_async
        def save_batch():
            with transaction.atomic():

                flight_plans = [item["flight_plan"] for item in batch]

                filtered_flight_plans = []
                sids_to_check = [fp.sid for fp in flight_plans if fp.sid]
                duplicates_found = 0

                if sids_to_check:

                    existing_sids = set(
                        FlightPlan.objects.filter(sid__in=sids_to_check).values_list(
                            "sid", flat=True
                        )
                    )

                    for fp in flight_plans:
                        if not fp.sid or fp.sid not in existing_sids:
                            filtered_flight_plans.append(fp)
                        else:
                            duplicates_found += 1
                            logger.debug(
                                f"Пропускаем дублирующий план полета с SID: {fp.sid}"
                            )
                else:
                    filtered_flight_plans = flight_plans

                created_flight_plans = FlightPlan.objects.bulk_create(
                    filtered_flight_plans, ignore_conflicts=True, batch_size=10000
                )

                created_count = len(created_flight_plans)

                if created_flight_plans:
                    actual_flights = []

                    actual_data_map = {}
                    for item in batch:
                        if item["actual_flight_data"]:
                            actual_data_map[item["flight_plan"].id] = item[
                                "actual_flight_data"
                            ]

                    for plan in created_flight_plans:
                        actual_data = actual_data_map.get(plan.id)
                        if actual_data:

                            dep_region_code = (
                                plan.departure_region.code
                                if plan.departure_region
                                else None
                            )
                            dest_region_code = (
                                plan.destination_region.code
                                if plan.destination_region
                                else None
                            )

                            actual_departure_time = actual_data.get(
                                "actual_departure_time"
                            )
                            actual_departure_date = actual_data.get(
                                "actual_departure_date"
                            )
                            if (
                                actual_departure_time
                                and actual_data.get("dep_time_utc_raw")
                                and actual_departure_date
                            ):
                                utc_dt = datetime.combine(
                                    actual_departure_date, actual_departure_time
                                )
                                regional_dt = self._convert_utc_to_regional(
                                    utc_dt, dep_region_code
                                )
                                actual_departure_time = regional_dt.time()
                                actual_departure_date = regional_dt.date()

                            actual_arrival_time = actual_data.get("actual_arrival_time")
                            actual_arrival_date = actual_data.get("actual_arrival_date")
                            if (
                                actual_arrival_time
                                and actual_data.get("arr_time_utc_raw")
                                and actual_arrival_date
                            ):
                                utc_dt = datetime.combine(
                                    actual_arrival_date, actual_arrival_time
                                )
                                regional_dt = self._convert_utc_to_regional(
                                    utc_dt, dest_region_code or dep_region_code
                                )
                                actual_arrival_time = regional_dt.time()
                                actual_arrival_date = regional_dt.date()

                            actual_duration = None
                            if (
                                actual_departure_date
                                and actual_departure_time
                                and actual_arrival_date
                                and actual_arrival_time
                            ):
                                actual_duration = (
                                    self._calculate_actual_flight_duration(
                                        actual_departure_date,
                                        actual_departure_time,
                                        actual_arrival_date,
                                        actual_arrival_time,
                                    )
                                )

                            actual_flight = ActualFlight(
                                flight_plan=plan,
                                actual_departure_date=actual_departure_date,
                                actual_departure_time=actual_departure_time,
                                actual_departure_point=actual_data.get(
                                    "actual_departure_point"
                                ),
                                actual_arrival_date=actual_arrival_date,
                                actual_arrival_time=actual_arrival_time,
                                actual_destination_point=actual_data.get(
                                    "actual_destination_point"
                                ),
                                actual_duration=actual_duration,
                                flight_status="completed",
                            )
                            actual_flights.append(actual_flight)

                    if actual_flights:
                        created_actual = ActualFlight.objects.bulk_create(
                            actual_flights, ignore_conflicts=True, batch_size=10000
                        )

                        self.actual_flights_count += len(created_actual)

                return {"created": created_count, "duplicates": duplicates_found}

        return await save_batch()

    async def _fallback_single_save(self, batch: list[dict[str, Any]]):
        """Резервное сохранение по одному объекту при ошибке bulk операции."""
        from asgiref.sync import sync_to_async

        @sync_to_async
        def save_single_item(item):
            try:
                with transaction.atomic():
                    flight_plan = item["flight_plan"]
                    flight_plan.save()

                    if item["actual_flight_data"]:
                        actual_flight = ActualFlight(
                            flight_plan=flight_plan,
                            **{
                                k: v
                                for k, v in item["actual_flight_data"].items()
                                if k.startswith("actual_")
                            },
                        )
                        actual_flight.save()

                    return 1
            except Exception as e:
                logger.error(
                    f"Ошибка fallback сохранения строки {item['row_index'] + 2}: {e}"
                )
                return 0

        saved_count = 0
        for item in batch:
            result = await save_single_item(item)
            saved_count += result

        self.created_count += saved_count

    def _assign_region_by_coordinates(self, point: Point) -> Optional["RussianRegion"]:
        """
        Определение региона по координатам точки.

        Args:
            point: Геопространственная точка

        Returns:
            Регион или None если не найден
        """
        try:

            region = RussianRegion.objects.filter(geometry__contains=point).first()

            if region:
                logger.debug(f"Точка {point} найдена в основном регионе {region.name}")
                return region

            water_region = RussianRegionWithWater.objects.filter(
                geometry__contains=point
            ).first()

            if water_region:

                corresponding_region = RussianRegion.objects.filter(
                    code=water_region.code
                ).first()

                if corresponding_region:
                    logger.debug(
                        f"Точка {point} найдена в водной границе региона {water_region.name}, "
                        f"назначен соответствующий основной регион {corresponding_region.name}"
                    )
                    return corresponding_region
                else:
                    logger.warning(
                        f"Найден водный регион {water_region.name} ({water_region.code}), "
                        f"но не найден соответствующий основной регион"
                    )

            logger.debug(
                f"Регион для точки {point} не найден ни в основных, ни в водных границах"
            )
            return None

        except Exception as e:
            logger.error(f"Ошибка при определении региона для точки {point}: {e}")
            return None

    def _get_or_create_operator_cached(self, operator_info: str) -> DroneOperator:
        """Получение или создание оператора БАС с кешированием."""
        if not operator_info:
            operator_info = "Неизвестный оператор"

        normalized_name = self._normalize_operator_name(operator_info)
        cache_key = normalized_name.lower()[:100]

        if cache_key in self._operator_cache:
            return self._operator_cache[cache_key]

        operator = self._create_operator_from_info(operator_info, normalized_name)
        self._operator_cache[cache_key] = operator
        return operator

    def _normalize_operator_name(self, operator_info: str) -> str:
        """Нормализация имени оператора."""
        operator_info = operator_info[:1000]

        phone_pattern = r"\+?7?\d{10,11}"
        phones = re.findall(phone_pattern, operator_info)

        name = operator_info
        for phone in phones:
            name = name.replace(phone, "")

        cleanup_words = ["ОПЕРАТОР", "АДМИНИСТРАЦИЯ", "РАЗРЕШЕНИЕ", "ТЕЛ", "TEL"]
        for word in cleanup_words:
            name = re.sub(r"\b" + word + r"\b", "", name, flags=re.IGNORECASE)

        name = re.sub(r"\s+", " ", name).strip()
        name = re.sub(r"^[.,\-\s]+", "", name)
        name = re.sub(r"[.,\-\s]+$", "", name)

        if not name or len(name) < 3:
            org_pattern = (
                r"^([А-ЯЁ\s]+(?:МВД|МЧС|АДМИНИСТРАЦИЯ|УПРАВЛЕНИЕ|СЛУЖБА)[А-ЯЁ\s]*)"
            )
            org_match = re.search(org_pattern, operator_info, re.IGNORECASE)
            name = org_match.group(1).strip() if org_match else "Оператор БАС"

        return name[:500]

    def _create_operator_from_info(
        self, operator_info: str, name: str
    ) -> DroneOperator:
        """Создание оператора из информации."""

        phone_pattern = r"\+?7?\d{10,11}"
        phones = re.findall(phone_pattern, operator_info)
        primary_phone = phones[0] if phones else ""

        if any(word in operator_info.upper() for word in ["МВД", "ПОЛИЦ"]):
            organization_type = "МВД"
        elif any(word in operator_info.upper() for word in ["МЧС", "СПАСАТЕЛЬН"]):
            organization_type = "МЧС"
        elif any(
            word in operator_info.upper() for word in ["АДМИНИСТРАЦИЯ", "МУНИЦИПАЛЬН"]
        ):
            organization_type = "Администрация"
        elif any(
            word in operator_info.upper() for word in ["УПРАВЛЕНИЕ", "ДЕПАРТАМЕНТ"]
        ):
            organization_type = "Государственный орган"
        elif any(word in operator_info.upper() for word in ["СЛУЖБА"]):
            organization_type = "Служба"
        else:
            organization_type = "Прочие"

        operator, created = DroneOperator.objects.get_or_create(
            name=name,
            defaults={
                "phone": primary_phone[:20],
                "organization_type": organization_type[:200],
            },
        )

        return operator

    def _get_or_create_drone_type_cached(self, code: str) -> DroneType:
        """Получение или создание типа БАС с кешированием."""
        if not code:
            code = "BLA"

        if code in self._drone_type_cache:
            return self._drone_type_cache[code]

        type_names = {
            "BLA": "Беспилотная авиационная система",
            "AER": "Аэростат",
            "UAV": "Беспилотный летательный аппарат",
        }

        drone_type, created = DroneType.objects.get_or_create(
            code=code,
            defaults={
                "name": type_names.get(code, f"БАС типа {code}"),
                "description": f"Автоматически созданный тип {code}",
            },
        )

        self._drone_type_cache[code] = drone_type
        return drone_type

    def _get_or_create_flight_zone_cached(self, code: str) -> FlightZone:
        """Получение или создание зоны полета с кешированием."""
        if not code:
            code = "UNKNOWN"

        original_code = code
        code = code[:50]
        if len(original_code) > 50:
            code = original_code[:20] + "..." + original_code[-20:]
            if len(code) > 50:
                code = original_code[:47] + "..."
        code = re.sub(r"\s+", " ", code).strip()

        if code in self._flight_zone_cache:
            return self._flight_zone_cache[code]

        flight_zone, created = FlightZone.objects.get_or_create(
            code=code, defaults={"name": f"Зона {code}"}
        )

        self._flight_zone_cache[code] = flight_zone
        return flight_zone

    def _parse_shr_data(self, shr_text: str) -> dict[str, Any] | None:
        """Парсинг данных из столбца SHR (план полета)."""
        if not shr_text:
            return None

        cleaned_text = (
            shr_text.strip().replace("(", "").replace(")", "").replace('"', "")
        )
        data = {"raw_data": {"shr": cleaned_text}}

        try:

            flight_id_match = re.search(r"SHR-([A-Z0-9]+)", cleaned_text)
            if flight_id_match:
                flight_id_value = flight_id_match.group(1)
                if flight_id_value == "ZZZZZ":
                    data["flight_id"] = "ZZZZZ"
                    reg_match = re.search(r"REG/([^,\s]+)", cleaned_text)
                    if reg_match:
                        reg_number = reg_match.group(1).strip()

                        if len(reg_number) > 50:
                            reg_number = reg_number[:47] + "..."
                        data["reg_number"] = reg_number
                    else:
                        data["reg_number"] = ""
                else:

                    if len(flight_id_value) > 50:
                        flight_id_value = flight_id_value[:47] + "..."
                    data["flight_id"] = flight_id_value
                    reg_match = re.search(r"REG/([^,\s]+)", cleaned_text)
                    if reg_match:
                        reg_number = reg_match.group(1).strip()
                        if len(reg_number) > 50:
                            reg_number = reg_number[:47] + "..."
                        data["reg_number"] = reg_number

            sid_match = re.search(r"SID/(\d+)", cleaned_text)
            if sid_match:
                sid_value = sid_match.group(1)

                if len(sid_value) > 20:
                    sid_value = sid_value[:17] + "..."
                data["sid"] = sid_value

            time_matches = re.findall(r"-ZZZZ(\d{4})", cleaned_text)
            if len(time_matches) >= 1:

                data["planned_departure_time_utc_raw"] = time_matches[0]
                data["planned_departure_time"] = self._parse_time(time_matches[0])
            if len(time_matches) >= 2:
                data["planned_duration"] = self._parse_duration(
                    time_matches[0], time_matches[1]
                )
            else:
                data["planned_duration"] = timedelta(hours=1)

            altitude_match = re.search(r"-M(\d{4})/M(\d{4})", cleaned_text)
            if altitude_match:
                data["min_altitude"] = int(altitude_match.group(1))
                data["max_altitude"] = int(altitude_match.group(2))

            dep_coord_match = re.search(r"DEP/(\d{4}N\d{5}E)", cleaned_text)
            if dep_coord_match:
                data["departure_point"] = self._parse_coordinates(
                    dep_coord_match.group(1)
                )

            dest_coord_match = re.search(r"DEST/(\d{4}N\d{5}E)", cleaned_text)
            if dest_coord_match:
                data["destination_point"] = self._parse_coordinates(
                    dest_coord_match.group(1)
                )

            if "destination_point" not in data:
                zona_coord_match = re.search(r"(\d{4}N\d{5}E)", cleaned_text)
                if zona_coord_match:
                    coord_str = zona_coord_match.group(1)
                    if "departure_point" not in data:
                        data["departure_point"] = self._parse_coordinates(coord_str)
                    data["destination_point"] = self._parse_coordinates(coord_str)

            date_match = re.search(r"DOF/(\d{6})", cleaned_text)
            if date_match:
                data["planned_date"] = self._parse_date(date_match.group(1))

            opr_match = re.search(
                r"OPR/(.+?)(?:REG/|TYP/|RMK/|SID/|$)", cleaned_text, re.DOTALL
            )
            if opr_match:
                data["operator_info"] = re.sub(r"\s+", " ", opr_match.group(1).strip())

            typ_match = re.search(r"TYP/([A-Z]+)", cleaned_text)
            if typ_match:
                data["drone_type_code"] = typ_match.group(1)

            zona_matches = [
                re.search(r"/ZONA\s+([A-Z0-9,.\s]+?)/", cleaned_text),
                re.search(r"ZONA\s+([A-Z0-9,.\s]+)", cleaned_text),
                re.search(r"WR(\d+)", cleaned_text),
            ]
            for zona_match in zona_matches:
                if zona_match:
                    zone_code = zona_match.group(1).strip()
                    if zone_code:
                        data["flight_zone_code"] = zone_code
                        break

            rmk_match = re.search(r"RMK/(.+?)(?:SID/|$)", cleaned_text, re.DOTALL)
            if rmk_match:
                data["purpose"] = re.sub(r"\s+", " ", rmk_match.group(1).strip())

            return data

        except Exception as e:
            logger.error(f"Ошибка парсинга SHR данных: {e}")
            return None

    def _parse_dep_arr_data(
        self,
        dep_text: str,
        arr_text: str,
        flight_plan_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Парсинг данных DEP и ARR."""
        data = {"raw_data": {"dep": dep_text, "arr": arr_text}}

        try:
            if dep_text and dep_text != "nan" and dep_text.strip():
                dep_clean = dep_text.strip().replace('"', "")

                dep_date_match = re.search(r"-ADD\s+(\d{6})", dep_clean)
                if dep_date_match:
                    dep_date = self._parse_date(dep_date_match.group(1))
                    data["actual_departure_date"] = dep_date
                    data["dep_date"] = dep_date_match.group(1)

                dep_time_match = re.search(r"-ATD\s+(\d{4})", dep_clean)
                if dep_time_match:
                    dep_time = self._parse_time(dep_time_match.group(1))
                    data["actual_departure_time"] = dep_time
                    data["dep_time"] = dep_time_match.group(1)
                    data["dep_time_utc_raw"] = dep_time_match.group(1)

            if arr_text and arr_text != "nan" and arr_text.strip():
                arr_clean = arr_text.strip().replace('"', "")

                arr_date_match = re.search(r"-ADA\s+(\d{6})", arr_clean)
                if arr_date_match:
                    arr_date = self._parse_date(arr_date_match.group(1))
                    data["actual_arrival_date"] = arr_date
                    data["arr_date"] = arr_date_match.group(1)

                arr_time_match = re.search(r"-ATA\s+(\d{4})", arr_clean)
                if arr_time_match:
                    arr_time = self._parse_time(arr_time_match.group(1))
                    data["actual_arrival_time"] = arr_time
                    data["arr_time"] = arr_time_match.group(1)
                    data["arr_time_utc_raw"] = arr_time_match.group(1)

            if flight_plan_data:
                if "departure_point" in flight_plan_data:
                    data["actual_departure_point"] = flight_plan_data["departure_point"]

                if "destination_point" in flight_plan_data:
                    data["actual_destination_point"] = flight_plan_data[
                        "destination_point"
                    ]

            return data

        except Exception as e:
            logger.error(f"Ошибка парсинга DEP/ARR данных: {e}")
            return {"raw_data": {"dep": dep_text, "arr": arr_text}}

    def _parse_coordinates(self, coord_str: str) -> Point:
        """Парсинг координат DDMMNDDDMME -> десятичные градусы."""
        if not coord_str:
            return Point(0, 0)

        pattern = r"(\d{2})(\d{2})([NS])(\d{3})(\d{2})([EW])"
        match = re.match(pattern, coord_str)
        if not match:
            logger.warning(f"Не удалось распарсить координаты: {coord_str}")
            return Point(0, 0)

        lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = match.groups()
        try:
            latitude = float(lat_deg) + float(lat_min) / 60
            longitude = float(lon_deg) + float(lon_min) / 60

            if lat_dir == "S":
                latitude = -latitude
            if lon_dir == "W":
                longitude = -longitude

            return Point(longitude, latitude)
        except ValueError as e:
            logger.error(f"Ошибка конвертации координат {coord_str}: {e}")
            return Point(0, 0)

    def _parse_coordinates_extended(self, coord_str: str) -> Point:
        """Парсинг координат DDMMSSNDDDMMSSE -> десятичные градусы."""
        if not coord_str:
            return Point(0, 0)

        logger.info(f"Парсинг координат: '{coord_str}'")

        patterns = [
            r"(\d{2})(\d{2})([NS])(\d{3})(\d{2})([EW])",
            r"(\d{2})(\d{2})(\d{2})([NS])(\d{3})(\d{2})(\d{2})([EW])",
        ]

        for i, pattern in enumerate(patterns):
            match = re.match(pattern, coord_str)
            if match:
                groups = match.groups()
                logger.info(f"Координаты соответствуют паттерну {i}: {groups}")

                try:
                    if len(groups) == 6:
                        lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = groups
                        latitude = float(lat_deg) + float(lat_min) / 60
                        longitude = float(lon_deg) + float(lon_min) / 60
                        logger.info(
                            f"Парсим без секунд: lat={lat_deg}°{lat_min}'{lat_dir} = {latitude}, lon={lon_deg}°{lon_min}'{lon_dir} = {longitude}"
                        )
                    elif len(groups) == 8:
                        (
                            lat_deg,
                            lat_min,
                            lat_sec,
                            lat_dir,
                            lon_deg,
                            lon_min,
                            lon_sec,
                            lon_dir,
                        ) = groups
                        latitude = (
                            float(lat_deg) + float(lat_min) / 60 + float(lat_sec) / 3600
                        )
                        longitude = (
                            float(lon_deg) + float(lon_min) / 60 + float(lon_sec) / 3600
                        )
                        logger.info(
                            f"Парсим с секундами: lat={lat_deg}°{lat_min}'{lat_sec}\"{lat_dir} = {latitude}, lon={lon_deg}°{lon_min}'{lon_sec}\"{lon_dir} = {longitude}"
                        )
                    else:
                        continue

                    if lat_dir == "S":
                        latitude = -latitude
                    if lon_dir == "W":
                        longitude = -longitude

                    point = Point(longitude, latitude)
                    logger.info(f"Координаты успешно распарсены: {point}")
                    return point

                except (ValueError, TypeError) as e:
                    logger.error(f"Ошибка парсинга координат {coord_str}: {e}")
                    continue

        logger.warning(f"Используем fallback для координат: '{coord_str}'")
        return self._parse_coordinates(coord_str)

    def _parse_time(self, time_str: str) -> time:
        """Парсинг времени HHMM -> datetime.time."""
        if not time_str or len(time_str) != 4:
            return time(0, 0)

        try:
            hours = int(time_str[:2])
            minutes = int(time_str[2:])
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                return time(hours, minutes)
        except ValueError:
            pass

        return time(0, 0)

    def _parse_date(self, date_str: str) -> datetime.date:
        """Парсинг даты YYMMDD -> datetime.date."""
        if not date_str or len(date_str) != 6:
            return timezone.now().date()

        try:
            year = int("20" + date_str[:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])
            return datetime(year, month, day).date()
        except ValueError:
            return timezone.now().date()

    def _parse_duration(self, start_time_str: str, end_time_str: str) -> timedelta:
        """Парсинг продолжительности из двух временных меток HHMM -> timedelta."""
        try:
            start_hour = int(start_time_str[:2])
            start_minute = int(start_time_str[2:4])
            end_hour = int(end_time_str[:2])
            end_minute = int(end_time_str[2:4])

            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute

            if end_minutes < start_minutes:
                end_minutes += 24 * 60

            duration_minutes = end_minutes - start_minutes

            if duration_minutes <= 0:
                duration_minutes = 60
            elif duration_minutes > 24 * 60:
                duration_minutes = 24 * 60

            return timedelta(minutes=duration_minutes)
        except (ValueError, TypeError, IndexError):
            return timedelta(hours=1)

    def _process_row(self, index: int, row: pd.Series) -> None:
        """Обработка одной строки данных с валидацией DEP/ARR."""
        shr_data = str(row.get("SHR", ""))
        dep_data = str(row.get("DEP", ""))
        arr_data = str(row.get("ARR", ""))

        self.validation_stats["total_rows"] += 1

        has_shr = shr_data and shr_data != "nan" and shr_data.strip()
        has_dep = dep_data and dep_data != "nan" and dep_data.strip()
        has_arr = arr_data and arr_data != "nan" and arr_data.strip()

        if has_shr:
            self.validation_stats["valid_shr"] += 1
        if has_dep:
            self.validation_stats["valid_dep"] += 1
        if has_arr:
            self.validation_stats["valid_arr"] += 1

        if not has_shr:
            return
        if not has_dep:
            return
        if not has_arr:
            return

        flight_plan_data = self._parse_shr_data(shr_data)
        if not flight_plan_data:
            self.validation_stats["parsing_errors"] += 1
            raise ValueError("Не удалось извлечь данные плана полета")

        actual_flight_data = self._parse_dep_arr_data(
            dep_data, arr_data, flight_plan_data
        )

        self.validation_stats["complete_flights"] += 1
        self.validation_stats["flights_with_actual"] += 1

        with transaction.atomic():
            flight_plan = self._create_flight_plan(flight_plan_data)

            if actual_flight_data:
                actual_flight = self._create_actual_flight_with_duration(
                    flight_plan, actual_flight_data
                )
                if actual_flight:
                    self.actual_flights_count += 1

            self.created_count += 1

    def _create_flight_plan(self, data: dict[str, Any]) -> FlightPlan:
        """Создание плана полета (синхронная версия)."""
        operator = self._get_or_create_operator(data.get("operator_info", ""))
        drone_type = self._get_or_create_drone_type(data.get("drone_type_code", "BLA"))
        flight_zone = None
        if data.get("flight_zone_code"):
            flight_zone = self._get_or_create_flight_zone(data["flight_zone_code"])

        departure_point = data.get("departure_point", Point(0, 0))
        destination_point = data.get("destination_point", Point(0, 0))

        departure_region = None
        destination_region = None

        if departure_point and departure_point.x != 0 and departure_point.y != 0:
            departure_region = self._assign_region_by_coordinates(departure_point)

        if destination_point and destination_point.x != 0 and destination_point.y != 0:
            destination_region = self._assign_region_by_coordinates(destination_point)

        departure_region_code = departure_region.code if departure_region else None

        sid = data.get("sid", "")
        if sid:
            existing_plan = FlightPlan.objects.filter(sid=sid).first()
            if existing_plan:
                logger.debug(f"Пропускаем дублирующий план полета с SID: {sid}")
                return existing_plan

        planned_departure_time_utc = data.get("planned_departure_time")
        if isinstance(planned_departure_time_utc, time) and data.get("planned_date"):

            utc_dt = datetime.combine(data["planned_date"], planned_departure_time_utc)
            regional_dt = self._convert_utc_to_regional(utc_dt, departure_region_code)
            planned_departure_time = regional_dt.time()
        else:
            planned_departure_time = planned_departure_time_utc or time(0, 0)

        return FlightPlan.objects.create(
            flight_id=data.get(
                "flight_id", f"UNKNOWN_{timezone.now().strftime('%Y%m%d%H%M%S')}"
            ),
            sid=data.get("sid", ""),
            reg_number=data.get("reg_number", ""),
            planned_date=data.get("planned_date", timezone.now().date()),
            planned_departure_time=planned_departure_time,
            planned_duration=data.get("planned_duration", timedelta(hours=1)),
            min_altitude=data.get("min_altitude", 0),
            max_altitude=data.get("max_altitude", 100),
            departure_point=departure_point,
            destination_point=destination_point,
            departure_region=departure_region,
            destination_region=destination_region,
            operator=operator,
            drone_type=drone_type,
            flight_zone=flight_zone,
            purpose=data.get("purpose", ""),
            raw_data=data.get("raw_data", {}),
        )

    def _create_actual_flight(
        self, flight_plan: FlightPlan, data: dict[str, Any]
    ) -> ActualFlight:
        """Создание записи фактического полета с конвертацией времени из UTC в региональное."""

        dep_region_code = (
            flight_plan.departure_region.code if flight_plan.departure_region else None
        )
        dest_region_code = (
            flight_plan.destination_region.code
            if flight_plan.destination_region
            else None
        )

        actual_departure_time = data.get("actual_departure_time")
        if (
            actual_departure_time
            and isinstance(actual_departure_time, time)
            and data.get("actual_departure_date")
        ):
            utc_dt = datetime.combine(
                data["actual_departure_date"], actual_departure_time
            )
            regional_dt = self._convert_utc_to_regional(utc_dt, dep_region_code)
            actual_departure_time = regional_dt.time()

        actual_arrival_time = data.get("actual_arrival_time")
        if (
            actual_arrival_time
            and isinstance(actual_arrival_time, time)
            and data.get("actual_arrival_date")
        ):
            utc_dt = datetime.combine(data["actual_arrival_date"], actual_arrival_time)
            regional_dt = self._convert_utc_to_regional(
                utc_dt, dest_region_code or dep_region_code
            )
            actual_arrival_time = regional_dt.time()

        return ActualFlight.objects.create(
            flight_plan=flight_plan,
            actual_departure_date=data.get("actual_departure_date"),
            actual_departure_time=actual_departure_time,
            actual_departure_point=data.get("actual_departure_point"),
            actual_arrival_date=data.get("actual_arrival_date"),
            actual_arrival_time=actual_arrival_time,
            actual_destination_point=data.get("actual_destination_point"),
        )

    def _create_actual_flight_with_duration(
        self, flight_plan: FlightPlan, data: dict[str, Any]
    ) -> ActualFlight:
        """Создание записи фактического полета с расчетом продолжительности и конвертацией времени."""

        dep_region_code = (
            flight_plan.departure_region.code if flight_plan.departure_region else None
        )
        dest_region_code = (
            flight_plan.destination_region.code
            if flight_plan.destination_region
            else None
        )

        actual_departure_time = data.get("actual_departure_time")
        if (
            actual_departure_time
            and data.get("dep_time_utc_raw")
            and data.get("actual_departure_date")
        ):
            utc_dt = datetime.combine(
                data["actual_departure_date"], actual_departure_time
            )
            regional_dt = self._convert_utc_to_regional(utc_dt, dep_region_code)
            actual_departure_time = regional_dt.time()

            actual_departure_date = regional_dt.date()
        else:
            actual_departure_date = data.get("actual_departure_date")

        actual_arrival_time = data.get("actual_arrival_time")
        if (
            actual_arrival_time
            and data.get("arr_time_utc_raw")
            and data.get("actual_arrival_date")
        ):
            utc_dt = datetime.combine(data["actual_arrival_date"], actual_arrival_time)
            regional_dt = self._convert_utc_to_regional(
                utc_dt, dest_region_code or dep_region_code
            )
            actual_arrival_time = regional_dt.time()

            actual_arrival_date = regional_dt.date()
        else:
            actual_arrival_date = data.get("actual_arrival_date")

        actual_duration = None
        if (
            actual_departure_date
            and actual_departure_time
            and actual_arrival_date
            and actual_arrival_time
        ):
            actual_duration = self._calculate_actual_flight_duration(
                actual_departure_date,
                actual_departure_time,
                actual_arrival_date,
                actual_arrival_time,
            )

        return ActualFlight.objects.create(
            flight_plan=flight_plan,
            actual_departure_date=actual_departure_date,
            actual_departure_time=actual_departure_time,
            actual_departure_point=data.get("actual_departure_point"),
            actual_arrival_date=actual_arrival_date,
            actual_arrival_time=actual_arrival_time,
            actual_destination_point=data.get("actual_destination_point"),
            actual_duration=actual_duration,
            flight_status="completed",
        )

    def _get_or_create_operator(self, operator_info: str) -> DroneOperator:
        return self._get_or_create_operator_cached(operator_info)

    def _get_or_create_drone_type(self, code: str) -> DroneType:
        return self._get_or_create_drone_type_cached(code)

    def _get_or_create_flight_zone(self, code: str) -> FlightZone:
        return self._get_or_create_flight_zone_cached(code)
