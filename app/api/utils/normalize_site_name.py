from typing import List
import re

def normalize_site_name(site_name: str) -> str:
    """
    Normalize the site name by removing domain suffixes and appending '.purpledove.net'.
    
    Args:
        site_name (str): The original site name from the frontend.
    
    Returns:
        str: The normalized site name with '.purpledove.net' appended.
    """
    # Remove any domain suffixes (e.g., .com, .com.ng, .org, etc.)
    site_name = re.sub(r'\.[a-z]{2,}(\.[a-z]{2,})?$', '', site_name, flags=re.IGNORECASE)
    
    # Append '.purpledove.net' to the site name
    normalized_site_name = f"{site_name}.erp.staging.purpledove.net"
    
    return normalized_site_name



def validate_site_name(normalized_site_name: str) -> bool:
    """
    Validate a site name according to common rules.
    
    Args:
        site_name (str): The site name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Basic validation rules
    if not normalized_site_name:
        return False
    
    # Check length (adjust min/max as needed)
    if len(normalized_site_name) < 3 or len(normalized_site_name) > 63:
        return False
    
    # Check for valid characters (letters, numbers, hyphens)
    import re
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', normalized_site_name.split('.')[0]):
        return False
    
    return True