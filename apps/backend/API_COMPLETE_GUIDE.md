# 📋 Полное руководство по API системы управления полетами БАС

## 🚀 Обзор

Система управления полетами беспилотных авиационных систем (БАС) предоставляет комплексный REST API для управления планами полетов, операторами, статистикой и аналитикой.

**Base URL:** `http://localhost:8000/api/v1/flights/`

## 🔐 Аутентификация

API поддерживает несколько типов аутентификации:

### Token аутентификация (рекомендуется)
```bash
curl -H "Authorization: Token your-api-token-here" \
     -X GET "http://localhost:8000/api/v1/flights/flight-plans/"
```

### Basic аутентификация
```bash
curl -H "Authorization: Basic $(echo -n username:password | base64)" \
     -X GET "http://localhost:8000/api/v1/flights/flight-plans/"
```

### Уровни доступа
- **👤 Анонимный** - только GET запросы, базовая статистика
- **🔑 Аутентифицированный** - полный CRUD доступ к планам полетов
- **👨‍💼 Staff** - загрузка файлов, административные функции

---

## 📊 1. ПЛАНЫ ПОЛЕТОВ `/flight-plans/`

### 1.1 Список планов полетов
**GET** `/flight-plans/`

Возвращает пагинированный список всех планов полетов с возможностью фильтрации.

#### Параметры запроса:

##### 📅 Временные фильтры
| Параметр | Описание | Пример |
|----------|----------|---------|
| `planned_date` | Конкретная дата | `2024-01-15` |
| `planned_date_from` | Дата начала | `2024-01-01` |
| `planned_date_to` | Дата окончания | `2024-01-31` |
| `planned_departure_time_from` | Время начала | `09:00:00` |
| `planned_departure_time_to` | Время окончания | `18:00:00` |

##### 🌍 Географические фильтры
| Параметр | Описание | Пример |
|----------|----------|---------|
| `departure_region_code` | Код региона вылета | `77` (Москва) |
| `destination_region_code` | Код региона назначения | `78` (СПб) |
| `near_point` | Близость к точке | `55.7558,37.6173,50` |

##### 🏢 Операционные фильтры
| Параметр | Описание | Пример |
|----------|----------|---------|
| `operator_name` | Поиск по оператору | `МВД` |
| `organization_type` | Тип организации | `Государственная` |
| `drone_type_code` | Код типа БАС | `BLA` |
| `flight_status` | Статус полета | `completed` |
| `has_actual_flight` | Наличие фактических данных | `true` |

##### 🔍 Высотные фильтры
| Параметр | Описание | Пример |
|----------|----------|---------|
| `min_altitude_gte` | Мин. высота >= | `100` |
| `min_altitude_lte` | Мин. высота <= | `500` |
| `max_altitude_gte` | Макс. высота >= | `200` |
| `max_altitude_lte` | Макс. высота <= | `1000` |

##### 📄 Пагинация и сортировка
| Параметр | Описание | Пример |
|----------|----------|---------|
| `page` | Номер страницы | `2` |
| `page_size` | Размер страницы (1-100) | `50` |
| `ordering` | Поле сортировки | `-planned_date` |

**Доступные поля сортировки:**
- `planned_date` - по дате планирования
- `planned_departure_time` - по времени вылета
- `operator__name` - по оператору
- `created` - по времени создания
- `-field` - обратная сортировка

#### Примеры запросов:

```bash
# Все полеты за сегодня
curl "http://localhost:8000/api/v1/flights/flight-plans/?planned_date=2024-01-15"

# Полеты МВД в Москве за декабрь
curl "http://localhost:8000/api/v1/flights/flight-plans/?operator_name__icontains=мвд&departure_region_code=77&planned_date_from=2024-12-01&planned_date_to=2024-12-31"

# Полеты выше 500м в радиусе 100км от точки
curl "http://localhost:8000/api/v1/flights/flight-plans/?min_altitude_gte=500&near_point=55.7558,37.6173,100"

# Завершенные полеты, сортированные по дате
curl "http://localhost:8000/api/v1/flights/flight-plans/?flight_status=completed&ordering=-planned_date&page_size=100"
```

