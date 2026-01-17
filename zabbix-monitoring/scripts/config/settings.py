"""
Configuration settings loader for Zabbix Monitoring Integration
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigError(Exception):
    """Configuration error exception"""
    pass


class Settings:
    """Configuration settings manager"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize settings
        
        Args:
            config_dir: Configuration directory path (default: ./config)
        """
        # Load environment variables from .env if python-dotenv is available
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass  # python-dotenv not installed; use env vars and config files

        # Set config directory
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
        
        # Load configurations
        self.zabbix = self._load_zabbix_config()
        self.database = self._load_database_config()
        self.monitoring = self._load_monitoring_config()
        self.reporting = self._load_reporting_config()
        self.logging = self._load_logging_config()
        self.performance = self._load_performance_config()
    
    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """
        Load YAML configuration file
        
        Args:
            filename: Configuration file name
            
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigError: If file cannot be loaded
        """
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            # Try to load from environment or use defaults
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigError(f"Failed to load config file {filename}: {str(e)}")
    
    def _load_zabbix_config(self) -> Dict[str, Any]:
        """Load Zabbix API configuration"""
        config = self._load_yaml_file("zabbix_api_config.yml")
        
        # Override with environment variables if present
        return {
            "url": os.getenv("ZABBIX_URL", config.get("url", "")),
            "user": os.getenv("ZABBIX_USER", config.get("user", "")),
            "password": os.getenv("ZABBIX_PASSWORD", config.get("password", "")),
            "timeout": int(os.getenv("ZABBIX_TIMEOUT", config.get("timeout", 30))),
            "verify_ssl": os.getenv("ZABBIX_VERIFY_SSL", str(config.get("verify_ssl", True))).lower() == "true"
        }
    
    def _load_database_config(self) -> Dict[str, Any]:
        """Load database configuration"""
        config = self._load_yaml_file("db_config.yml")
        
        # Override with environment variables if present
        return {
            "host": os.getenv("DB_HOST", config.get("host", "")),
            "port": int(os.getenv("DB_PORT", config.get("port", 5432))),
            "name": os.getenv("DB_NAME", config.get("name", "")),
            "user": os.getenv("DB_USER", config.get("user", "")),
            "password": os.getenv("DB_PASSWORD", config.get("password", "")),
            "sslmode": os.getenv("DB_SSLMODE", config.get("sslmode", "prefer")),
            "pool_size": int(os.getenv("DB_POOL_SIZE", config.get("pool_size", 5))),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", config.get("max_overflow", 10)))
        }
    
    def _load_monitoring_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        config = self._load_yaml_file("monitoring_config.yml")
        
        # Default connectivity patterns
        default_patterns = [
            "icmpping",
            "icmppingsec",
            "net.tcp.service",
            "net.tcp.service.perf",
            "net.udp.service",
            "agent.ping"
        ]
        
        return {
            "data_source": os.getenv("MONITORING_DATA_SOURCE", config.get("data_source", "api")),
            "connectivity_patterns": config.get("connectivity_patterns", default_patterns),
            "analysis": {
                "max_data_age": int(os.getenv("MAX_DATA_AGE", config.get("analysis", {}).get("max_data_age", 3600))),
                "min_connectivity_score": float(os.getenv("MIN_CONNECTIVITY_SCORE", config.get("analysis", {}).get("min_connectivity_score", 0.8))),
                "inactive_threshold": int(os.getenv("INACTIVE_THRESHOLD", config.get("analysis", {}).get("inactive_threshold", 7200)))
            }
        }
    
    def _load_reporting_config(self) -> Dict[str, Any]:
        """Load reporting configuration"""
        config = self._load_yaml_file("reporting_config.yml")
        
        return {
            "output_formats": config.get("output_formats", ["json"]),
            "output_dir": os.getenv("OUTPUT_DIR", config.get("output_dir", "./reports")),
            "filename_pattern": config.get("filename_pattern", "zabbix_monitoring_{timestamp}.{format}"),
            "include_item_details": config.get("include_item_details", True),
            "include_host_details": config.get("include_host_details", True)
        }
    
    def _load_logging_config(self) -> Dict[str, Any]:
        """Load logging configuration"""
        config = self._load_yaml_file("logging_config.yml")
        
        return {
            "level": os.getenv("LOG_LEVEL", config.get("level", "INFO")),
            "file": os.getenv("LOG_FILE", config.get("file", "./logs/zabbix_monitoring.log")),
            "max_size": config.get("max_size", "10MB"),
            "backup_count": config.get("backup_count", 5),
            "format": config.get("format", "json")
        }
    
    def _load_performance_config(self) -> Dict[str, Any]:
        """Load performance configuration"""
        config = self._load_yaml_file("performance_config.yml")
        
        return {
            "api_batch_size": int(os.getenv("API_BATCH_SIZE", config.get("api_batch_size", 100))),
            "db_batch_size": int(os.getenv("DB_BATCH_SIZE", config.get("db_batch_size", 1000))),
            "max_workers": int(os.getenv("MAX_WORKERS", config.get("max_workers", 5))),
            "enable_cache": os.getenv("ENABLE_CACHE", str(config.get("enable_cache", True))).lower() == "true",
            "cache_ttl": int(os.getenv("CACHE_TTL", config.get("cache_ttl", 300)))
        }
    
    def validate(self) -> bool:
        """
        Validate configuration
        
        Returns:
            True if valid
            
        Raises:
            ConfigError: If configuration is invalid
        """
        errors = []
        
        # Validate Zabbix config
        if self.monitoring["data_source"] == "api":
            if not self.zabbix["url"]:
                errors.append("Zabbix URL is required when using API data source")
            if not self.zabbix["user"]:
                errors.append("Zabbix user is required when using API data source")
            if not self.zabbix["password"]:
                errors.append("Zabbix password is required when using API data source")
        
        # Validate Database config
        if self.monitoring["data_source"] == "database":
            if not self.database["host"]:
                errors.append("Database host is required when using database data source")
            if not self.database["name"]:
                errors.append("Database name is required when using database data source")
            if not self.database["user"]:
                errors.append("Database user is required when using database data source")
        
        if errors:
            raise ConfigError("Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors))
        
        return True
    
    def get_zabbix_url(self) -> str:
        """Get Zabbix API URL"""
        return self.zabbix["url"]
    
    def get_zabbix_credentials(self) -> tuple:
        """Get Zabbix credentials (user, password)"""
        return (self.zabbix["user"], self.zabbix["password"])
    
    def get_database_connection_string(self) -> str:
        """Get database connection string"""
        return (
            f"postgresql://{self.database['user']}:{self.database['password']}"
            f"@{self.database['host']}:{self.database['port']}/{self.database['name']}"
            f"?sslmode={self.database['sslmode']}"
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(config_dir: Optional[str] = None) -> Settings:
    """
    Get global settings instance (singleton pattern)
    
    Args:
        config_dir: Configuration directory path
        
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings(config_dir)
        _settings.validate()
    return _settings
