"""
Validation utilities for WhatsApp Sales Agent
Provides comprehensive validation for user inputs with natural language parsing
"""

import re
from typing import Optional, Tuple, Dict
import phonenumbers
from email_validator import validate_email as validate_email_format, EmailNotValidError


class ValidationResult:
    """Result of a validation operation"""
    def __init__(self, is_valid: bool, value: any = None, message: str = ""):
        self.is_valid = is_valid
        self.value = value
        self.message = message


def validate_phone_number(phone_input: str) -> ValidationResult:
    """
    Validate and format phone numbers (international format)
    
    Handles:
    - International format: +971 50 123 4567
    - UAE format: 050 123 4567
    - Various separators (spaces, dashes, dots)
    
    Args:
        phone_input: Raw phone number string from user
        
    Returns:
        ValidationResult with formatted phone number if valid
    """
    if not phone_input or len(phone_input.strip()) < 5:
        return ValidationResult(False, None, "Phone number too short")
    
    # Clean the input
    cleaned = re.sub(r'[^\d+]', '', phone_input.strip())
    
    # Check for obviously invalid patterns
    if re.match(r'^(\d)\1+$', cleaned.replace('+', '')):  # All same digits like 1111111
        return ValidationResult(False, None, "Invalid phone number pattern")
    
    try:
        # Try to parse with UAE as default region
        if not cleaned.startswith('+'):
            # Try adding UAE country code
            phone = phonenumbers.parse(cleaned, "AE")
        else:
            phone = phonenumbers.parse(cleaned, None)
        
        # Validate the number
        if phonenumbers.is_valid_number(phone):
            formatted = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
            return ValidationResult(True, formatted, "Valid phone number")
        else:
            return ValidationResult(False, None, "Invalid phone number")
            
    except phonenumbers.NumberParseException:
        return ValidationResult(False, None, "Could not parse phone number")


def validate_email(email_input: str) -> ValidationResult:
    """
    Validate email addresses
    
    Args:
        email_input: Raw email string from user
        
    Returns:
        ValidationResult with normalized email if valid
    """
    if not email_input or '@' not in email_input:
        return ValidationResult(False, None, "Invalid email format")
    
    try:
        # Validate and normalize
        validated = validate_email_format(email_input.strip(), check_deliverability=False)
        return ValidationResult(True, validated.normalized, "Valid email")
    except EmailNotValidError as e:
        return ValidationResult(False, None, str(e))


def validate_budget(budget_input: str) -> ValidationResult:
    """
    Parse and validate budget inputs with natural language support
    
    Handles formats like:
    - "500k" -> 500,000
    - "1.5M" -> 1,500,000
    - "2 million" -> 2,000,000
    - "AED 1,500,000" -> 1,500,000
    - "500000-1000000" -> (500000, 1000000) range
    
    Args:
        budget_input: Raw budget string from user
        
    Returns:
        ValidationResult with parsed budget value(s)
    """
    if not budget_input:
        return ValidationResult(False, None, "No budget provided")
    
    # Clean input
    text = budget_input.strip().upper()
    text = text.replace('AED', '').replace('DIRHAMS', '').replace('DHS', '')
    text = text.replace(',', '').strip()
    
    # Check for range (e.g., "500k-1M" or "500000-1000000")
    if '-' in text or 'TO' in text:
        separator = '-' if '-' in text else 'TO'
        parts = text.split(separator)
        if len(parts) == 2:
            min_result = validate_budget(parts[0].strip())
            max_result = validate_budget(parts[1].strip())
            if min_result.is_valid and max_result.is_valid:
                return ValidationResult(
                    True, 
                    {"min": min_result.value, "max": max_result.value, "type": "range"},
                    f"Budget range: {min_result.value:,} - {max_result.value:,} AED"
                )
    
    # Parse single value
    try:
        # Handle K (thousands)
        if 'K' in text:
            number = float(re.sub(r'[^\d.]', '', text.replace('K', '')))
            value = int(number * 1000)
        # Handle M (millions)
        elif 'M' in text:
            number = float(re.sub(r'[^\d.]', '', text.replace('M', '')))
            value = int(number * 1000000)
        # Handle "million" or "lakh"
        elif 'MILLION' in text:
            number = float(re.sub(r'[^\d.]', '', text.replace('MILLION', '')))
            value = int(number * 1000000)
        elif 'LAKH' in text:
            number = float(re.sub(r'[^\d.]', '', text.replace('LAKH', '')))
            value = int(number * 100000)
        # Plain number
        else:
            value = int(float(re.sub(r'[^\d.]', '', text)))
        
        # Validate reasonable range (10k to 1 billion AED)
        if value < 10000:
            return ValidationResult(False, None, "Budget seems too low")
        if value > 1000000000:
            return ValidationResult(False, None, "Budget seems too high")
        
        return ValidationResult(
            True, 
            {"value": value, "type": "fixed"},
            f"Budget: {value:,} AED"
        )
        
    except (ValueError, AttributeError):
        return ValidationResult(False, None, "Could not parse budget amount")


