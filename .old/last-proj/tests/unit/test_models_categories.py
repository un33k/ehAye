"""Tests for model categorization module."""

import pytest

from ehaye.models.categories import ModelCategorizer, ModelInfo, categorize_model, group_models


class TestModelCategorizer:
    """Test the model categorizer."""
    
    def test_extract_size_info(self):
        """Test size extraction from model IDs."""
        categorizer = ModelCategorizer()
        
        # Test various size patterns
        assert categorizer.extract_size_info("model-7B") == ("7B", 7.0)
        assert categorizer.extract_size_info("model-1.5B") == ("1.5B", 1.5)
        assert categorizer.extract_size_info("model-13b") == ("13b", 13.0)
        assert categorizer.extract_size_info("model-no-size") == (None, None)
    
    def test_categorize_by_size(self):
        """Test categorization by parameter size."""
        categorizer = ModelCategorizer()
        
        assert categorizer.categorize_by_size(0.5) == "tiny"
        assert categorizer.categorize_by_size(2.5) == "small"
        assert categorizer.categorize_by_size(7.0) == "medium"
        assert categorizer.categorize_by_size(13.0) == "large"
    
    def test_categorize_by_name(self):
        """Test categorization by name patterns."""
        categorizer = ModelCategorizer()
        
        assert categorizer.categorize_by_name("CodeLlama-7B") == "code"
        assert categorizer.categorize_by_name("model-instruct") == "instruct"
        assert categorizer.categorize_by_name("model-chat") == "chat"
        assert categorizer.categorize_by_name("regular-model") == "unknown"
    
    def test_categorize_model(self):
        """Test full model categorization."""
        categorizer = ModelCategorizer()
        
        # Test size-based categorization
        model_info = categorizer.categorize_model("org/test-model-7B-4bit")
        
        assert model_info.id == "org/test-model-7B-4bit"
        assert model_info.name == "test-model-7B-4bit"
        assert model_info.category == "medium"
        assert model_info.size_params == "7B"
        assert model_info.size_gb == 3.5  # 7B * 0.5 for 4bit
        assert model_info.quantization == "4bit"
        assert model_info.emoji == "🟡"
    
    def test_get_category_info(self):
        """Test category information retrieval."""
        categorizer = ModelCategorizer()
        
        tiny_info = categorizer.get_category_info("tiny")
        assert tiny_info["emoji"] == "🔵"
        assert "Tiny Models" in tiny_info["description"]
        assert tiny_info["name"] == "tiny"
    
    def test_group_models_by_category(self):
        """Test grouping models by category."""
        categorizer = ModelCategorizer()
        
        models = [
            ModelInfo("model1", "model1", "tiny", emoji="🔵"),
            ModelInfo("model2", "model2", "medium", emoji="🟡"),
            ModelInfo("model3", "model3", "tiny", emoji="🔵"),
        ]
        
        grouped = categorizer.group_models_by_category(models)
        
        assert len(grouped["tiny"]) == 2
        assert len(grouped["medium"]) == 1
        assert grouped["tiny"][0].id == "model1"


class TestModuleFunctions:
    """Test module-level functions."""
    
    def test_categorize_model_function(self):
        """Test the categorize_model function."""
        model_info = categorize_model("test/phi-2-MLX")
        
        assert isinstance(model_info, ModelInfo)
        assert model_info.id == "test/phi-2-MLX"
        assert model_info.name == "phi-2-MLX"
    
    def test_group_models_function(self, sample_models):
        """Test the group_models function."""
        grouped = group_models(sample_models)
        
        assert isinstance(grouped, dict)
        assert len(grouped) > 0
        
        # Check that all returned values are lists of ModelInfo
        for category, models in grouped.items():
            assert isinstance(models, list)
            for model in models:
                assert isinstance(model, ModelInfo)