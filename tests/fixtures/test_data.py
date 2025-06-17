"""
Test data and fixtures for ali tests.
"""

from ali.models.categories import ModelInfo


# Sample model data for testing
SAMPLE_MODELS = {
    "tiny": [
        "microsoft/phi-2",
        "microsoft/phi-1_5",
        "stabilityai/stablelm-zephyr-3b",
    ],
    "small": [
        "microsoft/phi-3-mini-4k-instruct",
        "google/gemma-2b-it",
        "Qwen/Qwen2-0.5B-Instruct",
    ],
    "medium": [
        "mistralai/Mistral-7B-Instruct-v0.2",
        "microsoft/DialoGPT-medium",
        "NousResearch/Llama-2-7b-chat-hf",
    ],
    "large": [
        "meta-llama/Llama-2-13b-chat-hf",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "microsoft/DialoGPT-large",
    ],
    "code": [
        "codellama/CodeLlama-7b-Instruct-hf",
        "deepseek-ai/deepseek-coder-6.7b-instruct",
        "microsoft/CodeGPT-small-py",
    ]
}

# Sample model info objects
SAMPLE_MODEL_INFOS = [
    ModelInfo(
        id="test-org/tiny-model-500m",
        name="tiny-model-500m",
        category="tiny",
        size_params="500M",
        size_gb=0.5,
        quantization=None,
        emoji="🔵"
    ),
    ModelInfo(
        id="test-org/small-model-2b",
        name="small-model-2b", 
        category="small",
        size_params="2B",
        size_gb=2.0,
        quantization=None,
        emoji="🟢"
    ),
    ModelInfo(
        id="test-org/medium-model-7b",
        name="medium-model-7b",
        category="medium",
        size_params="7B", 
        size_gb=7.0,
        quantization=None,
        emoji="🟡"
    ),
    ModelInfo(
        id="test-org/large-model-13b",
        name="large-model-13b",
        category="large",
        size_params="13B",
        size_gb=13.0,
        quantization=None,
        emoji="🟠"
    ),
    ModelInfo(
        id="test-org/code-model-6b",
        name="code-model-6b",
        category="code",
        size_params="6B",
        size_gb=6.0,
        quantization=None,
        emoji="💻"
    )
]

# Sample chat messages for testing prompt formatting
SAMPLE_CHAT_MESSAGES = [
    {"role": "user", "content": "Hello, how are you?"},
    {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"},
    {"role": "user", "content": "Can you explain what a neural network is?"},
    {"role": "assistant", "content": "A neural network is a computational model inspired by biological neural networks..."},
    {"role": "user", "content": "That's helpful, thanks!"}
]

# Sample system prompts for testing
SAMPLE_SYSTEM_PROMPTS = {
    "helpful": "You are a helpful assistant that provides accurate and useful information.",
    "code": "You are a coding assistant that helps users write, debug, and understand code.",
    "creative": "You are a creative writing assistant that helps users with storytelling and creative content.",
    "concise": "You are a concise assistant that provides brief, to-the-point responses."
}

# Sample configuration values for testing
SAMPLE_CONFIG_VALUES = {
    "performance": {
        "omp_num_threads": 8,
        "mlx_memory_pool": True,
        "max_cache_size_gb": 50
    },
    "chat": {
        "default_temperature": 0.7,
        "max_tokens": 2048,
        "stream": True
    },
    "models": {
        "categories": ["tiny", "small", "medium", "large", "code"],
        "default_backend": "ollama"
    }
}

# Sample environment variables for testing
SAMPLE_ENV_VARS = {
    "MLX_CACHE_DIR": "/test/cache/mlx",
    "MLX_MODELS_DIR": "/test/models",
    "HF_HOME": "/test/cache/huggingface",
    "OMP_NUM_THREADS": "8",
    "CUDA_VISIBLE_DEVICES": "0"
}