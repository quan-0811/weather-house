-- 1. Create Keyspace
-- 'SimpleStrategy' is suitable for a single-datacenter/local setup.
CREATE KEYSPACE IF NOT EXISTS weather_house 
WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };

-- 2. Use the Keyspace
USE weather_house;

-- 3. Create Table
-- Data types map to PySpark: LongType->bigint, DoubleType->double, StringType->text
CREATE TABLE IF NOT EXISTS raw_weather_data (
    -- Primary Key: Partition by Location, Cluster by Time (descending) for fast dashboards
    location_id bigint,
    time timestamp,

    -- Quality Flag (Added for visualization)
    data_quality text,

    -- Metadata
    latitude double,
    longitude double,
    elevation double,
    utc_offset_seconds bigint,
    timezone text,
    timezone_abbreviation text,

    -- Atmospheric Metrics
    temperature_2m double,
    relative_humidity_2m double,
    dew_point_2m double,
    apparent_temperature double,
    pressure_msl double,
    surface_pressure double,
    weather_code text,

    -- Precipitation
    precipitation double,
    rain double,
    snowfall double,
    snow_depth double,

    -- Cloud Cover
    cloud_cover double,
    cloud_cover_low double,
    cloud_cover_mid double,
    cloud_cover_high double,

    -- Wind
    wind_speed_10m double,
    wind_speed_100m double,
    wind_direction_10m double,
    wind_direction_100m double,
    wind_gusts_10m double,

    -- Soil Metrics
    soil_temperature_0_to_7cm double,
    soil_temperature_7_to_28cm double,
    soil_temperature_28_to_100cm double,
    soil_temperature_100_to_255cm double,
    soil_moisture_0_to_7cm double,
    soil_moisture_7_to_28cm double,
    soil_moisture_28_to_100cm double,
    soil_moisture_100_to_255cm double,

    PRIMARY KEY (location_id, time)
) WITH CLUSTERING ORDER BY (time DESC);