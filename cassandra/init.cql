-- Initialize keyspace and tables for weather analytics platform
-- Aligned with weather_schema.py data models

CREATE KEYSPACE IF NOT EXISTS weather_ks
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE weather_ks;

CREATE TABLE IF NOT EXISTS weather_events (
    -- Partition key: region for geographic distribution
    station_region text,
    -- Clustering keys: timestamp DESC for latest-first, station_id for uniqueness
    timestamp timestamp,
    station_id text,
    
    -- Station metadata
    station_name text,
    station_longitude double,
    station_latitude double,
    station_elevation double,
    station_timezone text,
    
    -- Temperature measurements (°C)
    temperature_2m double,
    relative_humidity_2m double,
    dewpoint_2m double,
    apparent_temperature double,
    
    -- Pressure measurements (hPa)
    pressure_msl double,
    surface_pressure double,
    
    -- Precipitation measurements
    precipitation double,  -- mm
    rain double,          -- mm
    snowfall double,      -- cm
    
    -- Cloud cover (%)
    cloud_cover double,
    cloud_cover_low double,
    cloud_cover_mid double,
    cloud_cover_high double,
    
    -- Solar radiation (W/m²)
    shortwave_radiation double,
    direct_radiation double,
    direct_normal_irradiance double,
    diffuse_radiation double,
    global_tilted_irradiance double,
    
    -- Sunshine (seconds)
    sunshine_duration double,
    
    -- Wind measurements
    wind_speed_10m double,       -- km/h
    wind_speed_100m double,      -- km/h
    wind_direction_10m double,   -- degrees
    wind_direction_100m double,  -- degrees
    wind_gusts_10m double,       -- km/h
    
    -- Evapotranspiration (mm)
    et0_fao_evapotranspiration double,
    
    -- Other measurements
    weather_code int,                -- WMO weather code
    snow_depth double,               -- m
    vapor_pressure_deficit double,   -- kPa
    
    -- Soil temperature (°C) at different depths
    soil_temperature_0_to_7cm double,
    soil_temperature_7_to_28cm double,
    soil_temperature_28_to_100cm double,
    soil_temperature_100_to_255cm double,
    
    -- Soil moisture (m³/m³) at different depths
    soil_moisture_0_to_7cm double,
    soil_moisture_7_to_28cm double,
    soil_moisture_28_to_100cm double,
    soil_moisture_100_to_255cm double,
    
    PRIMARY KEY ((station_region), timestamp, station_id)
) WITH CLUSTERING ORDER BY (timestamp DESC, station_id ASC)
AND compaction = {'class': 'TimeWindowCompactionStrategy', 'compaction_window_size': '1', 'compaction_window_unit': 'DAYS'}
AND default_time_to_live = 604800  -- 7 days retention (matches Kafka retention)
AND comment = 'Raw weather sensor events partitioned by region for parallel processing';

-- Index for querying by station_id across regions
CREATE INDEX IF NOT EXISTS idx_events_station_id ON weather_events (station_id);

-- Index for weather code queries (e.g., find all storms)
CREATE INDEX IF NOT EXISTS idx_events_weather_code ON weather_events (weather_code);


