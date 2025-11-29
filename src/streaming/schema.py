from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType

# 1. Full Schema matching incoming CSV/JSON keys EXACTLY
weather_schema = StructType([
    StructField("location_id", LongType(), True),
    StructField("latitude", DoubleType(), True),
    StructField("longitude", DoubleType(), True),
    StructField("elevation", DoubleType(), True),
    StructField("utc_offset_seconds", LongType(), True),
    StructField("timezone", StringType(), True),
    StructField("timezone_abbreviation", StringType(), True),
    StructField("time", StringType(), True),
    
    # Atmospheric Data
    StructField("temperature_2m", DoubleType(), True),
    StructField("relative_humidity_2m", DoubleType(), True),
    StructField("dew_point_2m", DoubleType(), True),
    StructField("apparent_temperature", DoubleType(), True),
    StructField("precipitation", DoubleType(), True),
    StructField("rain", DoubleType(), True),
    StructField("snowfall", DoubleType(), True),
    StructField("snow_depth", DoubleType(), True),
    StructField("weather_code", StringType(), True),
    StructField("pressure_msl", DoubleType(), True),
    StructField("surface_pressure", DoubleType(), True),
    
    # Cloud Cover
    StructField("cloud_cover", DoubleType(), True),
    StructField("cloud_cover_low", DoubleType(), True),
    StructField("cloud_cover_mid", DoubleType(), True),
    StructField("cloud_cover_high", DoubleType(), True),
    
    # Wind
    StructField("wind_speed_10m", DoubleType(), True),
    StructField("wind_speed_100m", DoubleType(), True),
    StructField("wind_direction_10m", DoubleType(), True),
    StructField("wind_direction_100m", DoubleType(), True),
    StructField("wind_gusts_10m", DoubleType(), True),
    
    # Soil Temperature
    StructField("soil_temperature_0_to_7cm", DoubleType(), True),
    StructField("soil_temperature_7_to_28cm", DoubleType(), True),
    StructField("soil_temperature_28_to_100cm", DoubleType(), True),
    StructField("soil_temperature_100_to_255cm", DoubleType(), True),
    
    # Soil Moisture
    StructField("soil_moisture_0_to_7cm", DoubleType(), True),
    StructField("soil_moisture_7_to_28cm", DoubleType(), True),
    StructField("soil_moisture_28_to_100cm", DoubleType(), True),
    StructField("soil_moisture_100_to_255cm", DoubleType(), True)
])