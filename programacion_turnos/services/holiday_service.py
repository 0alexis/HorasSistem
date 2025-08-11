import holidays
from datetime import datetime, date
from django.core.cache import cache

def get_holidays_for_range(start_date, end_date, country='CO'):
    """
    Get holidays for a specific date range
    
    Args:
        start_date: datetime.date or string in YYYY-MM-DD format
        end_date: datetime.date or string in YYYY-MM-DD format
        country: ISO country code (default 'CO' for Colombia)
        
    Returns:
        Dictionary of holidays with dates as keys and names as values
    """
    # Convert string dates to date objects if needed
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Generate years needed for the range
    years = list(range(start_date.year, end_date.year + 1))
    
    # Create a cache key
    cache_key = f'holidays_{country}_{years[0]}'
    if len(years) > 1:
        cache_key += f'_{years[-1]}'
    
    # Try to get from cache first
    cached_holidays = cache.get(cache_key)
    if cached_holidays:
        return {k: v for k, v in cached_holidays.items() 
                if start_date <= k <= end_date}
    
    # If not in cache, fetch holidays
    country_holidays = holidays.CountryHoliday(country, years=years)
    
    # Cache the results (1 day expiration)
    cache.set(cache_key, country_holidays, 86400)
    
    # Filter to requested range and convert to strings
    result = {}
    for holiday_date, holiday_name in country_holidays.items():
        if start_date <= holiday_date <= end_date:
            result[holiday_date] = holiday_name
    
    return result

def is_holiday(check_date, country='CO'):
    """
    Check if a date is a holiday
    
    Args:
        check_date: datetime.date or string in YYYY-MM-DD format
        country: ISO country code (default 'CO' for Colombia)
        
    Returns:
        Boolean indicating if the date is a holiday
    """
    if isinstance(check_date, str):
        check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
    
    year = check_date.year
    cache_key = f'holidays_{country}_{year}'
    
    cached_holidays = cache.get(cache_key)
    if not cached_holidays:
        cached_holidays = holidays.CountryHoliday(country, years=year)
        cache.set(cache_key, cached_holidays, 86400)
    
    return check_date in cached_holidays

def get_holiday_name(check_date, country='CO'):
    """
    Get the name of a holiday
    
    Args:
        check_date: datetime.date or string in YYYY-MM-DD format
        country: ISO country code (default 'CO' for Colombia)
        
    Returns:
        Name of the holiday or None if not a holiday
    """
    if isinstance(check_date, str):
        check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
    
    year = check_date.year
    cache_key = f'holidays_{country}_{year}'
    
    cached_holidays = cache.get(cache_key)
    if not cached_holidays:
        cached_holidays = holidays.CountryHoliday(country, years=year)
        cache.set(cache_key, cached_holidays, 86400)
    
    return cached_holidays.get(check_date)