#!/usr/bin/env python3
"""
MLX Configuration Module
Centralized configuration for all MLX scripts
Reads from mlx-config.json
"""

import os
import json
from pathlib import Path

class MLXConfig:
    """Centralized MLX configuration loaded from JSON"""
    
    def __init__(self, config_file="mlx-config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.home_dir = Path.home()
        
        # Expand paths
        self.paths = {}
        for key, path in self.config["paths"].items():
            self.paths[key] = Path(path.replace("~", str(self.home_dir)))
        
        # Environment variables with expanded paths
        self.env_vars = {}
        for var, value in self.config["environment_variables"].items():
            self.env_vars[var] = value.replace("~", str(self.home_dir))
        
        # Model categories
        self.model_categories = self.config["model_categories"]
        
        # Performance settings
        self.performance = self.config["performance"]
        
        # Defaults
        self.defaults = self.config["defaults"]
    
    def _load_config(self):
        """Load configuration from JSON file"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file {self.config_file} not found")
        
        with open(self.config_file, 'r') as f:
            return json.load(f)
    
    def setup_directories(self):
        """Create all necessary directories"""
        # Create base directories
        for path in self.paths.values():
            path.mkdir(parents=True, exist_ok=True)
        
        # Create model category subdirectories
        for category in self.model_categories:
            (self.paths["models_dir"] / category).mkdir(exist_ok=True)
    
    def setup_environment(self):
        """Set up environment variables"""
        for var, value in self.env_vars.items():
            os.environ[var] = value
        
        # Create directories
        self.setup_directories()
    
    def check_environment(self):
        """Check if all required environment variables are set"""
        missing_vars = []
        for var in self.env_vars.keys():
            if var not in os.environ:
                missing_vars.append(var)
        return missing_vars
    
    def get_model_list_file(self, category):
        """Get path to model list file for a category"""
        return self.paths["models_dir"] / category / ".model_list"
    
    def print_config(self):
        """Print current configuration"""
        print("🔧 MLX Configuration:")
        for var, value in self.env_vars.items():
            print(f"   {var}={value}")
    
    def get_path(self, path_name):
        """Get a specific path by name"""
        return self.paths.get(path_name)
    
    def get_env_var(self, var_name):
        """Get a specific environment variable value"""
        return self.env_vars.get(var_name)

# Global config instance
mlx_config = MLXConfig()

def ensure_mlx_environment():
    """Ensure MLX environment is properly set up"""
    missing_vars = mlx_config.check_environment()
    if missing_vars:
        print("🔧 Setting up MLX environment...")
        mlx_config.setup_environment()
        print("✅ MLX environment configured")
    return True