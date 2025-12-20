"""
JSON normalization utilities.

Handles normalization of JSON structures, particularly for PostgreSQL JSON columns
where numeric keys might be stored as strings but need to be accessed as integers.
"""
from typing import Dict, Any, Union


def normalize_json_int_keys(data: Union[Dict[str, Any], Dict[int, Any], None]) -> Dict[int, Any]:
    """
    Normalize JSON dict keys: convert numeric strings to int.
    
    This function handles the common issue where PostgreSQL JSON columns store
    numeric keys as strings (e.g., {"30": 1000}) but Python code expects integer
    keys (e.g., {30: 1000}).
    
    Args:
        data: Dictionary with potentially string or int keys, or None
        
    Returns:
        Dictionary with all numeric keys converted to int.
        If data is None, returns empty dict.
        If data is not a dict, returns empty dict (defensive).
        
    Examples:
        >>> normalize_json_int_keys({"30": 1000, "60": 2000})
        {30: 1000, 60: 2000}
        
        >>> normalize_json_int_keys({30: 1000, 60: 2000})
        {30: 1000, 60: 2000}
        
        >>> normalize_json_int_keys(None)
        {}
    """
    if not isinstance(data, dict):
        return {}
    
    normalized: Dict[int, Any] = {}
    for key, value in data.items():
        # Try to convert key to int if it's a numeric string
        if isinstance(key, int):
            # Already an int, use as is
            normalized[key] = value
        elif isinstance(key, str):
            # Try to convert string to int
            try:
                int_key = int(key)
                normalized[int_key] = value
            except (ValueError, TypeError):
                # If conversion fails, skip this key (non-numeric string keys are not expected)
                # Log warning in production, but for now we'll skip silently to avoid errors
                continue
        else:
            # Non-string, non-int key (unexpected), skip it
            continue
    
    return normalized









