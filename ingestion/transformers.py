from typing import Optional
from datetime import datetime, timezone
import pytz


def parse_temperature(tmp_value: str) -> Optional[float]:
    """
    Parse ISD temperature field: "+0044,1" → 4.4°C (the "1" is only the flag, not the value)
    Args:
        tmp_value: ISD temperature string (e.g., "+0044,1" or "-0025,1")
    Returns:
        Temperature in Celsius, or None if missing/invalid
    """
    if not tmp_value or tmp_value.strip() == "":
        return None
    
    if tmp_value.startswith("+9999") or tmp_value.startswith("-9999"):
        return None
    
    try:
        sign = -1 if tmp_value.startswith('-') else 1
        value_str = tmp_value.split(',')[0].lstrip('+-')
        value = int(value_str)
        return sign * (value / 10.0)
    except (ValueError, IndexError):
        return None


def parse_pressure(slp_value: str) -> Optional[float]:
    """
    Parse ISD pressure field: "10117,1" → 1011.7 hPa  
    Args:
        slp_value: ISD pressure string (e.g., "10117,1")
    Returns:
        Pressure in hPa, or None if missing/invalid
    """
    if not slp_value or slp_value.strip() == "":
        return None

    if slp_value == "99999,9" or slp_value.startswith("99999"):
        return None

    try:
        value_str = slp_value.split(',')[0]
        value = float(value_str)
        return value / 10.0
    except (ValueError, IndexError):
        return None


def parse_relative_humidity(ah1_value: str) -> Optional[float]:
    """
    Parse ISD relative humidity field: "099,9" → 99.0%
    Args:
        ah1_value: ISD humidity string (e.g., "099,9")
    Returns:
        Humidity percentage (0-100), or None if missing/invalid
    """
    if not ah1_value or ah1_value.strip() == "":
        return None
    
    if ah1_value == "999,9" or ah1_value.startswith("999"):
        return None
    
    try:
        value_str = ah1_value.split(',')[0]
        value = int(value_str)
        if 0 <= value <= 100:
            return float(value)
        return None
    except (ValueError, IndexError):
        return None


def parse_wind(wnd_value: str) -> tuple[Optional[float], Optional[float]]:
    """
    Parse ISD wind field: "040,1,N,0026,1" → (direction=40°, speed=93.6 km/h)
    Args:
        wnd_value: ISD wind string (e.g., "040,1,N,0026,1")
    Returns:
        Tuple of (direction_degrees, speed_kmh) or (None, None) if missing
    """
    if not wnd_value or wnd_value.strip() == "":
        return None, None
    
    if wnd_value == "999,9,9,9999,9" or wnd_value.startswith("999,9"):
        return None, None
    
    try:
        parts = wnd_value.split(',')
        if len(parts) < 4:
            return None, None
        
        direction_str = parts[0]
        if direction_str == "999":
            direction = None
        else:
            direction = int(direction_str)
            if direction < 0 or direction > 360:
                direction = None

        speed_str = parts[3]
        if speed_str == "9999":
            speed_kmh = None
        else:
            speed_raw = int(speed_str)
            speed_kmh = speed_raw * 1.852 # convert knots to km/h
        
        return direction, speed_kmh
    except (ValueError, IndexError):
        return None, None


def parse_wind_gust(ga1_value: str) -> Optional[float]:
    """
    Parse ISD wind gust field: "30,5" → 108.0 km/h
    Args:
        ga1_value: ISD gust string (e.g., "30,5")
    Returns:
        Gust speed in km/h, or None if missing/invalid
    """
    if not ga1_value or ga1_value.strip() == "":
        return None
    
    try:
        parts = ga1_value.split(',')
        if len(parts) < 1:
            return None
        
        speed_str = parts[0]
        if speed_str == "99" or speed_str == "":
            return None
        
        speed_raw = int(speed_str)
        return speed_raw * 1.852 # convert knots to km/h
    except (ValueError, IndexError):
        return None


def parse_precipitation(aa1_value: str) -> Optional[float]:
    """
    Parse ISD precipitation field: "01,00100,9,5" → 2.54 mm
    Args:
        aa1_value: ISD precipitation string (e.g., "01,00100,9,5")
    Returns:
        Precipitation in mm, or None if missing/invalid
    """
    if not aa1_value or aa1_value.strip() == "":
        return None
    
    if aa1_value.startswith("99,") or aa1_value == "99,99999,9,9":
        return None
    
    try:
        parts = aa1_value.split(',')
        if len(parts) < 2:
            return None
        
        period = parts[0]
        if period == "99":
            return None
        
        depth_str = parts[1]
        if depth_str == "99999" or depth_str == "":
            return None
        
        depth_thousandths = int(depth_str)
        depth_inches = depth_thousandths / 1000.0
        depth_mm = depth_inches * 25.4
        
        return depth_mm
    except (ValueError, IndexError):
        return None


