#!/usr/bin/env python3
"""
Structured logging configuration for the BEDROT data pipeline.

Provides centralized logging setup with:
- Structured log formatting (JSON and human-readable)
- Log rotation with size and time-based policies
- Correlation IDs for request tracking
- Sensitive data filtering
- Performance metrics logging
"""

import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid
import re
from functools import wraps
import time

# Get project root
PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', Path(__file__).resolve().parents[2]))
LOG_DIR = PROJECT_ROOT / 'logs'
LOG_DIR.mkdir(exist_ok=True)


class SensitiveDataFilter(logging.Filter):
    """Filter to remove sensitive data from logs."""
    
    # Patterns for sensitive data
    SENSITIVE_PATTERNS = [
        (r'(password|pwd|passwd|pass)[\"\']?\s*[:=]\s*[\"\']?[^\s\"\']+', '***REDACTED***'),
        (r'(api_key|apikey|key)[\"\']?\s*[:=]\s*[\"\']?[^\s\"\']+', '***REDACTED***'),
        (r'(token|access_token|refresh_token)[\"\']?\s*[:=]\s*[\"\']?[^\s\"\']+', '***REDACTED***'),
        (r'(secret|client_secret)[\"\']?\s*[:=]\s*[\"\']?[^\s\"\']+', '***REDACTED***'),
        (r'(cookie|session)[\"\']?\s*[:=]\s*[\"\']?[^\s\"\']+', '***REDACTED***'),
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***EMAIL***'),
        (r'\b\d{3}-\d{2}-\d{4}\b', '***SSN***'),
        (r'\b\d{16}\b', '***CARD***'),
    ]
    
    def __init__(self):
        super().__init__()
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), replacement) 
            for pattern, replacement in self.SENSITIVE_PATTERNS
        ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter sensitive data from log records."""
        # Filter message
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            for pattern, replacement in self.compiled_patterns:
                msg = pattern.sub(replacement, msg)
            record.msg = msg
        
        # Filter arguments
        if hasattr(record, 'args') and record.args:
            filtered_args = []
            for arg in record.args:
                arg_str = str(arg)
                for pattern, replacement in self.compiled_patterns:
                    arg_str = pattern.sub(replacement, arg_str)
                filtered_args.append(arg_str)
            record.args = tuple(filtered_args)
        
        return True


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records for request tracking."""
    
    def __init__(self):
        super().__init__()
        self._correlation_id = None
    
    def set_correlation_id(self, correlation_id: Optional[str] = None):
        """Set correlation ID for current context."""
        self._correlation_id = correlation_id or str(uuid.uuid4())
    
    def clear_correlation_id(self):
        """Clear correlation ID."""
        self._correlation_id = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        record.correlation_id = self._correlation_id or '-'
        return True


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', '-'),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName', 
                          'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                          'pathname', 'process', 'processName', 'relativeCreated', 
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                          'correlation_id']:
                log_obj[key] = value
        
        return json.dumps(log_obj)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Get color for level
        color = self.COLORS.get(record.levelname, '')
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build formatted message
        correlation_id = getattr(record, 'correlation_id', '-')
        
        formatted = f"{color}{timestamp} [{record.levelname:8}]{self.RESET} "
        formatted += f"[{correlation_id[:8]}] "
        formatted += f"{record.name} - {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def setup_logging(
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = True,
    log_dir: Optional[Path] = None,
    service_name: Optional[str] = None
) -> Dict[str, logging.Logger]:
    """
    Set up structured logging for the pipeline.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Enable console logging
        enable_file: Enable file logging
        enable_json: Enable JSON structured logging
        log_dir: Directory for log files (defaults to PROJECT_ROOT/logs)
        service_name: Service name for log files
        
    Returns:
        Dictionary of configured loggers
    """
    # Use provided log dir or default
    log_dir = log_dir or LOG_DIR
    log_dir.mkdir(exist_ok=True)
    
    # Create filters
    sensitive_filter = SensitiveDataFilter()
    correlation_filter = CorrelationIdFilter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(ColoredFormatter())
        console_handler.addFilter(sensitive_filter)
        console_handler.addFilter(correlation_filter)
        root_logger.addHandler(console_handler)
    
    # File handlers
    if enable_file:
        # Service-specific log file
        service_name = service_name or "pipeline"
        
        # Regular log file with rotation
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_dir / f"{service_name}.log",
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(correlation_id)s] %(name)s - %(message)s'
        ))
        file_handler.addFilter(sensitive_filter)
        file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)
        
        # Error log file
        error_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / f"{service_name}_errors.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(correlation_id)s] %(name)s - %(message)s\n%(exc_info)s'
        ))
        error_handler.addFilter(sensitive_filter)
        error_handler.addFilter(correlation_filter)
        root_logger.addHandler(error_handler)
    
    # JSON structured log file
    if enable_json:
        json_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_dir / f"{service_name}_structured.jsonl",
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        json_handler.setLevel(getattr(logging, log_level.upper()))
        json_handler.setFormatter(StructuredFormatter())
        json_handler.addFilter(sensitive_filter)
        json_handler.addFilter(correlation_filter)
        root_logger.addHandler(json_handler)
    
    # Create service-specific loggers
    loggers = {
        'root': root_logger,
        'pipeline': logging.getLogger('pipeline'),
        'extractors': logging.getLogger('pipeline.extractors'),
        'cleaners': logging.getLogger('pipeline.cleaners'),
        'cookies': logging.getLogger('pipeline.cookies'),
        'health': logging.getLogger('pipeline.health'),
        'notifications': logging.getLogger('pipeline.notifications'),
    }
    
    # Store correlation filter for later use
    loggers['_correlation_filter'] = correlation_filter
    
    return loggers


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def with_correlation_id(correlation_id: Optional[str] = None):
    """Decorator to add correlation ID to function execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get correlation filter
            root_logger = logging.getLogger()
            correlation_filter = None
            
            for handler in root_logger.handlers:
                for filter in handler.filters:
                    if isinstance(filter, CorrelationIdFilter):
                        correlation_filter = filter
                        break
            
            if correlation_filter:
                # Set correlation ID
                correlation_filter.set_correlation_id(correlation_id)
                
                try:
                    return func(*args, **kwargs)
                finally:
                    # Clear correlation ID
                    correlation_filter.clear_correlation_id()
            else:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_performance(logger: Optional[logging.Logger] = None):
    """Decorator to log function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                logger.info(
                    f"Function {func.__name__} completed",
                    extra={
                        'function': func.__name__,
                        'duration_ms': round(elapsed * 1000, 2),
                        'status': 'success'
                    }
                )
                
                return result
                
            except Exception as e:
                elapsed = time.time() - start_time
                
                logger.error(
                    f"Function {func.__name__} failed",
                    extra={
                        'function': func.__name__,
                        'duration_ms': round(elapsed * 1000, 2),
                        'status': 'error',
                        'error': str(e)
                    },
                    exc_info=True
                )
                
                raise
        
        return wrapper
    return decorator


# Initialize default logging on import
DEFAULT_LOGGERS = setup_logging(
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    service_name='bedrot_pipeline'
)