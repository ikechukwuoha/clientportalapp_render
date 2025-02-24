from typing import List

from typing import List
import re

def normalize_site_name(site_name: str, target_domain: str = ".purpledove.net") -> str:
    """
    Normalize a site name by removing any existing domain/TLD and ensuring it ends with the target domain.
    
    Args:
        site_name (str): The original site name to process
        target_domain (str): The domain suffix to ensure (default: .purpledove.net)
        
    Returns:
        str: Normalized site name with correct domain suffix
    """
    # Convert to lowercase and strip whitespace
    site_name = site_name.lower().strip()
    
    # First, check if the target domain is already at the end
    if site_name.endswith(target_domain):
        return site_name
    
    # Extract just the first part of the domain (before any dot)
    # This handles both standard and non-standard TLDs
    base_name = re.sub(r'\..*$', '', site_name)
    
    # If the regex didn't match (no dots), use the original site_name
    if base_name == "":
        base_name = site_name
    
    # Ensure site name ends with target domain
    normalized_name = f"{base_name}{target_domain}"
    
    return normalized_name



def validate_site_name(site_name: str) -> bool:
    """
    Validate a site name according to common rules.
    
    Args:
        site_name (str): The site name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Basic validation rules
    if not site_name:
        return False
    
    # Check length (adjust min/max as needed)
    if len(site_name) < 3 or len(site_name) > 63:
        return False
    
    # Check for valid characters (letters, numbers, hyphens)
    import re
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', site_name.split('.')[0]):
        return False
    
    return True