def parse_snowfall(ab1_value: str) -> Optional[float]:
    """
    Parse ISD snowfall field: "01,00100,9,5" → 2.54 mm
    Args:
        ab1_value: ISD snowfall string
    Returns:
        Snowfall in cm, or None if missing/invalid
    """
    if not ab1_value or ab1_value.strip() == "":
        return None
    
    if ab1_value.startswith("99,"):
        return None
    
    try:
        parts = ab1_value.split(',')
        if len(parts) < 2:
            return None
        
        depth_str = parts[1]
        if depth_str == "99999" or depth_str == "":
            return None
        
        depth_thousandths = int(depth_str)
        depth_inches = depth_thousandths / 1000.0
        depth_cm = depth_inches * 2.54
        
        return depth_cm
    except (ValueError, IndexError):
        return None


def parse_snow_depth(ab1_value: str) -> Optional[float]:
    """
    Parse ISD snow depth field: Convert to meters
    Args:
        ab1_value: ISD snow depth string
    Returns:
        Snow depth in meters, or None if missing/invalid
    """
    if not ab1_value or ab1_value.strip() == "":
        return None
    
    if ab1_value.startswith("99,"):
        return None
    
    try:
        parts = ab1_value.split(',')
        if len(parts) < 2:
            return None
        
        depth_str = parts[1]
        if depth_str == "99999" or depth_str == "":
            return None
        
        depth_thousandths = int(depth_str)
        depth_inches = depth_thousandths / 1000.0
        depth_meters = depth_inches / 39.37
        
        return depth_meters
    except (ValueError, IndexError):
        return None


def parse_cloud_cover(ai1_value: str) -> Optional[float]:
    """
    Parse ISD cloud cover field: "04,U,0366,9" → 50.0%
    Args:
        ai1_value: ISD cloud cover string (e.g., "04,U,0366,9")    
    Returns:
        Cloud cover percentage (0-100), or None if missing/invalid
    """
    if not ai1_value or ai1_value.strip() == "":
        return None
    
    if ai1_value.startswith("99,") or ai1_value == "99,99,99999,9":
        return None
    
    try:
        parts = ai1_value.split(',')
        if len(parts) < 1:
            return None
        
        oktas_str = parts[0]
        if oktas_str == "99" or oktas_str == "":
            return None
        
        oktas = int(oktas_str)
        if 0 <= oktas <= 8:
            percentage = oktas * 12.5
            return percentage
        return None
    except (ValueError, IndexError):
        return None


def parse_weather_code(ke1_value: str) -> Optional[int]:
    """
    Parse ISD weather code field: "RA" → 61 (WMO code for rain)
    Args:
        ke1_value: ISD weather code string (e.g., "RA" for rain)
    Returns:
        WMO weather code as integer, or None if missing/invalid
    """
    if not ke1_value or ke1_value.strip() == "":
        return None
    
    weather_code_map = {
        "RA": 61,   # Rain
        "SN": 71,   # Snow
        "FG": 45,   # Fog
        "BR": 10,   # Mist
        "TS": 95,   # Thunderstorm
        "DZ": 53,   # Drizzle
    }
    
    code = weather_code_map.get(ke1_value.strip().upper())
    if code:
        return code
    
    return None


def derive_region_from_name(name: str) -> str:
    """
    Extract region from station name: "ROCHESTER, NY US" → "north" (based on state abbreviations)
    Args:
        name: Station name string
    Returns:
        Region string (north, south, east, west, unknown)
    """
    if not name:
        return "unknown"
    
    name_upper = name.upper()
    
    north_states = ["NY", "MA", "VT", "NH", "ME", "CT", "RI", "PA", "NJ", 
                    "MI", "WI", "MN", "ND", "SD", "MT", "ID", "WA", "OR"]
    south_states = ["TX", "FL", "GA", "NC", "SC", "AL", "MS", "LA", "AR", 
                    "OK", "TN", "KY", "WV", "VA", "MD", "DE"]
    west_states = ["CA", "NV", "AZ", "NM", "CO", "UT", "WY"]
    east_states = ["ME", "NH", "VT", "MA", "RI", "CT", "NY", "NJ", "PA", 
                   "DE", "MD", "VA", "NC", "SC", "GA", "FL"]
    
    for state in north_states:
        if state in name_upper:
            return "north"
    
    for state in south_states:
        if state in name_upper:
            return "south"
    
    for state in west_states:
        if state in name_upper:
            return "west"
    
    for state in east_states:
        if state in name_upper:
            return "east"
    
    return "unknown"


