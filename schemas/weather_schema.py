from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class WeatherEvent(BaseModel):
    """Raw sensor event - published to weather-events topic""" 
    # Station metadata
    station_id: str = Field(..., description="Unique station identifier")
    station_name: str = Field(..., description="Name of the weather station")
    station_region: str = Field(..., description="Geographical region of the weather station")
    station_longitude: float = Field(..., description="Longitude of the weather station")
    station_latitude: float = Field(..., description="Latitude of the weather station")
    station_elevation: float = Field(..., description="Elevation of the weather station (meters)")
    station_timezone: str = Field(..., description="Timezone of the weather station (e.g., 'UTC', 'America/New_York')")
    timestamp: datetime = Field(..., description="Timestamp of the measurement in ISO 8601 format")
    
    # Temperature 
    temperature_2m: Optional[float] = Field(None, description="Air temperature at 2 meters above ground (°C)")
    relative_humidity_2m: Optional[float] = Field(None, description="Relative humidity at 2 meters above ground (%)")
    dewpoint_2m: Optional[float] = Field(None, description="Dew point temperature at 2 meters above ground (°C)")
    apparent_temperature: Optional[float] = Field(None, description="Apparent temperature combining wind chill, humidity and solar radiation (°C)")
    
    # Pressure 
    pressure_msl: Optional[float] = Field(None, description="Atmospheric air pressure reduced to mean sea level or pressure at surface (hPa)")
    surface_pressure: Optional[float] = Field(None, description="Atmospheric pressure at surface (hPa)")
    
    # Precipitation 
    precipitation: Optional[float] = Field(None, description="Total precipitation (rain, showers, snow) sum of preceding hour (mm)")
    rain: Optional[float] = Field(None, description="Only liquid precipitation of preceding hour including local showers and rain from large scale systems (mm)")
    snowfall: Optional[float] = Field(None, description="Snowfall amount of preceding hour (cm)")
    
    # Cloud cover 
    cloud_cover: Optional[float] = Field(None, description="Total cloud cover as area fraction (%)")
    cloud_cover_low: Optional[float] = Field(None, description="Low level clouds and fog up to 2 km altitude (%)")
    cloud_cover_mid: Optional[float] = Field(None, description="Mid level clouds from 2 to 6 km altitude (%)")
    cloud_cover_high: Optional[float] = Field(None, description="High level clouds from 6 km altitude (%)")

    # Radiation 
    shortwave_radiation: Optional[float] = Field(None, description="Shortwave solar radiation as average of preceding hour (W/m²)")
    direct_radiation: Optional[float] = Field(None, description="Direct solar radiation as average of preceding hour on horizontal plane (W/m²)")
    direct_normal_irradiance: Optional[float] = Field(None, description="Direct solar radiation on normal plane (W/m²)")
    diffuse_radiation: Optional[float] = Field(None, description="Diffuse solar radiation as average of preceding hour (W/m²)")
    global_tilted_irradiance: Optional[float] = Field(None, description="Total radiation received on tilted plane (W/m²)")

    # Sunshine 
    sunshine_duration: Optional[float] = Field(None, description="Number of seconds of sunshine of preceding hour per hour calculated by direct normalized irradiance exceeding 120 W/m² (s)")
    
    # Wind
    wind_speed_10m: Optional[float] = Field(None, description="Wind speed at 10 or 100 meters above ground (km/h)")
    wind_speed_100m: Optional[float] = Field(None, description="Wind speed at 100 meters above ground (km/h)")
    wind_direction_10m: Optional[float] = Field(None, description="Wind direction at 10 or 100 meters above ground (degrees)")
    wind_direction_100m: Optional[float] = Field(None, description="Wind direction at 100 meters above ground (degrees)")
    wind_gusts_10m: Optional[float] = Field(None, description="Gusts at 10 meters above ground of indicated hour (km/h)")

    # Evapotranspiration 
    et0_fao_evapotranspiration: Optional[float] = Field(None, description="ET₀ Reference Evapotranspiration of well watered grass field (mm)")
    
    # Other
    weather_code: Optional[int] = Field(None, description="Weather condition as numeric code (WMO code)")
    snow_depth: Optional[float] = Field(None, description="Snow depth on ground (m)")
    vapor_pressure_deficit: Optional[float] = Field(None, description="Vapor Pressure Deficit (VPD) in kilopascal (kPa)")
    
    # Soil Temperature 
    soil_temperature_0_to_7cm: Optional[float] = Field(None, description="Average temperature at different soil levels below ground (°C)")
    soil_temperature_7_to_28cm: Optional[float] = Field(None, description="Average temperature at 7-28cm depth (°C)")
    soil_temperature_28_to_100cm: Optional[float] = Field(None, description="Average temperature at 28-100cm depth (°C)")
    soil_temperature_100_to_255cm: Optional[float] = Field(None, description="Average temperature at 100-255cm depth (°C)")

    # Soil Moisture 
    soil_moisture_0_to_7cm: Optional[float] = Field(None, description="Average soil water content as volumetric mixing ratio at 0-7cm depth (m³/m³)")
    soil_moisture_7_to_28cm: Optional[float] = Field(None, description="Average soil water content at 7-28cm depth (m³/m³)")
    soil_moisture_28_to_100cm: Optional[float] = Field(None, description="Average soil water content at 28-100cm depth (m³/m³)")
    soil_moisture_100_to_255cm: Optional[float] = Field(None, description="Average soil water content at 100-255cm depth (m³/m³)")