#### Пример ответа:
```json
{
    "count": 1250,
    "next": "http://localhost:8000/api/v1/flights/flight-plans/?page=2",
    "previous": null,
    "results": [
        {
            "id": "uuid-here",
            "flight_id": "FL20240115001",
            "sid": "SID001",
            "reg_number": "RF-12345",
            "planned_date": "2024-01-15",
            "planned_departure_time": "10:30:00",
            "planned_duration": "02:15:00",
            "min_altitude": 150,
            "max_altitude": 400,
            "departure_point": "POINT(37.6173 55.7558)",
            "destination_point": "POINT(37.5407 55.7033)",
            "departure_latitude": 55.7558,
            "departure_longitude": 37.6173,
            "destination_latitude": 55.7033,
            "destination_longitude": 37.5407,
            "operator": "uuid-operator",
            "operator_name": "МВД России",
            "drone_type": "uuid-drone-type",
            "drone_type_code": "BLA",
            "departure_region": "uuid-region",
            "departure_region_name": "Москва",
            "destination_region": "uuid-region",
            "destination_region_name": "Москва",
            "flight_zone": "uuid-zone",
            "flight_zone_code": "ZON001",
            "purpose": "Патрулирование",
            "special_conditions": "Ночные условия",
            "has_actual_flight": true,
            "created": "2024-01-14T18:00:00Z",
            "modified": "2024-01-15T12:30:00Z"
        }
    ]
}
```

### 1.2 Детальная информация о полете
**GET** `/flight-plans/{id}/`

Возвращает полную информацию о конкретном плане полета.

```bash
curl "http://localhost:8000/api/v1/flights/flight-plans/uuid-here/"
```

### 1.3 Создание плана полета
**POST** `/flight-plans/`

Создает новый план полета.

**Требуется аутентификация**

#### Тело запроса:
```json
{
    "flight_id": "FL20240115002",
    "sid": "SID002",
    "reg_number": "RF-12346",
    "planned_date": "2024-01-15",
    "planned_departure_time": "14:00:00",
    "planned_duration": "01:30:00",
    "min_altitude": 200,
    "max_altitude": 600,
    "departure_latitude": 55.7558,
    "departure_longitude": 37.6173,
    "destination_latitude": 55.7033,
    "destination_longitude": 37.5407,
    "operator": "uuid-operator",
    "drone_type": "uuid-drone-type",
    "flight_zone": "uuid-zone",
    "purpose": "Мониторинг территории",
    "special_conditions": "Хорошие погодные условия"
}
```

### 1.4 Обновление плана полета
**PUT/PATCH** `/flight-plans/{id}/`

Обновляет существующий план полета.

**Требуется аутентификация**

### 1.5 Удаление плана полета
**DELETE** `/flight-plans/{id}/`

Удаляет план полета.

**Требуется аутентификация**

---

## 📂 2. ЗАГРУЗКА EXCEL ФАЙЛОВ

### 2.1 Загрузка Excel файла
**POST** `/flight-plans/upload_excel/`

Загружает планы полетов из Excel файла (как в Django Admin).

**Требуются права Staff**

#### Параметры:
- `excel_file` - Excel файл (.xlsx, .xls)
- Максимальный размер: 50MB

#### Поддерживаемые форматы столбцов:
- **SHR format**: полные данные включая координаты
- **DEP format**: данные вылета
- **ARR format**: данные прилета

#### Пример запроса:
```bash
curl -X POST \
  -H "Authorization: Token your-token" \
  -F "excel_file=@flight_plans.xlsx" \
  "http://localhost:8000/api/v1/flights/flight-plans/upload_excel/"
```

