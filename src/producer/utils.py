import json
import random
from config import NUMERIC_FIELDS

def get_corrupted_payload(row):
    """
    Applies real-world corruption scenarios to RANDOM fields
    """
    row = row.copy()
    raw_json = json.dumps(row)
    
    corruption_type = random.choice(['outlier', 'nulls'])

    if corruption_type == 'schema_mismatch':
        field_to_corrupt = random.choice(NUMERIC_FIELDS)
        
        if field_to_corrupt in row:
            row[field_to_corrupt] = "SENSOR_ERROR_CODE_505"
            return json.dumps(row), f"Schema Mismatch ({field_to_corrupt} became String)"

    elif corruption_type == 'outlier':
        field_to_corrupt = random.choice(NUMERIC_FIELDS)
        
        if field_to_corrupt in row:
            val = 999999.99 if random.random() > 0.5 else -999999.99
            row[field_to_corrupt] = val
            return json.dumps(row), f"Logical Outlier ({field_to_corrupt} = {val})"

    elif corruption_type == 'malformed_json':
        return raw_json[:-5], "Malformed JSON (Truncated)"
        
    elif corruption_type == 'nulls':
        valid_keys = [k for k in row.keys() if k != 'location_id']
        
        if valid_keys:
            key_to_null = random.choice(valid_keys)
            row[key_to_null] = None
            return json.dumps(row), f"Missing Field ({key_to_null})"

    return raw_json, "Normal"