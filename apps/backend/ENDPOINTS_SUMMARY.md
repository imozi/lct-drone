# 📋 Полный список API эндпоинтов

## 🚁 Планы полетов (`/flight-plans/`)

| Метод | Эндпоинт | Описание | Параметры |
|-------|----------|----------|-----------|
| GET | `/flight-plans/` | Список планов полетов | Фильтрация, пагинация |
| GET | `/flight-plans/{id}/` | Детальная информация | - |
| POST | `/flight-plans/` | Создание плана | JSON данные |
| PUT/PATCH | `/flight-plans/{id}/` | Обновление плана | JSON данные |
| DELETE | `/flight-plans/{id}/` | Удаление плана | - |

### Специализированные эндпоинты

| Метод | Эндпоинт | Описание | Параметры |
|-------|----------|----------|-----------|
| POST | `/flight-plans/upload_excel/` | Загрузка Excel | excel_file |
| GET | `/flight-plans/map_data/` | Данные для карты (GeoJSON) | date_from, date_to, region, status |
| GET | `/flight-plans/time_statistics/` | Статистика по времени | period, date_from, date_to |
| GET | `/flight-plans/regional_statistics/` | Статистика по регионам | date_from, date_to |
| GET | `/flight-plans/operator_statistics/` | Статистика по операторам | date_from, date_to, limit |

## 🔬 Расширенная аналитика

| Метод | Эндпоинт | Описание | Параметры |
|-------|----------|----------|-----------|
| GET | `/flight-plans/advanced_analytics/` | Универсальный эндпоинт | metric, date_from, date_to |
| GET | `/flight-plans/peak_load_analysis/` | Пиковая нагрузка | date_from, date_to |
| GET | `/flight-plans/flight_density_analysis/` | Плотность полетов | top, date_from, date_to |
| GET | `/flight-plans/daily_activity_analysis/` | Дневная активность | date_from, date_to |
| GET | `/flight-plans/regional_comparison/` | Сравнение регионов | regions, date_from, date_to |

### Типы метрик для `advanced_analytics`:
- `comprehensive` - все метрики (по умолчанию)
- `peak_load` - пиковая нагрузка
- `daily_dynamics` - среднесуточная динамика
- `growth_decline` - рост/падение
- `flight_density` - плотность полетов
- `daily_activity` - дневная активность
- `zero_flight_days` - дни без полетов

## ✈️ Фактические полеты (`/actual-flights/`)

| Метод | Эндпоинт | Описание | Параметры |
|-------|----------|----------|-----------|
| GET | `/actual-flights/` | Список фактических полетов | Фильтрация, пагинация |
| GET | `/actual-flights/{id}/` | Детальная информация | - |
| GET | `/actual-flights/status_statistics/` | Статистика по статусам | - |

## 📊 Статистика и тренды (`/statistics/`)

| Метод | Эндпоинт | Описание | Параметры |
|-------|----------|----------|-----------|
| GET | `/statistics/dashboard/` | Основная статистика | - |
| GET | `/statistics/growth_trends/` | Рост/падение полетов | month |
| GET | `/statistics/zero_flight_days_analysis/` | Дни без полетов | top, date_from, date_to |
| GET | `/statistics/comprehensive_metrics/` | Все расширенные метрики | date_from, date_to |
| GET | `/statistics/export_data/` | Экспорт данных | format, date_from, date_to |

## 📚 Справочники

### Операторы БАС (`/operators/`)
| Метод | Эндпоинт | Описание | Параметры |
|-------|----------|----------|-----------|
| GET | `/operators/` | Список операторов | search, ordering |
| GET | `/operators/{id}/` | Информация об операторе | - |

### Типы БАС (`/drone-types/`)
| Метод | Эндпоинт | Описание | Параметры |
|-------|----------|----------|-----------|
| GET | `/drone-types/` | Список типов дронов | ordering |
| GET | `/drone-types/{id}/` | Информация о типе | - |

### Регионы РФ (`/regions/`)
| Метод | Эндпоинт | Описание | Параметры |
|-------|----------|----------|-----------|
| GET | `/regions/` | Список регионов | search, ordering |
| GET | `/regions/{code}/` | Информация о регионе | - |
| GET | `/regions/{code}/flights/` | Полеты по региону | type, date_from, date_to |

## 🔍 Параметры фильтрации

### Временные фильтры
| Параметр | Описание | Формат |
|----------|----------|--------|
| `planned_date` | Конкретная дата | YYYY-MM-DD |
| `planned_date_from` | Дата начала | YYYY-MM-DD |
| `planned_date_to` | Дата окончания | YYYY-MM-DD |
| `planned_departure_time_from` | Время начала | HH:MM:SS |
| `planned_departure_time_to` | Время окончания | HH:MM:SS |

### Географические фильтры
| Параметр | Описание | Формат |
|----------|----------|--------|
| `departure_region_code` | Код региона вылета | 77, 78, etc. |
| `destination_region_code` | Код региона назначения | 77, 78, etc. |
| `near_point` | Близость к точке | "lat,lng,distance_km" |

