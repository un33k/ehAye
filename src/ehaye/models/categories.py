"""Model categorization and metadata."""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..core.logging import get_logger

logger = get_logger("models.categories")


@dataclass
class ModelInfo:
    """Information about a model."""
    id: str
    name: str
    category: str
    size_params: Optional[str] = None
    size_gb: Optional[float] = None
    quantization: Optional[str] = None
    description: Optional[str] = None
    emoji: str = "📦"
    
    @property
    def display_name(self) -> str:
        """Get display name with emoji and size."""
        size_str = f" ({self.size_params})" if self.size_params else ""
        return f"{self.emoji} {self.name.replace('-', ' ').replace('_', ' ')}{size_str}"


class ModelCategorizer:
    """Categorizes models based on size and type."""
    
    CATEGORY_EMOJIS = {
        "tiny": "🔵",
        "small": "🟢", 
        "medium": "🟡",
        "large": "🔴",
        "code": "💻",
        "instruct": "🎯",
        "chat": "💬",
        "unknown": "📦"
    }
    
    CATEGORY_DESCRIPTIONS = {
        "tiny": "Tiny Models (< 2B parameters)",
        "small": "Small Models (2B-3B parameters)",
        "medium": "Medium Models (3B-8B parameters)", 
        "large": "Large Models (> 8B parameters)",
        "code": "Code Models (specialized for programming)",
        "instruct": "Instruction-following Models",
        "chat": "Chat-optimized Models",
        "unknown": "Uncategorized Models"
    }
    
    SIZE_PATTERNS = [
        r'(\d+\.?\d*)[Bb]',  # Matches "1.5B", "7B", "8B", etc.
        r'(\d+\.?\d*)b',     # Matches "1.5b", "7b", etc.
    ]
    
    def extract_size_info(self, model_id: str) -> Tuple[Optional[str], Optional[float]]:
        """Extract parameter size from model ID."""
        for pattern in self.SIZE_PATTERNS:
            match = re.search(pattern, model_id, re.IGNORECASE)
            if match:
                size_str = match.group(1)
                try:
                    size_num = float(size_str)
                    return f"{size_str}B", size_num
                except ValueError:
                    continue
        
        return None, None
    
    def categorize_by_size(self, size_b: float) -> str:
        """Categorize model by parameter size."""
        if size_b < 2:
            return "tiny"
        elif size_b < 3:
            return "small" 
        elif size_b < 8:
            return "medium"
        else:
            return "large"
    
    def categorize_by_name(self, model_id: str) -> str:
        """Categorize model by name patterns."""
        model_lower = model_id.lower()
        
        # Code models
        if any(keyword in model_lower for keyword in [
            "code", "coder", "codellama", "starcoder", "deepseek-coder"
        ]):
            return "code"
        
        # Instruction models
        if any(keyword in model_lower for keyword in [
            "instruct", "instruction", "it"
        ]):
            return "instruct"
        
        # Chat models
        if any(keyword in model_lower for keyword in [
            "chat", "conversation", "dialogue"
        ]):
            return "chat"
        
        return "unknown"
    
    def categorize_model(self, model_id: str) -> ModelInfo:
        """Categorize a model and return ModelInfo."""
        # Extract basic info
        name = model_id.split("/")[-1] if "/" in model_id else model_id
        size_params, size_b = self.extract_size_info(model_id)
        
        # Determine primary category
        if size_b is not None:
            category = self.categorize_by_size(size_b)
        else:
            category = self.categorize_by_name(model_id)
        
        # Get emoji and description
        emoji = self.CATEGORY_EMOJIS.get(category, "📦")
        
        # Detect quantization
        quantization = None
        if "4bit" in model_id.lower():
            quantization = "4bit"
        elif "8bit" in model_id.lower():
            quantization = "8bit"
        elif "fp16" in model_id.lower():
            quantization = "fp16"
        
        # Estimate size in GB (rough approximation)
        size_gb = None
        if size_b is not None:
            if quantization == "4bit":
                size_gb = size_b * 0.5  # Rough estimate for 4-bit
            elif quantization == "8bit":
                size_gb = size_b * 1.0  # Rough estimate for 8-bit
            else:
                size_gb = size_b * 2.0  # Rough estimate for fp16
        
        return ModelInfo(
            id=model_id,
            name=name,
            category=category,
            size_params=size_params,
            size_gb=size_gb,
            quantization=quantization,
            emoji=emoji
        )
    
    def get_category_info(self, category: str) -> Dict[str, str]:
        """Get emoji and description for a category."""
        return {
            "emoji": self.CATEGORY_EMOJIS.get(category, "📦"),
            "description": self.CATEGORY_DESCRIPTIONS.get(category, category.title()),
            "name": category
        }
    
    def group_models_by_category(self, models: List[ModelInfo]) -> Dict[str, List[ModelInfo]]:
        """Group models by category."""
        grouped = {}
        for model in models:
            if model.category not in grouped:
                grouped[model.category] = []
            grouped[model.category].append(model)
        
        # Sort within each category by size (if available) then name
        for category in grouped:
            grouped[category].sort(key=lambda m: (
                m.size_gb or 0,
                m.name.lower()
            ))
        
        return grouped


# Global categorizer instance
model_categorizer = ModelCategorizer()


def categorize_model(model_id: str) -> ModelInfo:
    """Categorize a model ID."""
    return model_categorizer.categorize_model(model_id)


def group_models(models: List[str]) -> Dict[str, List[ModelInfo]]:
    """Group model IDs by category."""
    model_infos = [categorize_model(model_id) for model_id in models]
    return model_categorizer.group_models_by_category(model_infos)