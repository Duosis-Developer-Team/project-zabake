"""
Logging utility for Zabbix Monitoring Integration
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Text formatter for human-readable logging"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class Logger:
    """Logger manager class"""
    
    _loggers: dict = {}
    _initialized: bool = False
    
    @classmethod
    def initialize(
        cls,
        level: str = "INFO",
        log_file: Optional[str] = None,
        max_size: str = "10MB",
        backup_count: int = 5,
        format_type: str = "json",
        console_output: bool = True
    ):
        """
        Initialize logging system
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Log file path (None for no file logging)
            max_size: Maximum log file size (e.g., "10MB")
            backup_count: Number of backup files to keep
            format_type: Log format ("json" or "text")
            console_output: Enable console output
        """
        if cls._initialized:
            return
        
        # Parse log level
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Parse max size
        max_bytes = cls._parse_size(max_size)
        
        # Get formatter
        if format_type.lower() == "json":
            formatter = JSONFormatter()
        else:
            formatter = TextFormatter()
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get logger instance
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Logger instance
        """
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @staticmethod
    def _parse_size(size_str: str) -> int:
        """
        Parse size string to bytes
        
        Args:
            size_str: Size string (e.g., "10MB", "1GB")
            
        Returns:
            Size in bytes
        """
        size_str = size_str.upper().strip()
        
        if size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            # Assume bytes
            return int(size_str)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_size: str = "10MB",
    backup_count: int = 5,
    format_type: str = "json",
    console_output: bool = True
):
    """
    Setup logging system (convenience function)
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file path (None for no file logging)
        max_size: Maximum log file size (e.g., "10MB")
        backup_count: Number of backup files to keep
        format_type: Log format ("json" or "text")
        console_output: Enable console output
    """
    Logger.initialize(
        level=level,
        log_file=log_file,
        max_size=max_size,
        backup_count=backup_count,
        format_type=format_type,
        console_output=console_output
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance (convenience function)
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return Logger.get_logger(name)
