"""Validation utilities for various data types."""

import os
import re
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

from ..exceptions import ValidationError
from ..logging import get_logger

logger = get_logger("utilities.validators")


def validate_model_name(name: str) -> bool:
    """Validate model name format."""
    if not name or not isinstance(name, str):
        raise ValidationError("Model name must be a non-empty string")
    
    # Basic format: alphanumeric, hyphens, underscores, colons (for tags), dots (for versions)
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._:-]*$'
    if not re.match(pattern, name):
        raise ValidationError(
            f"Invalid model name '{name}'. Must contain only alphanumeric characters, "
            "hyphens, underscores, colons, and dots"
        )
    
    # Check length
    if len(name) > 100:
        raise ValidationError(f"Model name too long: {len(name)} characters (max 100)")
    
    if len(name) < 1:
        raise ValidationError("Model name cannot be empty")
    
    return True


def validate_path(
    path: Union[str, Path],
    must_exist: bool = False,
    must_be_file: bool = False,
    must_be_dir: bool = False,
    must_be_writable: bool = False,
    create_if_missing: bool = False
) -> Path:
    """Validate and normalize a path."""
    if not path:
        raise ValidationError("Path cannot be empty")
    
    path_obj = Path(path).expanduser().resolve()
    
    # Check existence
    if must_exist and not path_obj.exists():
        raise ValidationError(f"Path does not exist: {path_obj}")
    
    if path_obj.exists():
        # Check type constraints
        if must_be_file and not path_obj.is_file():
            raise ValidationError(f"Path is not a file: {path_obj}")
        
        if must_be_dir and not path_obj.is_dir():
            raise ValidationError(f"Path is not a directory: {path_obj}")
        
        # Check writability
        if must_be_writable and not os.access(path_obj, os.W_OK):
            raise ValidationError(f"Path is not writable: {path_obj}")
    
    elif create_if_missing:
        try:
            if must_be_dir or (not must_be_file and str(path).endswith('/')):
                path_obj.mkdir(parents=True, exist_ok=True)
            else:
                path_obj.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValidationError(f"Cannot create path {path_obj}: {e}")
    
    return path_obj


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
    """Validate URL format."""
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")
    
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {e}")
    
    if not parsed.scheme:
        raise ValidationError("URL must include a scheme (http://, https://, etc.)")
    
    if not parsed.netloc:
        raise ValidationError("URL must include a domain name")
    
    if allowed_schemes and parsed.scheme not in allowed_schemes:
        raise ValidationError(
            f"URL scheme '{parsed.scheme}' not allowed. "
            f"Allowed schemes: {', '.join(allowed_schemes)}"
        )
    
    return True


def validate_file_exists(file_path: Union[str, Path]) -> Path:
    """Validate that a file exists and is readable."""
    return validate_path(
        file_path,
        must_exist=True,
        must_be_file=True
    )


def validate_directory_writable(dir_path: Union[str, Path]) -> Path:
    """Validate that a directory exists and is writable."""
    return validate_path(
        dir_path,
        must_exist=True,
        must_be_dir=True,
        must_be_writable=True
    )


def validate_port(port: Union[int, str]) -> int:
    """Validate port number."""
    try:
        port_int = int(port)
    except (ValueError, TypeError):
        raise ValidationError(f"Port must be a number, got: {port}")
    
    if not (1 <= port_int <= 65535):
        raise ValidationError(f"Port must be between 1 and 65535, got: {port_int}")
    
    return port_int


def validate_positive_number(
    value: Union[int, float, str],
    name: str = "value",
    allow_zero: bool = False
) -> Union[int, float]:
    """Validate positive number."""
    try:
        if isinstance(value, str):
            # Try int first, then float
            try:
                num_value = int(value)
            except ValueError:
                num_value = float(value)
        else:
            num_value = value
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be a number, got: {value}")
    
    if allow_zero:
        if num_value < 0:
            raise ValidationError(f"{name} must be non-negative, got: {num_value}")
    else:
        if num_value <= 0:
            raise ValidationError(f"{name} must be positive, got: {num_value}")
    
    return num_value