-- ============================================================================
-- WEATHER AGGREGATES TABLE (from WeatherAggregate model)
-- Stores hourly/daily aggregated metrics computed by Spark
-- ============================================================================
CREATE TABLE IF NOT EXISTS weather_aggregates (
    -- Partition key: region for geographic distribution
    station_region text,
    -- Clustering keys: window_start DESC for latest-first, station_id
    window_start timestamp,
    station_id text,
    
    -- Station metadata
    station_name text,
    station_longitude double,
    station_latitude double,
    
    -- Time window
    window_end timestamp,
    
    -- Temperature metrics (°C)
    avg_temperature_2m double,
    min_temperature_2m double,
    max_temperature_2m double,
    avg_apparent_temperature double,
    avg_dewpoint_2m double,
    temperature_variance double,
    
    -- Humidity & Pressure metrics
    avg_relative_humidity_2m double,
    min_relative_humidity_2m double,
    max_relative_humidity_2m double,
    avg_pressure_msl double,
    avg_surface_pressure double,
    avg_vapor_pressure_deficit double,
    
    -- Precipitation metrics
    total_precipitation double,
    total_rain double,
    total_snowfall double,
    max_precipitation_intensity double,
    avg_snow_depth double,
    precipitation_event_count int,
    
    -- Cloud & Radiation metrics
    avg_cloud_cover double,
    avg_cloud_cover_low double,
    avg_cloud_cover_mid double,
    avg_cloud_cover_high double,
    total_sunshine_duration double,
    avg_shortwave_radiation double,
    avg_direct_radiation double,
    avg_direct_normal_irradiance double,
    avg_diffuse_radiation double,
    avg_global_tilted_irradiance double,
    
    -- Wind metrics
    avg_wind_speed_10m double,
    max_wind_speed_10m double,
    avg_wind_speed_100m double,
    max_wind_speed_100m double,
    avg_wind_direction_10m double,
    avg_wind_direction_100m double,
    max_wind_gusts_10m double,
    high_wind_event_count int,
    
    -- Soil temperature metrics (°C)
    avg_soil_temperature_0_to_7cm double,
    avg_soil_temperature_7_to_28cm double,
    avg_soil_temperature_28_to_100cm double,
    avg_soil_temperature_100_to_255cm double,
    
    -- Soil moisture metrics (m³/m³)
    avg_soil_moisture_0_to_7cm double,
    avg_soil_moisture_7_to_28cm double,
    avg_soil_moisture_28_to_100cm double,
    avg_soil_moisture_100_to_255cm double,
    
    -- Evapotranspiration
    total_et0_fao_evapotranspiration double,
    
    -- Weather code
    most_common_weather_code int,
    
    -- Derived comfort indices
    avg_heat_index double,
    avg_wind_chill double,
    
    -- Trend indicators
    temperature_trend text,  -- 'rising', 'falling', 'stable'
    pressure_trend text,     -- 'rising', 'falling', 'stable'
    
    -- Quality metrics
    data_completeness double,        -- Percentage (0-100)
    missing_parameters list<text>,   -- List of missing parameter names
    
    -- Metadata
    event_count int,
    first_event_timestamp timestamp,
    last_event_timestamp timestamp,
    
    PRIMARY KEY ((station_region), window_start, station_id)
) WITH CLUSTERING ORDER BY (window_start DESC, station_id ASC)
AND compaction = {'class': 'TimeWindowCompactionStrategy', 'compaction_window_size': '7', 'compaction_window_unit': 'DAYS'}
AND default_time_to_live = 2592000  -- 30 days retention
AND comment = 'Hourly/daily aggregated weather metrics for analytics and trending';

-- Index for querying by station_id
CREATE INDEX IF NOT EXISTS idx_aggregates_station_id ON weather_aggregates (station_id);


-- ============================================================================
-- WEATHER ALERTS TABLE (from WeatherAlert model)
-- Stores triggered alerts for extreme weather conditions
-- ============================================================================
CREATE TABLE IF NOT EXISTS weather_alerts (
    -- Partition key: region for geographic distribution
    station_region text,
    -- Clustering keys: timestamp DESC for latest-first, alert_id for uniqueness
    timestamp timestamp,
    alert_id text,
    
    -- Alert versioning
    alert_version int,
    parent_alert_id text,
    
    -- Station metadata
    station_id text,
    station_name text,
    station_longitude double,
    station_latitude double,
    station_elevation double,
    
    -- Temporal information
    alert_start_time timestamp,
    alert_end_time timestamp,
    
    -- Alert classification
    alert_type text,      -- AlertType enum value
    severity text,        -- Severity enum value (info, advisory, warning, critical, emergency)
    certainty text,       -- 'observed', 'likely', 'possible', 'unlikely'
    urgency text,         -- 'immediate', 'expected', 'future', 'past'
    
    -- Trigger information
    parameter text,           -- Parameter name that triggered alert
    trigger_value double,     -- Actual measured value
    threshold double,         -- Threshold that was exceeded
    threshold_type text,      -- 'upper', 'lower', 'range'
    unit text,               -- Unit of measurement
    
    -- Alert details
    title text,
    message text,
    description text,
    recommendation text,
    
    -- Impact assessment
    impact_level text,                -- 'minimal', 'minor', 'moderate', 'major', 'severe'
    vulnerable_groups list<text>,     -- List of affected groups
    
    -- Duration tracking
    duration_minutes int,
    expected_duration_minutes int,
    
    -- Status tracking
    alert_status text,  -- 'active', 'updated', 'extended', 'cancelled', 'expired'
    
    PRIMARY KEY ((station_region), timestamp, alert_id)
) WITH CLUSTERING ORDER BY (timestamp DESC, alert_id ASC)
AND compaction = {'class': 'TimeWindowCompactionStrategy', 'compaction_window_size': '1', 'compaction_window_unit': 'DAYS'}
AND default_time_to_live = 86400  -- 1 day retention (time-sensitive alerts)
AND comment = 'Weather alerts and warnings partitioned by region for fast access';

-- Index for querying alerts by severity (find all critical alerts)
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON weather_alerts (severity);

-- Index for querying alerts by type (find all heat wave alerts)
CREATE INDEX IF NOT EXISTS idx_alerts_type ON weather_alerts (alert_type);

-- Index for querying alerts by status (find all active alerts)
CREATE INDEX IF NOT EXISTS idx_alerts_status ON weather_alerts (alert_status);

-- Index for querying by station_id
CREATE INDEX IF NOT EXISTS idx_alerts_station_id ON weather_alerts (station_id);