#### Пример ответа:
```json
{
    "success": true,
    "processed": 150,
    "created": 142,
    "updated": 8,
    "errors": [
        {
            "row": 15,
            "error": "Неверный формат координат"
        }
    ],
    "summary": {
        "total_rows": 150,
        "success_rate": 94.7,
        "processing_time": "00:02:34"
    }
}
```

---

## 🗺️ 3. ДАННЫЕ ДЛЯ КАРТЫ

### 3.1 GeoJSON данные для карты
**GET** `/flight-plans/map_data/`

Возвращает данные полетов в формате GeoJSON для отображения на карте.

#### Параметры фильтрации:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `date_from` | Дата начала | `2024-01-01` |
| `date_to` | Дата окончания | `2024-01-31` |
| `region` | Код региона | `77` |
| `status` | Статус полета | `completed` |
| `operator` | ID оператора | `uuid-operator` |

#### Пример запроса:
```bash
curl "http://localhost:8000/api/v1/flights/flight-plans/map_data/?date_from=2024-01-01&region=77&status=completed"
```

#### Пример ответа:
```json
{
    "type": "FeatureCollection",
    "features": [
        {
            "id": "uuid-here",
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [37.6173, 55.7558]
            },
            "properties": {
                "flight_id": "FL20240115001",
                "planned_date": "2024-01-15",
                "planned_departure_time": "10:30:00",
                "operator_name": "МВД России",
                "drone_type_code": "BLA",
                "purpose": "Патрулирование"
            }
        }
    ]
}
```

---

## 📈 4. БАЗОВАЯ СТАТИСТИКА

### 4.1 Главная статистика (Dashboard)
**GET** `/statistics/dashboard/`

Возвращает основную статистику системы.

#### Пример ответа:
```json
{
    "total_flights": 15420,
    "completed_flights": 13890,
    "planned_today": 45,
    "active_operators": 127,
    "completion_rate": 90.1,
    "top_regions": [
        {
            "region_name": "Москва",
            "region_code": "77",
            "flight_count": 3250
        }
    ],
    "recent_activity": {
        "last_24h": 67,
        "last_week": 445,
        "last_month": 1890
    }
}
```

### 4.2 Статистика по времени
**GET** `/flight-plans/time_statistics/`

Возвращает временную статистику полетов.

#### Параметры:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `period` | Период группировки | `day`, `week`, `month` |
| `date_from` | Дата начала | `2024-01-01` |
| `date_to` | Дата окончания | `2024-01-31` |

```bash
curl "http://localhost:8000/api/v1/flights/flight-plans/time_statistics/?period=week&date_from=2024-01-01&date_to=2024-01-31"
```

### 4.3 Региональная статистика
**GET** `/flight-plans/regional_statistics/`

Возвращает статистику по регионам.

#### Параметры:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `date_from` | Дата начала | `2024-01-01` |
| `date_to` | Дата окончания | `2024-01-31` |

```bash
curl "http://localhost:8000/api/v1/flights/flight-plans/regional_statistics/?date_from=2024-01-01&date_to=2024-01-31"
```

#### Пример ответа:
```json
{
    "date_range": {
        "from": "2024-01-01",
        "to": "2024-01-31"
    },
    "departure_regions": [
        {
            "region_name": "Москва",
            "region_code": "77",
            "flight_count": 145,
            "avg_duration": "02:15:30",
            "completion_rate": 92.4
        }
    ],
    "destination_regions": [
        {
            "region_name": "Московская область",
            "region_code": "50",
            "flight_count": 89,
            "avg_duration": "01:45:20",
            "completion_rate": 88.7
        }
    ],
    "cross_regional_routes": [
        {
            "departure_region": "Москва (77)",
            "destination_region": "Московская область (50)",
            "flight_count": 34
        }
    ]
}
```

### 4.4 Статистика операторов
**GET** `/flight-plans/operator_statistics/`

Возвращает статистику по операторам.

