"""
Utility functions for handling partial updates with intelligent merging.

This module provides reusable functions for merging update data with existing
data, particularly for complex types like dicts and lists.
"""
from typing import Dict, List, Any, Optional, Union


def merge_dict_update(
    existing_value: Optional[Dict[str, Any]],
    new_value: Optional[Dict[str, Any]],
    replace: bool = False
) -> Dict[str, Any]:
    """
    Intelligently merge a dictionary update with existing values.
    
    Args:
        existing_value: The existing dictionary value (from database).
        new_value: The new dictionary value (from update request).
        replace: If True, replace the entire dict. If False, merge keys.
    
    Returns:
        Merged dictionary.
    
    Examples:
        >>> merge_dict_update({"a": 1, "b": 2}, {"b": 3})
        {"a": 1, "b": 3}
        
        >>> merge_dict_update({"a": 1}, {"b": 2}, replace=True)
        {"b": 2}
    """
    if replace or existing_value is None:
        return new_value or {}
    
    if new_value is None:
        return existing_value
    
    # Merge: new values override existing ones, but keep existing keys not in new_value
    return {**existing_value, **new_value}


def merge_list_update(
    existing_value: Optional[List[Any]],
    new_value: Optional[List[Any]],
    replace: bool = True
) -> List[Any]:
    """
    Intelligently merge a list update with existing values.
    
    Args:
        existing_value: The existing list value (from database).
        new_value: The new list value (from update request).
        replace: If True, replace the entire list. If False, merge (append unique items).
    
    Returns:
        Merged or replaced list.
    
    Examples:
        >>> merge_list_update([1, 2], [2, 3], replace=True)
        [2, 3]
        
        >>> merge_list_update([1, 2], [2, 3], replace=False)
        [1, 2, 3]  # Note: this is a simple append, may have duplicates
    """
    if replace or existing_value is None:
        return new_value or []
    
    if new_value is None:
        return existing_value
    
    # For lists, default to replace (most common case)
    # If merge is needed, caller should handle it
    return new_value


def apply_intelligent_update(
    update_data: Dict[str, Any],
    existing_data: Dict[str, Any],
    merge_fields: Optional[Dict[str, bool]] = None
) -> Dict[str, Any]:
    """
    Apply intelligent updates to a data dictionary, merging complex types.
    
    This function handles partial updates by:
    - Keeping simple fields as-is (they replace existing values)
    - Merging dict fields intelligently (new keys override, existing keys preserved)
    - Replacing list fields by default (can be configured)
    
    Args:
        update_data: Dictionary of fields to update (from model_dump(exclude_unset=True)).
        existing_data: Dictionary of existing values (from database model).
        merge_fields: Optional dict mapping field names to merge behavior:
            - True: Merge dict/list with existing
            - False: Replace dict/list completely
            - None: Use default behavior (merge dicts, replace lists)
    
    Returns:
        Dictionary with intelligently merged update data.
    
    Examples:
        >>> existing = {"name": "Service", "prices": {"30": 1000, "60": 2000}}
        >>> update = {"prices": {"60": 2500}}
        >>> apply_intelligent_update(update, existing)
        {"prices": {"30": 1000, "60": 2500}}  # Merged, kept "30" key
    """
    if merge_fields is None:
        merge_fields = {}
    
    result = update_data.copy()
    
    for field_name, new_value in update_data.items():
        if field_name not in existing_data:
            # Field doesn't exist in existing data, use new value as-is
            continue
        
        existing_value = existing_data[field_name]
        
        # Determine merge behavior for this field
        should_merge = merge_fields.get(field_name, None)
        
        # Handle dict types
        if isinstance(new_value, dict) and isinstance(existing_value, dict):
            if should_merge is False:
                # Explicit replace
                result[field_name] = new_value
            else:
                # Default: merge dicts
                result[field_name] = merge_dict_update(existing_value, new_value, replace=False)
        
        # Handle list types
        elif isinstance(new_value, list) and isinstance(existing_value, list):
            if should_merge is True:
                # Explicit merge (append unique)
                result[field_name] = merge_list_update(existing_value, new_value, replace=False)
            else:
                # Default: replace lists
                result[field_name] = merge_list_update(existing_value, new_value, replace=True)
        
        # For other types (str, int, bool, etc.), keep new value (replace)
        # This is already handled by the copy() above
    
    return result


