class WeatherAggregate(BaseModel):
    """Aggregated metrics - published to weather-aggregates topic"""
    # Station metadata
    station_id: str = Field(..., description="Unique station identifier")
    station_name: str = Field(..., description="Name of the weather station")
    station_region: str = Field(..., description="Geographical region of the weather station")
    station_longitude: float = Field(..., description="Longitude of the weather station")
    station_latitude: float = Field(..., description="Latitude of the weather station")
    
    # Time window
    window_start: datetime = Field(..., description="Start of aggregation window")
    window_end: datetime = Field(..., description="End of aggregation window")
    
    # Temperature metrics (°C)
    avg_temperature_2m: Optional[float] = Field(None, description="Average air temperature at 2m (°C)")
    min_temperature_2m: Optional[float] = Field(None, description="Minimum air temperature at 2m (°C)")
    max_temperature_2m: Optional[float] = Field(None, description="Maximum air temperature at 2m (°C)")
    avg_apparent_temperature: Optional[float] = Field(None, description="Average apparent temperature (°C)")
    avg_dewpoint_2m: Optional[float] = Field(None, description="Average dew point temperature at 2m (°C)")
    
    # Humidity & Pressure metrics
    avg_relative_humidity_2m: Optional[float] = Field(None, description="Average relative humidity at 2m (%)")
    min_relative_humidity_2m: Optional[float] = Field(None, description="Minimum relative humidity at 2m (%)")
    max_relative_humidity_2m: Optional[float] = Field(None, description="Maximum relative humidity at 2m (%)")
    avg_pressure_msl: Optional[float] = Field(None, description="Average atmospheric pressure reduced to mean sea level (hPa)")
    avg_surface_pressure: Optional[float] = Field(None, description="Average atmospheric pressure at surface (hPa)")
    avg_vapor_pressure_deficit: Optional[float] = Field(None, description="Average vapor pressure deficit (kPa)")
    
    # Precipitation metrics
    total_precipitation: Optional[float] = Field(None, description="Total precipitation sum (mm)")
    total_rain: Optional[float] = Field(None, description="Total liquid precipitation sum (mm)")
    total_snowfall: Optional[float] = Field(None, description="Total snowfall sum (cm)")
    max_precipitation_intensity: Optional[float] = Field(None, description="Maximum precipitation intensity (mm/h)")
    avg_snow_depth: Optional[float] = Field(None, description="Average snow depth on ground (m)")
    
    # Cloud & Radiation metrics
    avg_cloud_cover: Optional[float] = Field(None, description="Average total cloud cover (%)")
    avg_cloud_cover_low: Optional[float] = Field(None, description="Average low level cloud cover (%)")
    avg_cloud_cover_mid: Optional[float] = Field(None, description="Average mid level cloud cover (%)")
    avg_cloud_cover_high: Optional[float] = Field(None, description="Average high level cloud cover (%)")
    total_sunshine_duration: Optional[float] = Field(None, description="Total sunshine duration (seconds)")
    avg_shortwave_radiation: Optional[float] = Field(None, description="Average shortwave solar radiation (W/m²)")
    avg_direct_radiation: Optional[float] = Field(None, description="Average direct solar radiation (W/m²)")
    avg_direct_normal_irradiance: Optional[float] = Field(None, description="Average direct normal irradiance (W/m²)")
    avg_diffuse_radiation: Optional[float] = Field(None, description="Average diffuse solar radiation (W/m²)")
    avg_global_tilted_irradiance: Optional[float] = Field(None, description="Average total radiation on tilted plane (W/m²)")
    
    # Wind metrics
    avg_wind_speed_10m: Optional[float] = Field(None, description="Average wind speed at 10m (km/h)")
    max_wind_speed_10m: Optional[float] = Field(None, description="Maximum wind speed at 10m (km/h)")
    avg_wind_speed_100m: Optional[float] = Field(None, description="Average wind speed at 100m (km/h)")
    max_wind_speed_100m: Optional[float] = Field(None, description="Maximum wind speed at 100m (km/h)")
    avg_wind_direction_10m: Optional[float] = Field(None, description="Average wind direction at 10m (degrees)")
    avg_wind_direction_100m: Optional[float] = Field(None, description="Average wind direction at 100m (degrees)")
    max_wind_gusts_10m: Optional[float] = Field(None, description="Maximum wind gusts at 10m (km/h)")
    
    # Soil temperature metrics (°C)
    avg_soil_temperature_0_to_7cm: Optional[float] = Field(None, description="Average soil temperature at 0-7cm depth (°C)")
    avg_soil_temperature_7_to_28cm: Optional[float] = Field(None, description="Average soil temperature at 7-28cm depth (°C)")
    avg_soil_temperature_28_to_100cm: Optional[float] = Field(None, description="Average soil temperature at 28-100cm depth (°C)")
    avg_soil_temperature_100_to_255cm: Optional[float] = Field(None, description="Average soil temperature at 100-255cm depth (°C)")
    
    # Soil moisture metrics (m³/m³)
    avg_soil_moisture_0_to_7cm: Optional[float] = Field(None, description="Average soil moisture at 0-7cm depth (m³/m³)")
    avg_soil_moisture_7_to_28cm: Optional[float] = Field(None, description="Average soil moisture at 7-28cm depth (m³/m³)")
    avg_soil_moisture_28_to_100cm: Optional[float] = Field(None, description="Average soil moisture at 28-100cm depth (m³/m³)")
    avg_soil_moisture_100_to_255cm: Optional[float] = Field(None, description="Average soil moisture at 100-255cm depth (m³/m³)")
    
    # Evapotranspiration
    total_et0_fao_evapotranspiration: Optional[float] = Field(None, description="Total ET₀ reference evapotranspiration (mm)")
    
    # Weather code
    most_common_weather_code: Optional[int] = Field(None, description="Most frequently occurring weather condition code (WMO code)")
    
    # Statistical metrics
    temperature_variance: Optional[float] = Field(None, description="Variance in temperature readings (°C²)")
    precipitation_event_count: Optional[int] = Field(None, description="Number of events with precipitation > 0")
    high_wind_event_count: Optional[int] = Field(None, description="Number of events with wind speed > 50 km/h")
    
    # Derived comfort indices
    avg_heat_index: Optional[float] = Field(None, description="Average heat index combining temperature and humidity (°C)")
    avg_wind_chill: Optional[float] = Field(None, description="Average wind chill factor (°C)")
    
    # Trend indicators (compared to previous window)
    temperature_trend: Optional[str] = Field(None, description="Temperature trend: 'rising', 'falling', 'stable'")
    pressure_trend: Optional[str] = Field(None, description="Pressure trend: 'rising', 'falling', 'stable'")
    
    # Quality metrics
    data_completeness: Optional[float] = Field(None, description="Percentage of expected data points received (%)")
    missing_parameters: Optional[list[str]] = Field(None, description="List of parameters with missing data")
    
    # Metadata
    event_count: int = Field(..., description="Number of events aggregated in this window")
    first_event_timestamp: Optional[datetime] = Field(None, description="Timestamp of first event in window")
    last_event_timestamp: Optional[datetime] = Field(None, description="Timestamp of last event in window")

