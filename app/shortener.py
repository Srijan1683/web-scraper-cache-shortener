from __future__ import annotations

import hashlib
from config import DEFAULT_CODE_LENGTH

def generate_short_code(url:str, length:int = DEFAULT_CODE_LENGTH) -> str:
    if not url.strip():
        raise ValueError("URL cannot be empty")
    
    if length <=0:
        raise ValueError("Length must be greater than 0")
    
    hashed = hashlib.sha256(url.encode()).hexdigest()
    return hashed[:length]

def is_valid_short_code(code:str, length:int = DEFAULT_CODE_LENGTH) -> bool:
    return len(code) == length and code.isalnum()
