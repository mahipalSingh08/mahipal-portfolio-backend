# pyrefly: ignore [missing-import]
from better_profanity import Profanity

# Extended bad words list including common Hindi profanity
# These are patterns/variations that may not be caught by the default English list
CUSTOM_BAD_WORDS = [
    # Hindi profanity - common variants
    "maderchod",
    "mader chod",
    "maderchod",
    "mader chod",
    "madarchod",
    "madar chod",
    "madarchod",
    "madar chod",
    "bhenchod",
    "bhen chod",
    "behenchod",
    "behen chod",
    "bhosdika",
    "bhosdike",
    "bhosdi ke",
    "bhosri",
    "bhosda",
    "bhosad",
    "chutiya",
    "chutiye",
    "chut",
    "choot",
    "chutmarika",
    "ghanta",
    "gaand",
    "gaandu",
    "gandu",
    "gand mara",
    "gand marao",
    "gandu",
    "harami",
    "haramkhor",
    "hijra",
    "kamine",
    "kameena",
    "kaminay",
    "khota",
    "kutta",
    "kuuta",
    "kutti",
    "kuttiya",
    "kutte",
    "lauda",
    "launda",
    "land",
    "loda",
    "lodu",
    "lora",
    "lori",
    "lun",
    "moot",
    "muth",
    "mutthal",
    "najayaz",
    "nalla",
    "nala",
    "pissing",
    "randi",
    "randwa",
    "saala",
    "sala",
    "saali",
    "sali",
    "saala kutta",
    "suar",
    "suwar",
    "tatti",
    "ullu",
    "ullu ka pattha",
]

# Initialize the profanity filter once (singleton)
_profanity = Profanity()

# Extend the default English word list with custom Hindi bad words
_profanity.add_censor_words(CUSTOM_BAD_WORDS)


def contains_profanity(text: str) -> bool:
    """Check if the given text contains profanity."""
    return _profanity.contains_profanity(text)


def censor_profanity(text: str, censor_char: str = "*") -> str:
    """Censor profanity in the given text, replacing with the specified character."""
    return _profanity.censor(text, censor_char)


def _normalize_text(text: str) -> str:
    """Remove separators between characters to catch bypass attempts like 'k u t t a', 'k_u_tt-a', etc."""
    # Remove common separator characters used to bypass filters
    for char in [" ", "\t", "_", "-", ".", ",", "|", "/", "\\", "+", "=", "~", "`", "@", "#", "$", "%", "^", "&", "*"]:
        text = text.replace(char, "")
    return text


def validate_profanity(text: str, field_name: str) -> str | None:
    """
    Validate text for profanity. Returns an error message if profanity is found, else None.
    
    Args:
        text: The text to validate
        field_name: The name of the field being validated (for error messages)
    
    Returns:
        Error message string if profanity detected, otherwise None
    """
    if not text:
        return None
    
    # Check each word individually to avoid false positives on compound words
    words = text.split()
    for word in words:
        # Clean word - remove common punctuation for checking
        clean_word = word.strip(".,!?;:'\"()[]{}").lower()
        if clean_word and contains_profanity(clean_word):
            return f"{field_name.capitalize()} contains inappropriate language. Please remove offensive words."

    # Also check the full text to catch multi-word phrases
    if contains_profanity(text.lower()):
        return f"{field_name.capitalize()} contains inappropriate language. Please remove offensive words."
    
    # Anti-bypass: check normalized version (spaces removed)
    # Catches attempts like "k u t t a" or "k  u  t  t  a"
    normalized = _normalize_text(text.lower())
    original_lower = text.lower()
    if normalized != original_lower:
        # Only check if there were actually spaces/tabs removed from original
        if contains_profanity(normalized):
            return f"{field_name.capitalize()} contains inappropriate language. Please remove offensive words."
    
    return None