### Операционные фильтры
| Параметр | Описание | Формат |
|----------|----------|--------|
| `operator_name` | Поиск по оператору | Текст |
| `organization_type` | Тип организации | Текст |
| `drone_type_code` | Код типа БАС | BLA, AER, etc. |
| `flight_status` | Статус полета | planned, departed, completed, cancelled |
| `has_actual_flight` | Наличие фактических данных | true, false |

### Высотные фильтры
| Параметр | Описание | Формат |
|----------|----------|--------|
| `min_altitude_gte` | Минимальная высота >= | Число |
| `min_altitude_lte` | Минимальная высота <= | Число |
| `max_altitude_gte` | Максимальная высота >= | Число |
| `max_altitude_lte` | Максимальная высота <= | Число |

## 📄 Пагинация

| Параметр | Описание | Значения |
|----------|----------|----------|
| `page` | Номер страницы | 1, 2, 3, ... |
| `page_size` | Размер страницы | 1-100 (по умолчанию 20) |

## 🔄 Сортировка

| Параметр | Описание | Пример |
|----------|----------|--------|
| `ordering` | Поле для сортировки | `planned_date`, `-planned_date` |

**Доступные поля:**
- `planned_date` - по дате
- `planned_departure_time` - по времени
- `operator__name` - по оператору
- `created` - по времени создания

## 🔐 Аутентификация

### Заголовки аутентификации
```bash
# Token аутентификация
Authorization: Token your-token-here

# Basic аутентификация
Authorization: Basic base64(username:password)
```

### Права доступа
- 👤 **Анонимный** - только GET запросы
- 🔑 **Аутентифицированный** - полный доступ к API
- 👨‍💼 **Staff** - загрузка файлов, административные функции

## 📊 Коды ответов

| Код | Описание |
|-----|----------|
| 200 | OK - Успешный запрос |
| 201 | Created - Ресурс создан |
| 400 | Bad Request - Неверные параметры |
| 401 | Unauthorized - Требуется аутентификация |
| 403 | Forbidden - Недостаточно прав |
| 404 | Not Found - Ресурс не найден |
| 422 | Unprocessable Entity - Ошибка валидации |
| 429 | Too Many Requests - Превышен лимит |
| 500 | Internal Server Error - Внутренняя ошибка |

## 🎯 Примеры запросов

### Базовые запросы
```bash
# Все полеты за сегодня
GET /api/v1/flights/flight-plans/?planned_date=2024-01-15

# Полеты МВД в Москве, отсортированные по дате
GET /api/v1/flights/flight-plans/?operator_name__icontains=мвд&departure_region_code=77&ordering=-planned_date

# Данные для карты с фильтрацией
GET /api/v1/flights/flight-plans/map_data/?date_from=2024-01-01&region=77&status=completed
```

### Расширенная аналитика
```bash
# Все метрики за месяц
GET /api/v1/flights/flight-plans/advanced_analytics/?metric=comprehensive&date_from=2024-01-01&date_to=2024-01-31

# Пиковая нагрузка
GET /api/v1/flights/flight-plans/peak_load_analysis/?date_from=2024-01-01

# Плотность полетов - топ 10
GET /api/v1/flights/flight-plans/flight_density_analysis/?top=10

# Сравнение регионов
GET /api/v1/flights/flight-plans/regional_comparison/?regions=77,78,50

# Дневная активность
GET /api/v1/flights/flight-plans/daily_activity_analysis/?date_from=2024-01-01
```

### Административные операции
```bash
# Загрузка Excel файла
POST /api/v1/flights/flight-plans/upload_excel/
Content-Type: multipart/form-data
Authorization: Token your-token

# Экспорт в CSV
GET /api/v1/flights/statistics/export_data/?format=csv&date_from=2024-01-01
```

## 🌐 Base URLs

- **Разработка:** `http://localhost:8000/api/v1/flights/`
- **Продакшн:** `https://yourdomain.com/api/v1/flights/`

## 📖 Дополнительные ресурсы

- **Интерактивное API:** `/api/v1/flights/` (в браузере)
- **Django Admin:** `/admin/`
- **Health Check:** `/health/`
- **API Root:** `/api/`

---

**💡 Совет:** Используйте интерактивный браузер API для тестирования запросов в режиме разработки!


. Устранил ошибку PostgreSQL - исправил SQL запрос в get_peak_load_statistics с правильным приведением типов
  2. Обновил логику обработки дат - теперь все аналитические методы:
    - Если не указаны даты - показывают статистику по всем доступным данным
    - Если указана только date_from - показывают от этой даты до конца
    - Если указана только date_to - показывают с начала до этой даты
    - Если указаны обе даты - используют диапазон
  3. Методы, которые теперь работают без дат:
    - get_peak_load_statistics - пиковая нагрузка по всем данным
    - get_daily_dynamics - динамика по дням для всего периода
    - get_flight_density_by_regions - плотность полетов по всем данным
    - get_daily_activity_distribution - активность по времени суток
    - get_zero_flight_days_by_regions - дни без полетов
    - get_comprehensive_analytics - комплексная аналитика
    - get_regional_comparison - сравнение регионов
