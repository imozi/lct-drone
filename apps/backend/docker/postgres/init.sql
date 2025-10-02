-- Создание расширений для работы с геопространственными данными
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_sfcgal;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- Создание индексов для оптимизации пространственных запросов
-- (будут созданы автоматически Django при создании моделей с GeoFields)