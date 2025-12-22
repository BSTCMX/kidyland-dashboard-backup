"""
DateTime helper utilities for timezone conversion and formatting.

Reusable functions for converting UTC datetimes to local timezones
and formatting dates/times for display.
"""
from datetime import datetime, date
from typing import Optional
from zoneinfo import ZoneInfo


def convert_utc_to_timezone(
    utc_datetime: Optional[datetime],
    timezone_str: str
) -> Optional[datetime]:
    """
    Convert a UTC datetime to a specific timezone.
    
    This function normalizes the input datetime to UTC first, then converts to the target timezone.
    If the datetime is naive (no timezone info), it assumes UTC.
    If the datetime is timezone-aware, it first converts to UTC, then to the target timezone.
    
    Args:
        utc_datetime: UTC datetime to convert (assumed UTC if timezone-naive)
        timezone_str: IANA timezone string (e.g., "America/Mexico_City")
        
    Returns:
        Datetime in the specified timezone, or None if input is None
        
    Raises:
        ValueError: If timezone_str is invalid
        
    Example:
        >>> from datetime import datetime, timezone
        >>> utc_time = datetime.now(timezone.utc)
        >>> local_time = convert_utc_to_timezone(utc_time, "America/Mexico_City")
    """
    if utc_datetime is None:
        return None
    
    try:
        target_timezone = ZoneInfo(timezone_str)
    except Exception as e:
        raise ValueError(f"Invalid timezone string: {timezone_str}") from e
    
    from datetime import timezone
    
    # Normalize to UTC first
    if utc_datetime.tzinfo is None:
        # If naive, assume UTC and make it timezone-aware
        # This handles cases where PostgreSQL returns naive datetimes
        # (though with our UTC connection config, they should be aware)
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    else:
        # If already timezone-aware, normalize to UTC first to ensure consistency
        # This handles cases where datetime might be in a different timezone
        utc_datetime = utc_datetime.astimezone(timezone.utc)
    
    # Convert from UTC to target timezone
    return utc_datetime.astimezone(target_timezone)


def format_datetime_local(
    utc_datetime: Optional[datetime],
    timezone_str: str,
    date_format: str = "%d/%m/%Y",
    time_format: str = "%H:%M:%S"
) -> tuple[str, str]:
    """
    Format a UTC datetime as local date and time strings.
    
    Args:
        utc_datetime: UTC datetime to format
        timezone_str: IANA timezone string
        date_format: Date format string (default: "%d/%m/%Y")
        time_format: Time format string (default: "%H:%M:%S")
        
    Returns:
        Tuple of (date_string, time_string), or ("N/A", "N/A") if input is None
        
    Example:
        >>> from datetime import datetime, timezone
        >>> utc_time = datetime.now(timezone.utc)
        >>> date_str, time_str = format_datetime_local(utc_time, "America/Mexico_City")
        >>> print(f"{date_str} {time_str}")
    """
    if utc_datetime is None:
        return ("N/A", "N/A")
    
    local_datetime = convert_utc_to_timezone(utc_datetime, timezone_str)
    if local_datetime is None:
        return ("N/A", "N/A")
    
    date_str = local_datetime.strftime(date_format)
    time_str = local_datetime.strftime(time_format)
    
    return (date_str, time_str)


def format_time_local(
    utc_datetime: Optional[datetime],
    timezone_str: str,
    time_format: str = "%H:%M"
) -> str:
    """
    Format a UTC datetime as local time string (hours:minutes).
    
    Args:
        utc_datetime: UTC datetime to format
        timezone_str: IANA timezone string
        time_format: Time format string (default: "%H:%M")
        
    Returns:
        Formatted time string, or "N/A" if input is None
        
    Example:
        >>> from datetime import datetime, timezone
        >>> utc_time = datetime.now(timezone.utc)
        >>> time_str = format_time_local(utc_time, "America/Mexico_City")
        >>> print(time_str)  # "14:30"
    """
    if utc_datetime is None:
        return "N/A"
    
    local_datetime = convert_utc_to_timezone(utc_datetime, timezone_str)
    if local_datetime is None:
        return "N/A"
    
    return local_datetime.strftime(time_format)


def get_business_date_in_timezone(
    utc_datetime: datetime,
    timezone_str: str
) -> date:
    """
    Get the business date (YYYY-MM-DD) for a UTC datetime in a specific timezone.
    
    This function converts a UTC datetime to the local timezone and returns
    the date portion. This is useful for determining which "business day"
    a transaction belongs to based on the sucursal's timezone.
    
    Args:
        utc_datetime: UTC datetime (should be timezone-aware)
        timezone_str: IANA timezone string (e.g., "America/Mexico_City")
        
    Returns:
        Date object representing the business date in the specified timezone
        
    Raises:
        ValueError: If timezone_str is invalid
        
    Example:
        >>> from datetime import datetime, timezone
        >>> utc_time = datetime(2025, 1, 15, 6, 0, 0, tzinfo=timezone.utc)
        >>> # In America/Mexico_City (UTC-6), 06:00 UTC = 00:00 local (same day)
        >>> business_date = get_business_date_in_timezone(utc_time, "America/Mexico_City")
        >>> print(business_date)  # 2025-01-15
    """
    local_datetime = convert_utc_to_timezone(utc_datetime, timezone_str)
    if local_datetime is None:
        raise ValueError(f"Could not convert datetime to timezone {timezone_str}")
    
    # Return just the date portion
    return local_datetime.date()


def create_local_midnight_datetime(
    date_obj: date,
    timezone_str: str
) -> datetime:
    """
    Create a timezone-aware datetime at midnight in a specific timezone, then convert to UTC.
    
    This function is useful for storing "date-only" fields (like scheduled_date) that need
    to be interpreted in a specific timezone context (e.g., sucursal timezone).
    
    The function:
    1. Creates a datetime at midnight (00:00:00) in the specified timezone
    2. Converts it to UTC for storage
    3. Returns the UTC datetime (timezone-aware)
    
    This ensures that when the date is later converted back to the local timezone for display,
    it will show the correct date without day shifts due to timezone conversion.
    
    Args:
        date_obj: Date object (date-only, no time component)
        timezone_str: IANA timezone string (e.g., "America/Mexico_City")
        
    Returns:
        Timezone-aware datetime in UTC representing midnight in the specified timezone
        
    Raises:
        ValueError: If timezone_str is invalid
        
    Example:
        >>> from datetime import date
        >>> scheduled_date = date(2025, 12, 21)
        >>> # Create datetime at midnight in Mexico City timezone, then convert to UTC
        >>> utc_datetime = create_local_midnight_datetime(scheduled_date, "America/Mexico_City")
        >>> # When converted back to Mexico City timezone, it will show 2025-12-21 00:00:00
        >>> # This avoids day shifts when displaying the date
    """
    try:
        target_timezone = ZoneInfo(timezone_str)
    except Exception as e:
        raise ValueError(f"Invalid timezone string: {timezone_str}") from e
    
    from datetime import time, timezone
    
    # Create datetime at midnight in the target timezone
    local_midnight = datetime.combine(date_obj, time.min)
    # Make it timezone-aware
    local_midnight = local_midnight.replace(tzinfo=target_timezone)
    
    # Convert to UTC for storage
    utc_datetime = local_midnight.astimezone(timezone.utc)
    
    return utc_datetime