#### Параметры:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `date_from` | Дата начала | `2024-01-01` |
| `date_to` | Дата окончания | `2024-01-31` |
| `limit` | Количество записей | `10` |

```bash
curl "http://localhost:8000/api/v1/flights/flight-plans/operator_statistics/?limit=10"
```

---

## 🔬 5. ПРОДВИНУТАЯ АНАЛИТИКА

Система предоставляет 6 специализированных метрик для глубокого анализа данных полетов.

### 5.1 Универсальный эндпоинт расширенной аналитики
**GET** `/flight-plans/advanced_analytics/`

#### Параметры:
| Параметр | Описание | Значения |
|----------|----------|----------|
| `metric` | Тип метрики | `comprehensive`, `peak_load`, `daily_dynamics`, `growth_decline`, `flight_density`, `daily_activity`, `zero_flight_days` |
| `date_from` | Дата начала | `2024-01-01` |
| `date_to` | Дата окончания | `2024-01-31` |

#### Примеры запросов:

```bash
# Все метрики сразу
curl "http://localhost:8000/api/v1/flights/flight-plans/advanced_analytics/?metric=comprehensive&date_from=2024-01-01&date_to=2024-01-31"

# Только пиковая нагрузка
curl "http://localhost:8000/api/v1/flights/flight-plans/advanced_analytics/?metric=peak_load&date_from=2024-01-01"

# Среднесуточная динамика
curl "http://localhost:8000/api/v1/flights/flight-plans/advanced_analytics/?metric=daily_dynamics"
```

### 5.2 Пиковая нагрузка (Peak Load)
**GET** `/flight-plans/peak_load_analysis/`

Анализ максимальной нагрузки по часам.

#### Пример ответа:
```json
{
    "metric": "peak_load",
    "date_range": {
        "from": "2024-01-01",
        "to": "2024-01-31"
    },
    "peak_hour": {
        "hour": "2024-01-15T10:00:00Z",
        "flights_count": 25,
        "formatted_hour": "10:00"
    },
    "average_flights_per_hour": 8.5,
    "total_flight_hours": 744,
    "peak_load_percentage": 294.1,
    "top_10_hours": [
        {
            "hour": "2024-01-15T10:00:00Z",
            "flights_count": 25,
            "formatted_hour": "10:00"
        }
    ]
}
```

### 5.3 Среднесуточная динамика (Daily Dynamics)
**GET** `/flight-plans/advanced_analytics/?metric=daily_dynamics`

#### Пример ответа:
```json
{
    "metric": "daily_dynamics",
    "date_range": {
        "from": "2024-01-01",
        "to": "2024-01-31"
    },
    "average_flights_per_day": 15.8,
    "median_flights_per_day": 14.0,
    "min_flights_per_day": 2,
    "max_flights_per_day": 45,
    "total_days": 31,
    "days_with_flights": 29,
    "days_without_flights": 2,
    "zero_flight_days_percentage": 6.5
}
```

### 5.4 Рост/падение (Growth Trends)
**GET** `/statistics/growth_trends/`

Анализ изменения активности по месяцам.

#### Параметры:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `month` | Конкретный месяц | `2024-01` |

```bash
curl "http://localhost:8000/api/v1/flights/statistics/growth_trends/?month=2024-01"
```

#### Пример ответа:
```json
{
    "metric": "growth_decline",
    "analysis_month": "2024-01",
    "current_month": {
        "month": "2024-01",
        "flights_count": 489
    },
    "previous_month": {
        "month": "2023-12",
        "flights_count": 437
    },
    "growth_rate": 11.9,
    "absolute_change": 52,
    "trend": "рост",
    "interpretation": "Рост на 11.9% по сравнению с предыдущим месяцем"
}
```

### 5.5 Плотность полетов (Flight Density)
**GET** `/flight-plans/flight_density_analysis/`

Расчет плотности полетов на 1000км² по регионам.

#### Параметры:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `top` | Количество топ регионов | `10` |
| `date_from` | Дата начала | `2024-01-01` |
| `date_to` | Дата окончания | `2024-01-31` |

