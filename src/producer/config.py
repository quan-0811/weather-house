KAFKA_BROKERS = ['localhost:9092', 'localhost:9093', 'localhost:9094']
TOPIC_NAME = 'weather-events'
INPUT_FILE = '../../data/final/final_data.csv'
CORRUPTION_PROBABILITY = 0.05
DUPLICATE_PROBABILITY = 0.05
NUMERIC_FIELDS = [
    "temperature_2m", 
    "relative_humidity_2m", 
    "dew_point_2m", 
    "apparent_temperature",
    "precipitation", 
    "rain", 
    "snowfall", 
    "snow_depth", 
    "pressure_msl", 
    "surface_pressure",
    "cloud_cover", 
    "cloud_cover_low", 
    "cloud_cover_mid", 
    "cloud_cover_high",
    "wind_speed_10m", 
    "wind_speed_100m", 
    "wind_direction_10m", 
    "wind_direction_100m", 
    "wind_gusts_10m",
    "soil_temperature_0_to_7cm", 
    "soil_temperature_7_to_28cm", 
    "soil_temperature_28_to_100cm", 
    "soil_temperature_100_to_255cm",
    "soil_moisture_0_to_7cm", 
    "soil_moisture_7_to_28cm", 
    "soil_moisture_28_to_100cm", 
    "soil_moisture_100_to_255cm"
]