def calculate_timezone_from_longitude(longitude: float) -> str:
    """
    Estimate timezone from longitude
    Args:
        longitude: Longitude in decimal degrees
    Returns:
        Timezone string (e.g., "America/New_York")
    """
    if longitude is None:
        return "UTC"
    
    offset_hours = int(longitude / 15)
    
    if -85 <= longitude <= -67:  # Eastern US
        return "America/New_York"
    elif -102 <= longitude < -85:  # Central US
        return "America/Chicago"
    elif -115 <= longitude < -102:  # Mountain US
        return "America/Denver"
    elif longitude < -115:  # Pacific US
        return "America/Los_Angeles"
    else:
        return "UTC"


def transform_isd_to_weather_event(isd_row: dict) -> dict:
    """
    Main transformation function: ISD CSV row → WeatherEvent dict
    Args:
        isd_row: Dictionary with ISD column names as keys
    Returns:
        Dictionary compatible with WeatherEvent Pydantic model
    """
    station_id = isd_row.get('STATION', '')
    station_name = isd_row.get('NAME', '')
    station_latitude = float(isd_row.get('LATITUDE', 0))
    station_longitude = float(isd_row.get('LONGITUDE', 0))
    station_elevation = float(isd_row.get('ELEVATION', 0))
    
    timestamp_str = isd_row.get('DATE', '')
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        timestamp = datetime.now(timezone.utc)
    
    station_region = derive_region_from_name(station_name)
    station_timezone = calculate_timezone_from_longitude(station_longitude)
    
    # Temperature fields
    temperature_2m = parse_temperature(isd_row.get('TMP', ''))
    dewpoint_2m = parse_temperature(isd_row.get('DEW', ''))
    relative_humidity_2m = parse_relative_humidity(isd_row.get('AH1', ''))
    
    # Pressure fields
    pressure_msl = parse_pressure(isd_row.get('SLP', ''))
    surface_pressure = parse_pressure(isd_row.get('AL1', '')) or parse_pressure(isd_row.get('AL2', ''))
    
    # Precipitation fields
    precipitation = parse_precipitation(isd_row.get('AA1', ''))
    rain = parse_precipitation(isd_row.get('AA1', ''))  # AA1 is liquid precipitation
    snowfall = parse_snowfall(isd_row.get('AB1', ''))
    snow_depth = parse_snow_depth(isd_row.get('AB1', ''))
    
    # Wind fields
    wind_direction_10m, wind_speed_10m = parse_wind(isd_row.get('WND', ''))
    wind_gusts_10m = parse_wind_gust(isd_row.get('GA1', ''))
    
    # Cloud cover fields
    cloud_cover = parse_cloud_cover(isd_row.get('AI1', ''))
    cloud_cover_low = parse_cloud_cover(isd_row.get('AI1', ''))  # Use AI1 as low cloud
    
    # Weather code
    weather_code = parse_weather_code(isd_row.get('KE1', '') or isd_row.get('MW1', ''))
    
    # Build WeatherEvent dict
    # All unavailable fields set to None per schemas/README.md
    return {
        "station_id": station_id,
        "station_name": station_name,
        "station_region": station_region,
        "station_longitude": station_longitude,
        "station_latitude": station_latitude,
        "station_elevation": station_elevation,
        "station_timezone": station_timezone,
        "timestamp": timestamp.isoformat(),
        "temperature_2m": temperature_2m,
        "relative_humidity_2m": relative_humidity_2m,
        "dewpoint_2m": dewpoint_2m,
        "apparent_temperature": None,  # Not available from ISD
        "pressure_msl": pressure_msl,
        "surface_pressure": surface_pressure,
        "precipitation": precipitation,
        "rain": rain,
        "snowfall": snowfall,
        "cloud_cover": cloud_cover,
        "cloud_cover_low": cloud_cover_low,
        "cloud_cover_mid": None,  # Requires height analysis
        "cloud_cover_high": None,  # Requires height analysis
        "shortwave_radiation": None,  # Not available
        "direct_radiation": None,  # Not available
        "direct_normal_irradiance": None,  # Not available
        "diffuse_radiation": None,  # Not available
        "global_tilted_irradiance": None,  # Not available
        "sunshine_duration": None,  # Not available
        "wind_speed_10m": wind_speed_10m,
        "wind_speed_100m": None,  # Not available
        "wind_direction_10m": wind_direction_10m,
        "wind_direction_100m": None,  # Not available
        "wind_gusts_10m": wind_gusts_10m,
        "et0_fao_evapotranspiration": None,  # Not available
        "weather_code": weather_code,
        "snow_depth": snow_depth,
        "vapor_pressure_deficit": None,  # Not available
        "soil_temperature_0_to_7cm": None,  # Not available
        "soil_temperature_7_to_28cm": None,  # Not available
        "soil_temperature_28_to_100cm": None,  # Not available
        "soil_temperature_100_to_255cm": None,  # Not available
        "soil_moisture_0_to_7cm": None,  # Not available
        "soil_moisture_7_to_28cm": None,  # Not available
        "soil_moisture_28_to_100cm": None,  # Not available
        "soil_moisture_100_to_255cm": None,  # Not available
    }