```bash
curl "http://localhost:8000/api/v1/flights/flight-plans/flight_density_analysis/?top=10"
```

#### Пример ответа:
```json
{
    "metric": "flight_density",
    "date_range": {
        "from": "2024-01-01",
        "to": "2024-01-31"
    },
    "regions": [
        {
            "region_name": "Москва",
            "region_code": "77",
            "flights_count": 145,
            "area_km2": 2511,
            "flight_density_per_1000km2": 57.75,
            "rank": 1
        },
        {
            "region_name": "Санкт-Петербург",
            "region_code": "78",
            "flights_count": 89,
            "area_km2": 1403,
            "flight_density_per_1000km2": 63.47,
            "rank": 2
        }
    ],
    "total_regions_analyzed": 85,
    "average_density": 12.4
}
```

### 5.6 Дневная активность (Daily Activity)
**GET** `/flight-plans/daily_activity_analysis/`

Распределение полетов по времени суток.

#### Пример ответа:
```json
{
    "metric": "daily_activity",
    "date_range": {
        "from": "2024-01-01",
        "to": "2024-01-31"
    },
    "hourly_distribution": {
        "0": 5, "1": 2, "2": 1, "3": 0,
        "4": 0, "5": 3, "6": 12, "7": 25,
        "8": 45, "9": 67, "10": 89, "11": 76,
        "12": 85, "13": 92, "14": 88, "15": 78,
        "16": 65, "17": 45, "18": 34, "19": 23,
        "20": 18, "21": 15, "22": 12, "23": 8
    },
    "period_distribution": {
        "morning": {
            "hours": "06:00-11:59",
            "flights": 214,
            "percentage": 23.4
        },
        "day": {
            "hours": "12:00-17:59",
            "flights": 408,
            "percentage": 44.6
        },
        "evening": {
            "hours": "18:00-22:59",
            "flights": 102,
            "percentage": 11.1
        },
        "night": {
            "hours": "23:00-05:59",
            "flights": 11,
            "percentage": 1.2
        }
    },
    "peak_hour": {
        "hour": 13,
        "flights_count": 92,
        "formatted_hour": "13:00"
    }
}
```

### 5.7 Нулевые дни (Zero Flight Days)
**GET** `/statistics/zero_flight_days_analysis/`

Анализ дней без полетов по регионам.

#### Параметры:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `top` | Количество регионов | `20` |
| `date_from` | Дата начала | `2024-01-01` |
| `date_to` | Дата окончания | `2024-01-31` |

```bash
curl "http://localhost:8000/api/v1/flights/statistics/zero_flight_days_analysis/?top=20"
```

#### Пример ответа:
```json
{
    "metric": "zero_flight_days",
    "date_range": {
        "from": "2024-01-01",
        "to": "2024-01-31"
    },
    "total_days": 31,
    "regions": [
        {
            "region_name": "Чукотский автономный округ",
            "region_code": "87",
            "zero_flight_days": 31,
            "zero_flight_days_percentage": 100.0,
            "active_days": 0,
            "avg_flights_per_active_day": 0
        },
        {
            "region_name": "Московская область",
            "region_code": "50",
            "zero_flight_days": 3,
            "zero_flight_days_percentage": 9.7,
            "active_days": 28,
            "avg_flights_per_active_day": 8.2
        }
    ],
    "summary": {
        "regions_with_zero_days": 45,
        "completely_inactive_regions": 12,
        "average_zero_days_percentage": 34.7
    }
}
```

### 5.8 Региональное сравнение
**GET** `/flight-plans/regional_comparison/`

Сравнительный анализ указанных регионов по всем метрикам.

#### Параметры:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `regions` | Коды регионов | `77,78,50` |
| `date_from` | Дата начала | `2024-01-01` |
| `date_to` | Дата окончания | `2024-01-31` |