def validate_percentage(value: Union[int, float, str], name: str = "percentage") -> float:
    """Validate percentage value (0-100)."""
    num_value = validate_positive_number(value, name, allow_zero=True)
    
    if num_value > 100:
        raise ValidationError(f"{name} cannot exceed 100%, got: {num_value}")
    
    return float(num_value)


def validate_choice(
    value: str,
    choices: List[str],
    name: str = "value",
    case_sensitive: bool = True
) -> str:
    """Validate that value is one of the allowed choices."""
    if not case_sensitive:
        value = value.lower()
        choices = [choice.lower() for choice in choices]
    
    if value not in choices:
        raise ValidationError(
            f"Invalid {name}: '{value}'. "
            f"Must be one of: {', '.join(choices)}"
        )
    
    return value


def validate_email(email: str) -> bool:
    """Validate email format (basic validation)."""
    if not email or not isinstance(email, str):
        raise ValidationError("Email must be a non-empty string")
    
    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email format: {email}")
    
    return True


def validate_version(version: str) -> bool:
    """Validate semantic version format."""
    if not version or not isinstance(version, str):
        raise ValidationError("Version must be a non-empty string")
    
    # Semantic version pattern (basic)
    pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$'
    if not re.match(pattern, version):
        raise ValidationError(
            f"Invalid version format: {version}. "
            "Expected format: MAJOR.MINOR.PATCH[-prerelease][+build]"
        )
    
    return True


def validate_hostname(hostname: str) -> bool:
    """Validate hostname format."""
    if not hostname or not isinstance(hostname, str):
        raise ValidationError("Hostname must be a non-empty string")
    
    # Basic hostname pattern
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?$'
    if not re.match(pattern, hostname):
        raise ValidationError(f"Invalid hostname format: {hostname}")
    
    if len(hostname) > 253:
        raise ValidationError(f"Hostname too long: {len(hostname)} characters (max 253)")
    
    # Check individual labels
    labels = hostname.split('.')
    for label in labels:
        if len(label) > 63:
            raise ValidationError(f"Hostname label too long: {label} (max 63 characters)")
        if label.startswith('-') or label.endswith('-'):
            raise ValidationError(f"Hostname label cannot start or end with hyphen: {label}")
    
    return True


def validate_json_string(json_str: str) -> bool:
    """Validate JSON string format."""
    if not json_str or not isinstance(json_str, str):
        raise ValidationError("JSON must be a non-empty string")
    
    try:
        import json
        json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {e}")
    
    return True


def validate_regex_pattern(pattern: str) -> bool:
    """Validate regular expression pattern."""
    if not pattern or not isinstance(pattern, str):
        raise ValidationError("Regex pattern must be a non-empty string")
    
    try:
        re.compile(pattern)
    except re.error as e:
        raise ValidationError(f"Invalid regex pattern: {e}")
    
    return True


def validate_file_size(
    file_path: Union[str, Path],
    max_size_mb: Optional[float] = None,
    min_size_mb: Optional[float] = None
) -> int:
    """Validate file size constraints."""
    path_obj = validate_file_exists(file_path)
    
    try:
        size_bytes = path_obj.stat().st_size
    except OSError as e:
        raise ValidationError(f"Cannot get file size for {path_obj}: {e}")
    
    size_mb = size_bytes / (1024 * 1024)
    
    if max_size_mb is not None and size_mb > max_size_mb:
        raise ValidationError(
            f"File too large: {size_mb:.1f}MB (max {max_size_mb}MB)"
        )
    
    if min_size_mb is not None and size_mb < min_size_mb:
        raise ValidationError(
            f"File too small: {size_mb:.1f}MB (min {min_size_mb}MB)"
        )
    
    return size_bytes