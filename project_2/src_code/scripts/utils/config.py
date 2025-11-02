"""
Configuration Management
========================
Handles loading and parsing of configuration files.
"""

import yaml
import os
from typing import Any, Dict
import re
from pathlib import Path


class ConfigLoader:
    """Load and manage configuration."""

    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = None

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file and substitute environment variables.

        Returns:
            Configuration dictionary
        """
        # Load YAML file
        config_file = Path(self.config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Substitute environment variables
        config = self._substitute_env_vars(config)

        self.config = config
        return config

    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        Recursively substitute environment variables in configuration.

        Args:
            obj: Configuration object (dict, list, or str)

        Returns:
            Object with substituted values
        """
        if isinstance(obj, dict):
            return {key: self._substitute_env_vars(value) for key, value in obj.items()}

        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]

        elif isinstance(obj, str):
            # Find environment variable references: ${VAR_NAME}
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, obj)

            for var_name in matches:
                env_value = os.getenv(var_name, '')
                if not env_value:
                    # Log warning but don't fail
                    print(f"Warning: Environment variable {var_name} not set")

                obj = obj.replace(f'${{{var_name}}}', env_value)

            return obj

        else:
            return obj

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Dot-separated key path (e.g., 'model.name')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        if self.config is None:
            self.load()

        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def validate(self) -> bool:
        """
        Validate required configuration fields.

        Returns:
            True if valid, raises exception otherwise
        """
        if self.config is None:
            self.load()

        # Check required fields
        required_fields = [
            'data_source.s3_paths',
            'storage.s3.bucket',
            'storage.s3.region'
        ]

        for field in required_fields:
            value = self.get(field)
            if value is None:
                raise ValueError(f"Required configuration field missing: {field}")

        return True