```bash
curl "http://localhost:8000/api/v1/flights/flight-plans/regional_comparison/?regions=77,78,50&date_from=2024-01-01&date_to=2024-01-31"
```

#### Пример ответа:
```json
{
    "date_range": {
        "from": "2024-01-01",
        "to": "2024-01-31"
    },
    "regions_comparison": [
        {
            "region_name": "Москва",
            "region_code": "77",
            "flights_count": 145,
            "flight_density_per_1000km2": 57.75,
            "zero_flight_days": 0,
            "zero_flight_days_percentage": 0.0,
            "avg_duration_minutes": 135,
            "peak_hour_flights": 15
        },
        {
            "region_name": "Санкт-Петербург",
            "region_code": "78",
            "flights_count": 89,
            "flight_density_per_1000km2": 63.47,
            "zero_flight_days": 2,
            "zero_flight_days_percentage": 6.5,
            "avg_duration_minutes": 105,
            "peak_hour_flights": 12
        }
    ],
    "comparison_summary": {
        "leader_by_flights": "Москва (77)",
        "leader_by_density": "Санкт-Петербург (78)",
        "most_consistent": "Москва (77)"
    }
}
```

---

## ✈️ 6. ФАКТИЧЕСКИЕ ПОЛЕТЫ `/actual-flights/`

### 6.1 Список фактических полетов
**GET** `/actual-flights/`

```bash
curl "http://localhost:8000/api/v1/flights/actual-flights/"
```

### 6.2 Статистика по статусам
**GET** `/actual-flights/status_statistics/`

#### Пример ответа:
```json
{
    "status_distribution": [
        {
            "flight_status": "completed",
            "count": 890,
            "percentage": 78.2
        },
        {
            "flight_status": "in_progress",
            "count": 45,
            "percentage": 4.0
        },
        {
            "flight_status": "cancelled",
            "count": 23,
            "percentage": 2.0
        }
    ],
    "total_actual_flights": 958
}
```

---

## 📚 7. СПРАВОЧНИКИ

### 7.1 Операторы БАС `/operators/`

#### Список операторов
**GET** `/operators/`

#### Параметры:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `search` | Поиск по названию | `МВД` |
| `ordering` | Сортировка | `name`, `-created` |

```bash
curl "http://localhost:8000/api/v1/flights/operators/?search=мвд"
```

#### Информация об операторе
**GET** `/operators/{id}/`

### 7.2 Типы БАС `/drone-types/`

#### Список типов дронов
**GET** `/drone-types/`

#### Параметры:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `ordering` | Сортировка | `code`, `name` |

```bash
curl "http://localhost:8000/api/v1/flights/drone-types/"
```

### 7.3 Регионы РФ `/regions/`

#### Список регионов
**GET** `/regions/`

#### Параметры:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `search` | Поиск по названию | `Москва` |
| `ordering` | Сортировка | `name`, `code` |

```bash
curl "http://localhost:8000/api/v1/flights/regions/?search=москва"
```

#### Полеты по региону
**GET** `/regions/{code}/flights/`

#### Параметры:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `type` | Тип полетов | `departure`, `destination`, `all` |
| `date_from` | Дата начала | `2024-01-01` |
| `date_to` | Дата окончания | `2024-01-31` |

```bash
curl "http://localhost:8000/api/v1/flights/regions/77/flights/?type=departure&date_from=2024-01-01"
```

---

## 📊 8. ЭКСПОРТ ДАННЫХ

### 8.1 Экспорт статистики
**GET** `/statistics/export_data/`

#### Параметры:
| Параметр | Описание | Пример |
|----------|----------|---------|
| `format` | Формат экспорта | `csv`, `xlsx`, `json` |
| `date_from` | Дата начала | `2024-01-01` |
| `date_to` | Дата окончания | `2024-01-31` |

