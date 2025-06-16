"""Configuration file loading utilities."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        raise ImportError("tomli is required for Python < 3.11. Install with: pip install tomli")

from ..exceptions import ConfigurationError
from ..logging import get_logger

logger = get_logger("config.loader")


class ConfigLoader:
    """Handles loading configuration from various sources."""
    
    @staticmethod
    def load_toml(config_file: Path) -> Dict[str, Any]:
        """Load configuration from TOML file."""
        if not config_file.exists():
            raise ConfigurationError(f"Config file not found: {config_file}")
        
        try:
            with open(config_file, 'rb') as f:
                return tomllib.load(f)
        except Exception as e:
            raise ConfigurationError(f"Failed to parse TOML config: {e}")
    
    @staticmethod
    def save_toml(config_data: Dict[str, Any], config_file: Path) -> None:
        """Save configuration to TOML file."""
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            import toml
            with open(config_file, 'w') as f:
                toml.dump(config_data, f)
            logger.debug(f"Saved configuration to {config_file}")
        except ImportError:
            raise ConfigurationError("toml package not available for saving config")
        except Exception as e:
            raise ConfigurationError(f"Failed to save config: {e}")
    
    @staticmethod
    def find_config_file(
        filename: str = "settings.toml",
        search_paths: Optional[list[Path]] = None
    ) -> Optional[Path]:
        """Find configuration file in standard locations."""
        if search_paths is None:
            search_paths = [
                Path.cwd() / "config",
                Path.home() / ".config" / "ehaye",
                Path.cwd(),
            ]
        
        for search_path in search_paths:
            config_file = search_path / filename
            if config_file.exists():
                logger.debug(f"Found config file: {config_file}")
                return config_file
        
        return None