class AlertType(str, Enum):
    # Temperature alerts
    EXTREME_HEAT = "extreme_heat"
    EXTREME_COLD = "extreme_cold"
    HEAT_WAVE = "heat_wave"
    COLD_WAVE = "cold_wave"
    FROST = "frost"
    FREEZING = "freezing"
    HEAT_STRESS = "heat_stress"
    
    # Precipitation alerts
    HEAVY_RAIN = "heavy_rain"
    FLOOD_RISK = "flood_risk"
    FLASH_FLOOD = "flash_flood"
    DROUGHT = "drought"
    HEAVY_SNOW = "heavy_snow"
    BLIZZARD = "blizzard"
    ICE_STORM = "ice_storm"
    HAIL = "hail"
    
    # Wind alerts
    HIGH_WIND = "high_wind"
    STORM = "storm"
    GALE_WARNING = "gale_warning"
    HURRICANE = "hurricane"
    TORNADO = "tornado"
    WINDSTORM = "windstorm"
    
    # Atmospheric alerts
    LOW_PRESSURE = "low_pressure"
    HIGH_PRESSURE = "high_pressure"
    PRESSURE_DROP = "pressure_drop"
    PRESSURE_RISE = "pressure_rise"
    
    # Humidity alerts
    EXTREME_HUMIDITY = "extreme_humidity"
    LOW_HUMIDITY = "low_humidity"
    FOG = "fog"
    DEW_POINT_ALERT = "dew_point_alert"
    
    # Soil alerts
    SOIL_DROUGHT = "soil_drought"
    SOIL_SATURATION = "soil_saturation"
    SOIL_FREEZE = "soil_freeze"
    EROSION_RISK = "erosion_risk"
    
    # Radiation alerts
    HIGH_UV = "high_uv"
    EXTREME_UV = "extreme_uv"
    LOW_SUNSHINE = "low_sunshine"
    SOLAR_STORM = "solar_storm"
    
    # Cloud alerts
    DENSE_CLOUD = "dense_cloud"
    CLEAR_SKY = "clear_sky"
    
    # Comfort alerts
    DISCOMFORT_INDEX_HIGH = "discomfort_index_high"
    WIND_CHILL_WARNING = "wind_chill_warning"
    
    # Agricultural alerts
    CROP_STRESS = "crop_stress"
    EVAPOTRANSPIRATION_HIGH = "evapotranspiration_high"
    IRRIGATION_NEEDED = "irrigation_needed"
    
    # General
    SEVERE_WEATHER = "severe_weather"
    WEATHER_CHANGE = "weather_change"

