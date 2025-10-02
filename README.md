# Проект ЛСТ - Сервис для анализа количества и длительности полетов гражданских беспилотников в регионах РФ

## Описание проекта

Комплексная система для анализа полетов беспилотных авиационных систем (БАС) по регионам РФ, предоставляющая статистику, визуализацию и расширенную аналитику.

## Структура проекта

Проект организован как монорепозиторий со следующими компонентами:

- **Backend**: API на базе Django с PostGIS для геопространственных данных + Django Rest Framework + Swagger + Redis
- **Frontend**: Приложение на Vue 3 + TypeScript + Pinia + Ant Design Vue
- **Services**: Пакет общих сервисов
- **UI**: Пакет переиспользуемых UI-компонентов
- **Geo**: Утилиты для обработки геопространственных данных

## Необходимые компоненты

Перед началом работы убедитесь, что у вас установлены:

### Docker и Docker Compose

Для установки Docker и Docker Compose следуйте официальной документации:

- [Установка Docker](https://docs.docker.com/engine/install/)
- [Установка Docker Compose](https://docs.docker.com/compose/install/)

### Node.js и PNPM

Для установки Node.js и PNPM следуйте официальной документации:

- [Установка Node.js](https://nodejs.org/ru/download/package-manager)
- [Установка PNPM](https://pnpm.io/installation)

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/imozi/lct-drone.git
cd drone
```

### 2. Установите все зависимости для фронтенда

Создайте файлы окружения для бэкенда:

```bash
# Из корня проекта
pnpm install

# И отдельно для фронтенда
cd apps/frontend

pnpm install

```

### 2. Запуск бэкенда в режиме разработки

```bash
# Из корня проекта
pnpm dev:backend
```

Это запустит следующие сервисы:

- PostgreSQL с расширением PostGIS
- Redis для кэширования
- Tegola для обслуживания тайлов карты
- Веб-приложение Django

```bash
# после запуска нужно загрузить данные в базу
# из корня проекта или загрузить из интерфейса администратора Django Admin
pnpm load:data
```

### 4. Запуск фронтенда в режиме разработки

```bash
# Из корня проекта
pnpm dev:frontend
```

Фронтенд будет доступен по адресу http://localhost:5173

### 5. Доступ к приложению

- **Фронтенд**: http://localhost:5173
- **API бэкенда**: http://localhost:8000/api/
- **Документация API**: http://localhost:8000/api/docs/
- **Интерфейс администратора**: http://localhost:8000/admin/
- **Интерфейс тайлового сервера Tegola**: http://localhost:8080

- Данные для входа в интерфейс администратора: admin/Admin123321

- Данные для входа в интерфейс пользователя под администратором: admin/Admin123321

- Данные для входа в интерфейс пользователя под пользователем для загрузки данных: user/User123321

## Команды для разработки

### Команды корневого проекта

```bash
# Запуск всех приложений в режиме разработки
pnpm dev

# Запуск только фронтенда
pnpm dev:frontend

# Запуск только бэкенда
pnpm dev:backend

# Остановка сервисов бэкенда
pnpm down:backend

# Сборка фронтенда для продакшена
pnpm build

# Предпросмотр продакшен-сборки
pnpm preview
```

### Команды бэкенда

```bash
# Запуск сервисов бэкенда
cd apps/backend
pnpm dev

# Остановка сервисов бэкенда
cd apps/backend
pnpm down

# Просмотр логов бэкенда
cd apps/backend
pnpm logs
```

### Команды фронтенда

```bash
# Запуск сервера разработки
cd apps/frontend
pnpm dev

# Сборка для продакшена
cd apps/frontend
pnpm build

# Предпросмотр продакшен-сборки
cd apps/frontend
pnpm preview
```

## API эндпоинты

Система предоставляет комплексный API для данных о полетах дронов:

### Планы полетов

- `GET /api/v1/flights/flight-plans/` - Получение списка планов полетов с возможностью фильтрации
- `GET /api/v1/flights/flight-plans/{id}/` - Получение детальной информации о плане полета
- `POST /api/v1/flights/flight-plans/` - Создание нового плана полета
- `PUT/PATCH /api/v1/flights/flight-plans/{id}/` - Обновление плана полета
- `DELETE /api/v1/flights/flight-plans/{id}/` - Удаление плана полета
- `POST /api/v1/flights/flight-plans/upload_excel/` - Загрузка планов полетов из Excel-файла

### Расширенная аналитика

- `GET /api/v1/flights/flight-plans/advanced_analytics/` - Расширенные метрики полетов
- `GET /api/v1/flights/flight-plans/peak_load_analysis/` - Анализ пиковой нагрузки
- `GET /api/v1/flights/flight-plans/flight_density_analysis/` - Анализ плотности полетов
- `GET /api/v1/flights/flight-plans/daily_activity_analysis/` - Анализ дневной активности
- `GET /api/v1/flights/flight-plans/regional_comparison/` - Сравнительный анализ регионов
- `GET /api/v1/flights/flight-plans/map_data/` - Получение данных для отображения на карте

### Статистика

- `GET /api/v1/flights/statistics/dashboard/` - Получение статистики для дашборда
- `GET /api/v1/flights/flight-plans/time_statistics/` - Статистика полетов по времени
- `GET /api/v1/flights/flight-plans/regional_statistics/` - Расширенная статистика по регионам
- `GET /api/v1/flights/flight-plans/operator_statistics/` - Статистика по операторам
- `GET /api/v1/flights/statistics/zero_flight_days_analysis/` - Анализ дней без полетов
- `GET /api/v1/flights/statistics/comprehensive_metrics/` - Комплексные метрики
- `GET /api/v1/flights/statistics/export_data/` - Экспорт данных в различных форматах

### Справочные данные

- `GET /api/v1/flights/operators/` - Получение списка операторов БАС
- `GET /api/v1/flights/operators/{id}/` - Детальная информация об операторе
- `GET /api/v1/flights/drone-types/` - Получение списка типов дронов
- `GET /api/v1/flights/drone-types/{id}/` - Детальная информация о типе дрона
- `GET /api/v1/flights/regions/` - Получение списка регионов РФ
- `GET /api/v1/flights/regions/{code}/flights/` - Получение полетов по конкретному региону