```bash
# Экспорт в CSV
curl "http://localhost:8000/api/v1/flights/statistics/export_data/?format=csv&date_from=2024-01-01"

# Экспорт в Excel
curl "http://localhost:8000/api/v1/flights/statistics/export_data/?format=xlsx&date_from=2024-01-01" -o flights_export.xlsx
```

---

## 📊 9. КОМПЛЕКСНЫЕ МЕТРИКИ

### 9.1 Все расширенные метрики
**GET** `/statistics/comprehensive_metrics/`

Возвращает все 6 продвинутых метрик в одном запросе.

```bash
curl "http://localhost:8000/api/v1/flights/statistics/comprehensive_metrics/?date_from=2024-01-01&date_to=2024-01-31"
```

#### Пример ответа:
```json
{
    "date_range": {
        "from": "2024-01-01",
        "to": "2024-01-31"
    },
    "metrics": {
        "peak_load": { /* данные пиковой нагрузки */ },
        "daily_dynamics": { /* среднесуточная динамика */ },
        "growth_decline": { /* рост/падение */ },
        "flight_density": { /* плотность полетов */ },
        "daily_activity": { /* дневная активность */ },
        "zero_flight_days": { /* нулевые дни */ }
    },
    "generated_at": "2024-01-15T10:30:00Z"
}
```

---

## 🚨 10. КОДЫ ОШИБОК

| Код | Название | Описание | Решение |
|-----|----------|----------|---------|
| **200** | OK | Успешный запрос | - |
| **201** | Created | Ресурс успешно создан | - |
| **400** | Bad Request | Некорректные параметры | Проверьте параметры запроса |
| **401** | Unauthorized | Требуется аутентификация | Добавьте заголовок Authorization |
| **403** | Forbidden | Недостаточно прав | Используйте аккаунт с правами staff |
| **404** | Not Found | Ресурс не найден | Проверьте URL и ID ресурса |
| **422** | Unprocessable Entity | Ошибка валидации | Проверьте данные запроса |
| **429** | Too Many Requests | Превышен лимит запросов | Уменьшите частоту запросов |
| **500** | Internal Server Error | Внутренняя ошибка сервера | Обратитесь к администратору |

### Примеры ошибок:

#### 400 Bad Request
```json
{
    "error": "Invalid date format",
    "details": {
        "planned_date": ["Введите правильную дату."]
    }
}
```

#### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

#### 403 Forbidden
```json
{
    "error": "Недостаточно прав для загрузки файлов"
}
```

---

## 🔧 11. ПРАКТИЧЕСКИЕ ПРИМЕРЫ

### 11.1 Мониторинг активности за день
```bash
#!/bin/bash
# Скрипт мониторинга полетов за сегодня

TODAY=$(date +%Y-%m-%d)
API_TOKEN="your-token-here"

# Общая статистика за день
curl -H "Authorization: Token $API_TOKEN" \
     "http://localhost:8000/api/v1/flights/flight-plans/?planned_date=$TODAY&page_size=100" \
     | jq '.count'

# Пиковая нагрузка
curl -H "Authorization: Token $API_TOKEN" \
     "http://localhost:8000/api/v1/flights/flight-plans/peak_load_analysis/?date_from=$TODAY&date_to=$TODAY"
```

### 11.2 Еженедельный отчет
```bash
#!/bin/bash
# Еженедельный отчет по регионам

WEEK_START=$(date -d 'last monday' +%Y-%m-%d)
WEEK_END=$(date -d 'next sunday' +%Y-%m-%d)

# Статистика по топ-10 регионам
curl "http://localhost:8000/api/v1/flights/flight-plans/flight_density_analysis/?top=10&date_from=$WEEK_START&date_to=$WEEK_END" \
     > weekly_report.json

# Экспорт данных в Excel
curl "http://localhost:8000/api/v1/flights/statistics/export_data/?format=xlsx&date_from=$WEEK_START&date_to=$WEEK_END" \
     -o "weekly_flights_$(date +%Y-%m-%d).xlsx"
```