class Severity(str, Enum):
    INFO = "info"           # Informational, no action needed
    ADVISORY = "advisory"   # Be aware, monitor situation
    WARNING = "warning"     # Take precautions
    CRITICAL = "critical"   # Immediate action required
    EMERGENCY = "emergency" # Life-threatening situation

class WeatherAlert(BaseModel):
    """Alert event - published to weather-alerts topic"""
    # Alert identification
    alert_id: str = Field(..., description="Unique alert identifier")
    alert_version: Optional[int] = Field(1, description="Version number if alert is updated")
    parent_alert_id: Optional[str] = Field(None, description="ID of parent alert if this is an update/continuation")
    
    # Station metadata
    station_id: str = Field(..., description="Unique station identifier")
    station_name: str = Field(..., description="Name of the weather station")
    station_region: str = Field(..., description="Geographical region of the weather station")
    station_longitude: float = Field(..., description="Longitude of the weather station")
    station_latitude: float = Field(..., description="Latitude of the weather station")
    station_elevation: Optional[float] = Field(None, description="Elevation of the weather station (meters)")
    
    # Temporal information
    timestamp: datetime = Field(..., description="Timestamp when alert was triggered")
    alert_start_time: Optional[datetime] = Field(None, description="When the condition began")
    alert_end_time: Optional[datetime] = Field(None, description="Expected end time of the condition")
    
    # Alert classification
    alert_type: AlertType = Field(..., description="Type of weather alert")
    severity: Severity = Field(..., description="Severity level of the alert")
    certainty: Optional[str] = Field(None, description="Certainty level: 'observed', 'likely', 'possible', 'unlikely'")
    urgency: Optional[str] = Field(None, description="Urgency: 'immediate', 'expected', 'future', 'past'")
    
    # Trigger information
    parameter: str = Field(..., description="Parameter that triggered alert (e.g., 'temperature_2m', 'wind_gusts_10m')")
    trigger_value: float = Field(..., description="Actual measured value that triggered the alert")
    threshold: float = Field(..., description="Threshold value that was exceeded")
    threshold_type: Optional[str] = Field(None, description="Type of threshold: 'upper', 'lower', 'range'")
    unit: str = Field(..., description="Unit of measurement (e.g., '°C', 'mm', 'km/h', '%', 'hPa')")
    
    # Alert details
    title: Optional[str] = Field(None, description="Short alert title")
    message: str = Field(..., description="Human-readable alert message describing the condition")
    description: Optional[str] = Field(None, description="Detailed description of the weather condition")
    recommendation: Optional[str] = Field(None, description="Recommended actions or precautions to take")
    
    # Impact assessment
    impact_level: Optional[str] = Field(None, description="Expected impact: 'minimal', 'minor', 'moderate', 'major', 'severe'")
    vulnerable_groups: Optional[list[str]] = Field(None, description="Groups at risk: 'children', 'elderly', 'outdoor_workers', etc.")
    
    # Duration tracking
    duration_minutes: Optional[int] = Field(None, description="How long the condition has persisted (minutes)")
    expected_duration_minutes: Optional[int] = Field(None, description="Expected duration of the condition (minutes)")
    
    # Status tracking
    alert_status: Optional[str] = Field("active", description="Status: 'active', 'updated', 'extended', 'cancelled', 'expired'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "alert_20241026_103000_HN001_extreme_heat",
                "alert_version": 1,
                "parent_alert_id": None,
                "station_id": "HN_001",
                "station_name": "Hanoi Center",
                "station_region": "north",
                "station_longitude": 105.8342,
                "station_latitude": 21.0278,
                "station_elevation": 12.0,
                "timestamp": "2024-10-26T10:30:00Z",
                "alert_start_time": "2024-10-26T08:30:00Z",
                "alert_end_time": "2024-10-26T16:00:00Z",
                "alert_type": "extreme_heat",
                "severity": "warning",
                "certainty": "observed",
                "urgency": "immediate",
                "parameter": "temperature_2m",
                "trigger_value": 42.5,
                "threshold": 40.0,
                "threshold_type": "upper",
                "unit": "°C",
                "title": "Extreme Heat Warning",
                "message": "Extreme heat detected: Temperature reached 42.5°C, exceeding threshold of 40°C",
                "description": "Dangerously high temperatures are occurring in the region. Heat index values suggest significant discomfort and potential health risks.",
                "recommendation": "Avoid outdoor activities during peak hours (11am-3pm). Stay hydrated, seek air-conditioned spaces, and check on vulnerable individuals.",
                "impact_level": "major",
                "vulnerable_groups": ["elderly", "children", "outdoor_workers", "chronic_illness"],
                "duration_minutes": 120,
                "expected_duration_minutes": 330,
                "alert_status": "active"
            }
        }