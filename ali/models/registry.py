"""Model registry and search functionality."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..core.config import get_config
from ..core.exceptions import ModelError
from ..core.logging import get_logger
from .categories import ModelInfo, categorize_model

logger = get_logger("models.registry")


class ModelRegistry:
    """Manages model registration and search."""
    
    def __init__(self):
        self.config = get_config()
        self._installed_cache: Optional[List[ModelInfo]] = None
    
    def get_model_list_file(self, category: str) -> Path:
        """Get path to model list file for category."""
        return self.config.paths.models_dir / category / ".model_list"
    
    def read_installed_models(self, category: str) -> List[str]:
        """Read installed models from category file."""
        model_file = self.get_model_list_file(category)
        
        if not model_file.exists() or model_file.stat().st_size == 0:
            return []
        
        models = []
        try:
            with open(model_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("model_id:"):
                        model_id = line.replace("model_id:", "").strip()
                        if model_id:
                            models.append(model_id)
        except Exception as e:
            logger.error(f"Error reading {model_file}: {e}")
        
        return models
    
    def write_model_to_category(self, model_id: str, category: str) -> None:
        """Write model ID to category file."""
        model_file = self.get_model_list_file(category)
        model_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if already exists
        existing = self.read_installed_models(category)
        if model_id in existing:
            logger.debug(f"Model {model_id} already in {category}")
            return
        
        try:
            with open(model_file, 'a') as f:
                f.write(f"model_id:{model_id}\n")
            logger.info(f"Added {model_id} to {category}")
        except Exception as e:
            raise ModelError(f"Failed to write model to registry: {e}")
    
    def remove_model_from_category(self, model_id: str, category: str) -> bool:
        """Remove model ID from category file."""
        model_file = self.get_model_list_file(category)
        
        if not model_file.exists():
            return False
        
        try:
            models = self.read_installed_models(category)
            if model_id not in models:
                return False
            
            models.remove(model_id)
            
            # Rewrite file
            with open(model_file, 'w') as f:
                for model in models:
                    f.write(f"model_id:{model}\n")
            
            logger.info(f"Removed {model_id} from {category}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing model from registry: {e}")
            return False
    
    def get_all_installed(self, refresh: bool = False) -> List[ModelInfo]:
        """Get all installed models across categories."""
        if self._installed_cache and not refresh:
            return self._installed_cache
        
        all_models = []
        
        for category in self.config.models.categories:
            model_ids = self.read_installed_models(category)
            for model_id in model_ids:
                model_info = categorize_model(model_id)
                # Override category with file-based category if different
                if model_info.category != category:
                    model_info.category = category
                all_models.append(model_info)
        
        # Sort by category, then size, then name
        all_models.sort(key=lambda m: (
            self.config.models.categories.index(m.category) 
            if m.category in self.config.models.categories else 999,
            m.size_gb or 0,
            m.name.lower()
        ))
        
        self._installed_cache = all_models
        return all_models
    
    def register_model(self, model_id: str, category: Optional[str] = None) -> ModelInfo:
        """Register a newly installed model."""
        model_info = categorize_model(model_id)
        
        # Use provided category or auto-categorized
        target_category = category or model_info.category
        
        # Ensure category is valid
        if target_category not in self.config.models.categories:
            logger.warning(f"Unknown category {target_category}, using 'medium'")
            target_category = "medium"
        
        self.write_model_to_category(model_id, target_category)
        
        # Update cached category
        model_info.category = target_category
        
        # Clear cache
        self._installed_cache = None
        
        return model_info
    
    def unregister_model(self, model_id: str) -> bool:
        """Unregister a model from all categories."""
        removed = False
        
        for category in self.config.models.categories:
            if self.remove_model_from_category(model_id, category):
                removed = True
        
        if removed:
            self._installed_cache = None
        
        return removed
    
    def find_model(self, model_id: str) -> Optional[ModelInfo]:
        """Find a specific model by ID."""
        installed = self.get_all_installed()
        
        for model in installed:
            if model.id == model_id:
                return model
        
        return None
    
    def search_installed(
        self, 
        query: Optional[str] = None,
        category: Optional[str] = None,
        size_filter: Optional[str] = None
    ) -> List[ModelInfo]:
        """Search installed models."""
        models = self.get_all_installed()
        
        # Filter by category
        if category and category in self.config.models.categories:
            models = [m for m in models if m.category == category]
        
        # Filter by query
        if query:
            query_lower = query.lower()
            models = [
                m for m in models 
                if query_lower in m.id.lower() or query_lower in m.name.lower()
            ]
        
        # Filter by size
        if size_filter:
            size_filter_lower = size_filter.lower()
            models = [
                m for m in models
                if (m.size_params and size_filter_lower in m.size_params.lower()) or
                   size_filter_lower in m.id.lower()
            ]
        
        return models
    
    def get_category_stats(self) -> Dict[str, int]:
        """Get count of models per category."""
        stats = {category: 0 for category in self.config.models.categories}
        
        for model in self.get_all_installed():
            if model.category in stats:
                stats[model.category] += 1
            else:
                stats["unknown"] = stats.get("unknown", 0) + 1
        
        return stats
    
    def cleanup_empty_categories(self) -> None:
        """Remove empty model list files."""
        for category in self.config.models.categories:
            model_file = self.get_model_list_file(category)
            
            if model_file.exists():
                models = self.read_installed_models(category)
                if not models:
                    try:
                        model_file.unlink()
                        logger.debug(f"Removed empty category file: {category}")
                    except Exception as e:
                        logger.error(f"Error removing empty file: {e}")


# Global registry instance
model_registry = ModelRegistry()


def get_installed_models() -> List[ModelInfo]:
    """Get all installed models."""
    return model_registry.get_all_installed()


def register_model(model_id: str, category: Optional[str] = None) -> ModelInfo:
    """Register a newly installed model."""
    return model_registry.register_model(model_id, category)


def find_model(model_id: str) -> Optional[ModelInfo]:
    """Find a specific model by ID."""
    return model_registry.find_model(model_id)


def search_models(
    query: Optional[str] = None,
    category: Optional[str] = None,
    size_filter: Optional[str] = None
) -> List[ModelInfo]:
    """Search installed models."""
    return model_registry.search_installed(query, category, size_filter)