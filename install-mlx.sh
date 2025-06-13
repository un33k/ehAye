#!/bin/zsh

# Usage:
#   source ./install-mlx.sh
#   install_mlx [model_name]
#
# Example:
#   install_mlx mlx-community/DeepSeek-Coder-V2-Lite-Instruct-4bit-mlx

function install_mlx() {
    # 1. Robust check for virtualenv (works for zsh and bash)
    local venv_ok=0
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        venv_ok=1
    else
        # Check if python3 sys.prefix is a .venv in this directory
        local py_prefix
        py_prefix=$(python3 -c "import sys; print(sys.prefix)" 2>/dev/null)
        if [[ "$py_prefix" == "$(pwd)/.venv" ]] || [[ "$py_prefix" == *.venv ]]; then
            venv_ok=1
        fi
    fi

    if [ $venv_ok -ne 1 ]; then
        echo "❌ Please activate a virtualenv first."
        echo "   source ./envy"
        echo "   source .venv/bin/activate"
        return 1
    fi

    # 2. Install requirements
    pip install --quiet --upgrade mlx-lm || { echo '❌ Failed to install mlx-lm'; return 1; }

    # 3. Get model name from argument or use default
    local MODEL="${1:-mlx-community/DeepSeek-Coder-V2-Lite-Instruct-4bit-mlx}"
    echo "🔎 Using model: $MODEL"

    # 4. Test the model
    python3 -c "
from mlx_lm import load, generate
try:
    print('Loading model...')
    model, tokenizer = load('$MODEL')
    print('Model loaded successfully!')
    prompt = 'Write a Python function to calculate fibonacci numbers:'
    print('Prompt:', prompt)
    response = generate(model, tokenizer, prompt=prompt, max_tokens=100)
    print('---\n' + response + '\n---')
    print('✅ Model is working!')
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)
" || echo '❌ Model test failed.'
}