def validate_name(name_input: str) -> ValidationResult:
    """
    Validate person names
    
    Args:
        name_input: Raw name string from user
        
    Returns:
        ValidationResult with cleaned name if valid
    """
    if not name_input:
        return ValidationResult(False, None, "No name provided")
    
    cleaned = name_input.strip()
    
    # Check length
    if len(cleaned) < 2:
        return ValidationResult(False, None, "Name too short")
    if len(cleaned) > 100:
        return ValidationResult(False, None, "Name too long")
    
    # Check for excessive numbers (some numbers ok for names like "Mohammed 2")
    digit_count = sum(c.isdigit() for c in cleaned)
    if digit_count > 2:
        return ValidationResult(False, None, "Name contains too many numbers")
    
    # Check for valid characters (letters, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z\s\-'\.]+$", cleaned):
        return ValidationResult(False, None, "Name contains invalid characters")
    
    # Capitalize properly
    formatted_name = ' '.join(word.capitalize() for word in cleaned.split())
    
    return ValidationResult(True, formatted_name, "Valid name")


def extract_location(text: str) -> Optional[str]:
    """
    Extract Dubai location/area from user message
    
    Args:
        text: User message text
        
    Returns:
        Extracted location or None
    """
    # Common Dubai areas
    dubai_areas = [
        'Downtown Dubai', 'Dubai Marina', 'Palm Jumeirah', 'JBR', 'Jumeirah Beach Residence',
        'Business Bay', 'Dubai Hills', 'Arabian Ranches', 'Jumeirah Village Circle', 'JVC',
        'Dubai Sports City', 'Motor City', 'Studio City', 'Discovery Gardens', 'JLT',
        'Jumeirah Lakes Towers', 'DIFC', 'Dubai International Financial Centre',
        'Mirdif', 'Deira', 'Bur Dubai', 'Karama', 'Satwa', 'Al Barsha', 'Jumeirah',
        'Umm Suqeim', 'Al Quoz', 'Dubai Silicon Oasis', 'DSO', 'International City',
        'Dubai Creek Harbour', 'City Walk', 'Al Furjan', 'Damac Hills', 'Dubai South',
        'Town Square', 'Reem', 'Mira', 'Tilal Al Ghaf', 'Dubai Land'
    ]
    
    text_upper = text.upper()
    
    for area in dubai_areas:
        if area.upper() in text_upper:
            return area
    
    return None


def extract_property_type(text: str) -> Optional[str]:
    """
    Extract property type from user message
    
    Args:
        text: User message text
        
    Returns:
        Property type or None
    """
    text_lower = text.lower()
    
    property_types = {
        'apartment': ['apartment', 'flat', 'unit'],
        'villa': ['villa', 'townhouse', 'townhome'],
        'penthouse': ['penthouse', 'pent house'],
        'studio': ['studio'],
        'duplex': ['duplex'],
        'land': ['land', 'plot'],
        'commercial': ['commercial', 'office', 'shop', 'retail']
    }
    
    for prop_type, keywords in property_types.items():
        for keyword in keywords:
            if keyword in text_lower:
                return prop_type.capitalize()
    
    return None


def calculate_lead_score(lead_data: Dict) -> int:
    """
    Calculate lead score based on collected information
    
    Args:
        lead_data: Dictionary containing lead information
        
    Returns:
        Lead score (0-100)
    """
    score = 0
    
    # Name provided: +10
    if lead_data.get('name'):
        score += 10
    
    # Phone validated: +25
    if lead_data.get('phone'):
        score += 25
    
    # Email validated: +15
    if lead_data.get('email'):
        score += 15
    
    # Budget specified: +20
    if lead_data.get('budget'):
        score += 20
    
    # Location preference: +15
    if lead_data.get('location_preference'):
        score += 15
    
    # Property type specified: +15
    if lead_data.get('property_type'):
        score += 15
    
    return min(score, 100)