### 11.3 Поиск проблемных регионов
```bash
#!/bin/bash
# Поиск регионов с нулевой активностью

curl "http://localhost:8000/api/v1/flights/statistics/zero_flight_days_analysis/?top=50" \
     | jq '.regions[] | select(.zero_flight_days_percentage > 80) | {region: .region_name, inactive_days: .zero_flight_days_percentage}'
```

### 11.4 Bulk создание полетов через JSON
```python
import requests
import json

# Создание нескольких планов полетов
flights_data = [
    {
        "flight_id": "FL20240115003",
        "planned_date": "2024-01-15",
        "planned_departure_time": "15:00:00",
        "departure_latitude": 55.7558,
        "departure_longitude": 37.6173,
        "destination_latitude": 55.7033,
        "destination_longitude": 37.5407,
        # ... остальные поля
    },
    # ... больше полетов
]

headers = {
    'Authorization': 'Token your-token-here',
    'Content-Type': 'application/json'
}

for flight in flights_data:
    response = requests.post(
        'http://localhost:8000/api/v1/flights/flight-plans/',
        headers=headers,
        json=flight
    )
    print(f"Flight {flight['flight_id']}: {response.status_code}")
```

---

## 🎯 12. БЫСТРЫЙ СТАРТ

### Шаг 1: Проверка подключения
```bash
curl "http://localhost:8000/api/v1/flights/statistics/dashboard/"
```

### Шаг 2: Получение токена
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}' \
  "http://localhost:8000/api-token-auth/"
```

### Шаг 3: Тестирование CRUD
```bash
TOKEN="your-token-here"

# Создание плана полета
curl -X POST \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "flight_id": "TEST001",
    "planned_date": "2024-01-15",
    "planned_departure_time": "10:00:00",
    "departure_latitude": 55.7558,
    "departure_longitude": 37.6173,
    "destination_latitude": 55.7033,
    "destination_longitude": 37.5407,
    "operator": "operator-uuid",
    "drone_type": "drone-type-uuid"
  }' \
  "http://localhost:8000/api/v1/flights/flight-plans/"
```

### Шаг 4: Тестирование аналитики
```bash
# Все метрики за месяц
curl "http://localhost:8000/api/v1/flights/flight-plans/advanced_analytics/?metric=comprehensive&date_from=2024-01-01&date_to=2024-01-31"
```

---

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте статус сервера**: `curl http://localhost:8000/health/`
2. **Проверьте токен аутентификации**: убедитесь, что токен действителен
3. **Валидация данных**: используйте корректные форматы дат и координат
4. **Лимиты**: учитывайте ограничения по размеру страниц и файлов

---

**🔗 Полезные ссылки:**
- **Интерактивное API**: `http://localhost:8000/api/v1/flights/` (в браузере)
- **Django Admin**: `http://localhost:8000/admin/`
- **Health Check**: `http://localhost:8000/health/`

---

*Документация обновлена: 2024-01-15*
*Версия API: v1*


очистка кэша редис
- подключиться docker-compose exec redis redis-cli
- очистить кэш FLUSHALL

http://localhost:8000/api/v1/flights/statistics/dashboard/
"overall_statistics": { по году
        "total_flights_count": 72254, - всего вылетов
        "overall_flight_density": 4, - плотность полетов на 1000 кв. км по всей россии
        "total_duration_hours": 736977, - всего продолжительность полетов часов
        "avg_duration_minutes": 612, - средняя продолжительность полетов минут
        "median_duration_minutes": 540 - медианная продолжительность полетов минут
    },
 "monthly_statistics": [ стата за месяц по всему году
        {
            "month": "2025-01", - месяц
            "flights_count": 5572, - кол-во полетов
            "flight_density": 0, - плотность полетов на 1000 кв. км
            "total_duration_hours": 64233, - всего продолжительность полетов часов
            "avg_duration_minutes": 692, - среднюю продолжительность полетов минут
            "median_duration_minutes": 719 - медианную продолжительность полетов минут
        },