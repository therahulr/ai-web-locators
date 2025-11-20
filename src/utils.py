"""
Utility Module
Helper functions and utilities
"""

import logging
import re
from typing import Any, Optional
from pathlib import Path


def setup_logging(log_file: str, log_level: str = "INFO", max_bytes: int = 10485760, backup_count: int = 5) -> None:
    """
    Setup logging configuration

    Args:
        log_file: Log file path
        log_level: Logging level
        max_bytes: Max log file size
        backup_count: Number of backup files
    """
    from logging.handlers import RotatingFileHandler

    # Create logs directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)


def sanitize_filename(name: str) -> str:
    """
    Sanitize string for use as filename

    Args:
        name: Original name

    Returns:
        Sanitized filename
    """
    # Replace spaces and special chars with underscore
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    # Convert to lowercase
    sanitized = sanitized.lower()
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')

    return sanitized or 'unnamed'


def format_validation_result(result: dict) -> str:
    """
    Format validation result for display

    Args:
        result: Validation result dictionary

    Returns:
        Formatted string
    """
    status = "✓" if result.get('valid', False) else "✗"
    name = result.get('name', 'Unknown')
    count = result.get('count', 0)
    error = result.get('error', '')

    if result.get('valid'):
        return f"{status} {name} - Valid (1 element found)"
    else:
        return f"{status} {name} - Invalid: {error} (count: {count})"


def format_file_size(bytes_size: int) -> str:
    """
    Format file size in human-readable format

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def extract_page_name_from_url(url: str) -> str:
    """
    Extract meaningful page name from URL

    Args:
        url: Page URL

    Returns:
        Page name
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    path = parsed.path.strip('/')

    if not path:
        return parsed.netloc.replace('.', '_')

    # Get last segment of path
    segments = path.split('/')
    page_name = segments[-1]

    # Remove file extensions
    page_name = re.sub(r'\.(html|htm|php|aspx)$', '', page_name)

    # Sanitize
    page_name = sanitize_filename(page_name)

    return page_name or 'home'


def validate_config(config: dict) -> bool:
    """
    Validate configuration dictionary

    Args:
        config: Configuration dictionary

    Returns:
        True if valid, raises ValueError otherwise
    """
    required_keys = ['openai', 'browser', 'locator', 'output', 'logging']

    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config section: {key}")

    # Validate OpenAI config
    if 'model' not in config['openai']:
        raise ValueError("OpenAI model not specified in config")

    # Validate output directories
    for dir_key in ['locators_dir', 'docs_dir', 'sessions_dir']:
        if dir_key not in config['output']:
            raise ValueError(f"Missing output directory config: {dir_key}")

    return True


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def disable():
        """Disable colors"""
        Colors.HEADER = ''
        Colors.OKBLUE = ''
        Colors.OKCYAN = ''
        Colors.OKGREEN = ''
        Colors.WARNING = ''
        Colors.FAIL = ''
        Colors.ENDC = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''


def print_success(message: str) -> None:
    """Print success message in green"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    """Print error message in red"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message: str) -> None:
    """Print warning message in yellow"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_info(message: str) -> None:
    """Print info message in blue"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def print_header(message: str) -> None:
    """Print header message in bold"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{message}{Colors.ENDC}\n")
