"""Path management utilities."""

from pathlib import Path
from typing import List, Optional

from ..logging import get_logger

logger = get_logger("config.paths")


class PathManager:
    """Manages application paths and directories."""
    
    def __init__(self, base_cache_dir: Optional[Path] = None, base_config_dir: Optional[Path] = None):
        self.base_cache_dir = base_cache_dir or Path.home() / ".cache" / "ehaye"
        self.base_config_dir = base_config_dir or Path.home() / ".config" / "ehaye"
    
    @property
    def cache_dir(self) -> Path:
        """Get cache directory."""
        return self.base_cache_dir
    
    @property 
    def models_dir(self) -> Path:
        """Get models directory."""
        return self.base_cache_dir / "models"
    
    @property
    def logs_dir(self) -> Path:
        """Get logs directory."""
        return self.base_cache_dir / "logs"
    
    @property
    def config_dir(self) -> Path:
        """Get config directory."""
        return self.base_config_dir
    
    def get_model_category_dir(self, category: str) -> Path:
        """Get directory for specific model category."""
        return self.models_dir / category
    
    def get_log_file(self, name: str) -> Path:
        """Get path for log file."""
        return self.logs_dir / f"{name}.log"
    
    def create_directories(self, categories: Optional[List[str]] = None) -> None:
        """Create all necessary directories."""
        directories = [
            self.cache_dir,
            self.models_dir,
            self.logs_dir,
            self.config_dir,
        ]
        
        # Add model category directories
        if categories:
            for category in categories:
                directories.append(self.get_model_category_dir(category))
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    def cleanup_empty_directories(self) -> None:
        """Remove empty directories."""
        for directory in [self.models_dir, self.logs_dir]:
            if directory.exists():
                try:
                    # Remove empty subdirectories
                    for subdir in directory.iterdir():
                        if subdir.is_dir() and not any(subdir.iterdir()):
                            subdir.rmdir()
                            logger.debug(f"Removed empty directory: {subdir}")
                except OSError as e:
                    logger.warning(f"Failed to cleanup directory {directory}: {e}")
    
    def get_size_info(self) -> dict:
        """Get size information for all directories."""
        def get_dir_size(directory: Path) -> int:
            """Get total size of directory in bytes."""
            if not directory.exists():
                return 0
            
            total_size = 0
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except OSError:
                        pass
            return total_size
        
        return {
            "cache_dir": get_dir_size(self.cache_dir),
            "models_dir": get_dir_size(self.models_dir),
            "logs_dir": get_dir_size(self.logs_dir),
            "config_dir": get_dir_size(self.config_dir),
        }