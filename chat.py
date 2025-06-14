#!/usr/bin/env python3
"""
Simple MLX Chat Interface
Usage: python chat.py [--model MODEL] [--max-tokens N] [--temp T]
"""

import argparse
import time
import os
import sys
import readline
import atexit

# Check if running in correct virtual environment
def check_virtual_env():
    """Ensure we're running in the correct virtual environment"""
    import subprocess
    
    # Check if in any virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        if 'VIRTUAL_ENV' not in os.environ and 'CONDA_DEFAULT_ENV' not in os.environ:
            print("❌ Error: Not running in a virtual environment!")
            print("🔒 For safety, this script requires a virtual environment.")
            print("")
            print("💡 To fix this:")
            print("   1. Run: source .venv/bin/activate") 
            print("   2. Or run: ./venv.sh")
            print("   3. Then run this script again")
            sys.exit(1)
    
    # Check if using the correct Python executable
    try:
        current_python = subprocess.check_output(['which', 'python'], text=True).strip()
        expected_python = os.path.abspath('.venv/bin/python')
        
        if current_python != expected_python:
            print("❌ Error: Not using the correct virtual environment!")
            print(f"🔍 Current Python: {current_python}")
            print(f"🎯 Expected Python: {expected_python}")
            print("")
            print("💡 To fix this:")
            print("   1. Run: source .venv/bin/activate")
            print("   2. Verify with: which python")
            print("   3. Then run this script again")
            sys.exit(1)
            
    except subprocess.CalledProcessError:
        print("❌ Error: Cannot determine Python path")
        sys.exit(1)

# Check virtual environment at startup
check_virtual_env()

from mlx_lm import load, generate
from mlx_lm.generate import stream_generate
from mlx_lm.sample_utils import make_sampler
import os
from pathlib import Path

def get_installed_models():
    """Get list of installed models from the MLX cache"""
    models = []
    models_dir = Path.home() / ".mlx-cache" / "models"
    
    if not models_dir.exists():
        return models
    
    # Category emojis
    category_emojis = {
        "tiny": "🔵",
        "small": "🟢", 
        "medium": "🟡",
        "large": "🔴",
        "code": "💻"
    }
    
    # Category descriptions
    category_desc = {
        "tiny": "Tiny Models (< 2B parameters)",
        "small": "Small Models (2B-3B parameters)",
        "medium": "Medium Models (3B-8B parameters)", 
        "large": "Large Models (> 8B parameters)",
        "code": "Code Models (specialized for programming)"
    }
    
    for category in ["tiny", "small", "medium", "large", "code"]:
        category_dir = models_dir / category
        model_list_file = category_dir / ".model_list"
        
        if model_list_file.exists() and model_list_file.stat().st_size > 0:
            emoji = category_emojis.get(category, "📦")
            desc = category_desc.get(category, category.title())
            
            with open(model_list_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("model_id:"):
                        model_id = line.replace("model_id:", "")
                        model_name = model_id.split("/")[-1] if "/" in model_id else model_id
                        
                        # Extract size info
                        size_info = ""
                        if any(size in model_id.lower() for size in ["1b", "2b", "3b", "7b", "13b", "33b", "67b"]):
                            import re
                            size_match = re.search(r'(\d+\.?\d*[Bb])', model_id)
                            if size_match:
                                size_info = f" ({size_match.group(1).upper()})"
                        
                        models.append({
                            "id": model_id,
                            "name": model_name,
                            "category": category,
                            "emoji": emoji,
                            "size": size_info,
                            "display": f"{emoji} {model_name.replace('-', ' ').replace('_', ' ')}{size_info}"
                        })
    
    return models

def select_model():
    """Let user select from installed models"""
    models = get_installed_models()
    
    if not models:
        print("❌ No models found!")
        print("💡 To install models:")
        print("   ./llm.sh -s <pattern>  # Search models")
        print("   ./llm.sh -d <number>   # Download by number")
        return None
    
    print("🤖 Available Models:")
    print("=" * 50)
    
    # Group by category
    current_category = None
    model_index = 1
    
    for model in models:
        if model["category"] != current_category:
            if current_category is not None:
                print()
            
            category_desc = {
                "tiny": "Tiny Models (< 2B parameters)",
                "small": "Small Models (2B-3B parameters)",
                "medium": "Medium Models (3B-8B parameters)",
                "large": "Large Models (> 8B parameters)",
                "code": "Code Models (specialized for programming)"
            }
            
            desc = category_desc.get(model["category"], model["category"].title())
            print(f"{model['emoji']} {desc}:")
            current_category = model["category"]
        
        print(f"  {model_index:2d}. {model['display']}")
        model_index += 1
    
    print()
    print(f"📊 Total: {len(models)} model(s) available")
    print()
    
    # Get user selection
    while True:
        try:
            try:
                choice = input(f"Select model (1-{len(models)}) or 'q' to quit: ").strip()
            except EOFError:
                print("\n👋 Goodbye!")
                return None
            
            if choice.lower() == 'q':
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(models):
                selected_model = models[choice_num - 1]
                print(f"✅ Selected: {selected_model['display']}")
                print(f"📦 Model ID: {selected_model['id']}")
                return selected_model['id']
            else:
                print(f"⚠️  Please enter a number between 1 and {len(models)}")
                
        except ValueError:
            print("⚠️  Please enter a valid number or 'q' to quit")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return None

def get_default_model():
    """Get a reasonable default model based on available models"""
    models = get_installed_models()
    if models:
        return models[0]['id']  # Return first available model
    
    # Fallback to common models
    candidate_models = [
        "mlx-community/Mistral-7B-Instruct-v0.1-4bit-mlx",
        "mlx-community/phi-2-MLX",
        "mlx-community/CodeLlama-7b-Instruct-hf-4bit-mlx",
        "mlx-community/Llama-2-7b-chat-hf-4bit-mlx"
    ]
    
    return candidate_models[0]  # Default to Mistral

def format_chat_prompt(message, model_name=""):
    """Format the prompt based on the model type"""
    if "mistral" in model_name.lower():
        return f"<s>[INST] {message} [/INST]"
    elif "llama" in model_name.lower():
        return f"### Human: {message}\n### Assistant:"
    elif "phi" in model_name.lower():
        return f"Human: {message}\nAssistant:"
    elif "deepseek" in model_name.lower():
        return f"User: {message}\n\nAssistant:"
    elif "qwen" in model_name.lower():
        return f"<|im_start|>user\n{message}<|im_end|>\n<|im_start|>assistant\n"
    elif "gemma" in model_name.lower():
        return f"<start_of_turn>user\n{message}<end_of_turn>\n<start_of_turn>model\n"
    else:
        return message

def show_gpu_memory():
    """Show GPU memory limit if available"""
    try:
        import subprocess
        result = subprocess.run(['sysctl', '-n', 'iogpu.wired_limit_mb'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            gpu_mb = int(result.stdout.strip())
            print(f"🎮 GPU Memory Limit: {gpu_mb}MB ({gpu_mb/1024:.1f}GB)")
        else:
            print("🎮 GPU Memory: Not available")
    except Exception:
        print("🎮 GPU Memory: Not detected")

def print_model_info(model_name):
    """Print information about the loaded model"""
    print(f"🤖 Model: {model_name}")
    
    # Show GPU memory limit
    show_gpu_memory()
    
    # Estimate model size and type
    if "phi-2" in model_name.lower():
        print("   📏 Size: ~2.7B parameters (2.8GB)")
        print("   🎯 Best for: Quick responses, testing")
    elif "7b" in model_name.lower():
        print("   📏 Size: ~7B parameters (4-7GB)")
        print("   🎯 Best for: General chat, coding")
    elif "13b" in model_name.lower():
        print("   📏 Size: ~13B parameters (7-13GB)")
        print("   🎯 Best for: High quality responses")
    elif "mixtral" in model_name.lower():
        print("   📏 Size: ~46.7B parameters (26GB)")
        print("   🎯 Best for: Expert-level responses")

def show_help():
    """Show available commands during chat"""
    print("""
💡 Available commands:
   quit, exit, q    - Exit the chat
   clear           - Clear the screen
   help            - Show this help
   stats           - Show memory usage
   temp <value>    - Change temperature (0.1-2.0)
   tokens <value>  - Change max tokens (1-2048)
   model           - Show current model info
   stream          - Toggle streaming mode on/off
   
🎮 Keyboard shortcuts:
   ↑↓ arrows       - Navigate command history
   Ctrl+A          - Move to beginning of line
   Ctrl+E          - Move to end of line
   Ctrl+K          - Delete to end of line
   Ctrl+U          - Delete entire line
   Ctrl+H          - Show help (quick shortcut)
   Tab             - Basic completion
   """)

def show_stats():
    """Show current memory and performance stats"""
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024**2)
        
        print(f"📊 Memory usage: {memory_mb:.1f}MB")
        print(f"🧠 Available memory: {psutil.virtual_memory().available / (1024**3):.1f}GB")
        
        # GPU memory if available
        try:
            import subprocess
            result = subprocess.run(['sysctl', '-n', 'iogpu.wired_limit_mb'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                gpu_mb = int(result.stdout.strip())
                print(f"🎮 GPU memory limit: {gpu_mb}MB")
        except:
            pass
            
    except ImportError:
        print("📊 Stats require psutil package")

def setup_readline():
    """Setup readline for command history and arrow key navigation"""
    try:
        # Set up history file
        history_file = os.path.expanduser('~/.mlx_chat_history')
        
        # Enable history
        readline.set_startup_hook(None)
        
        # Load existing history
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass  # First time, no history file yet
        
        # Limit history size
        readline.set_history_length(1000)
        
        # Save history on exit
        atexit.register(readline.write_history_file, history_file)
        
        # Enable tab completion (basic)
        readline.parse_and_bind('tab: complete')
        
        # Enable arrow key navigation
        readline.parse_and_bind('"\e[A": previous-history')  # Up arrow
        readline.parse_and_bind('"\e[B": next-history')      # Down arrow
        readline.parse_and_bind('"\e[C": forward-char')      # Right arrow
        readline.parse_and_bind('"\e[D": backward-char')     # Left arrow
        
        # Enable common editing shortcuts
        readline.parse_and_bind('"\C-a": beginning-of-line')  # Ctrl+A
        readline.parse_and_bind('"\C-e": end-of-line')        # Ctrl+E
        readline.parse_and_bind('"\C-k": kill-line')          # Ctrl+K
        readline.parse_and_bind('"\C-u": unix-line-discard')  # Ctrl+U
        readline.parse_and_bind('"\C-h": "help\n"')           # Ctrl+H for help
        
        print("✅ Command history enabled (↑↓ arrows, Ctrl+A/E/K/U)")
        
    except ImportError:
        print("⚠️  Readline not available - arrow key history disabled")
    except Exception as e:
        print(f"⚠️  History setup failed: {e}")

def show_memory_usage():
    """Show current memory usage"""
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024**2)
        total_memory_gb = psutil.virtual_memory().total / (1024**3)
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        used_percent = psutil.virtual_memory().percent
        
        print(f"📊 System Memory: {available_memory_gb:.1f}GB available / {total_memory_gb:.1f}GB total ({100-used_percent:.1f}% free)")
        print(f"📱 Process Memory: {memory_mb:.1f}MB")
        
    except ImportError:
        print("📊 Memory stats require psutil package")
    except Exception as e:
        print(f"📊 Memory stats unavailable: {e}")

def main():
    # Setup command line history
    setup_readline()
    print("\n🚀 MLX Chat Interface")
    print("=" * 50)
    
    # Show memory usage
    show_memory_usage()
    
    parser = argparse.ArgumentParser(description="MLX Chat Interface")
    parser.add_argument("--model", default=None, 
                       help="Model to use (if not specified, will show selection menu)")
    parser.add_argument("--max-tokens", type=int, default=512,
                       help="Maximum tokens to generate")
    parser.add_argument("--temp", type=float, default=0.7,
                       help="Temperature for generation")
    parser.add_argument("--system", default="",
                       help="System prompt (optional)")
    parser.add_argument("--no-stream", action="store_true", default=False,
                       help="Generate full response at once (default: streaming enabled)")
    
    args = parser.parse_args()
    
    # Set streaming based on --no-stream flag
    args.stream = not args.no_stream
    
    # If no model specified, show selection menu
    if args.model is None:
        args.model = select_model()
        if args.model is None:
            return 0
        print()
    else:
        # Use provided model
        pass
    
    # Validate parameters
    if args.temp < 0.1 or args.temp > 2.0:
        print("⚠️  Temperature should be between 0.1 and 2.0")
        args.temp = max(0.1, min(2.0, args.temp))
    
    if args.max_tokens < 1 or args.max_tokens > 4096:
        print("⚠️  Max tokens should be between 1 and 4096")
        args.max_tokens = max(1, min(4096, args.max_tokens))
    
    print(f"🔥 Loading model: {args.model}")
    print("   This may take a moment...")
    
    try:
        start_time = time.time()
        model, tokenizer = load(args.model)
        load_time = time.time() - start_time
        print(f"✅ Model loaded in {load_time:.2f}s")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print("\n💡 Try one of these models:")
        for model in [
            "mlx-community/phi-2-MLX",
            "mlx-community/Mistral-7B-Instruct-v0.1-4bit-mlx",
            "mlx-community/CodeLlama-7b-Instruct-hf-4bit-mlx"
        ]:
            print(f"   {model}")
        return 1
    
    print_model_info(args.model)
    
    print(f"\n💬 MLX Chat Session")
    stream_status = "🌊 ON" if args.stream else "⏸️  OFF"
    print(f"⚙️  Settings: temp={args.temp}, max_tokens={args.max_tokens}, stream={stream_status}")
    print("💡 Type 'help' (or Ctrl+H) for commands, 'quit' to exit")
    print("🎮 Use ↑↓ arrows for command history")
    print("-" * 60)
    
    # Add system prompt if provided
    conversation_history = []
    if args.system:
        conversation_history.append(f"System: {args.system}")
        print(f"🎯 System prompt: {args.system}")
    
    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'clear':
                os.system('clear' if os.name != 'nt' else 'cls')
                continue
            elif user_input.lower() == 'help' or user_input.lower() == 'h':
                show_help()
                continue
            elif user_input.lower() == 'stats':
                show_stats()
                continue
            elif user_input.lower() == 'model':
                print_model_info(args.model)
                continue
            elif user_input.lower() == 'stream':
                args.stream = not args.stream
                stream_status = "🌊 ON" if args.stream else "⏸️  OFF"
                print(f"🔄 Streaming mode: {stream_status}")
                continue
            elif user_input.lower().startswith('temp '):
                try:
                    new_temp = float(user_input.split()[1])
                    if 0.1 <= new_temp <= 2.0:
                        args.temp = new_temp
                        print(f"🌡️  Temperature set to {args.temp}")
                    else:
                        print("⚠️  Temperature must be between 0.1 and 2.0")
                except (ValueError, IndexError):
                    print("⚠️  Usage: temp <value>")
                continue
            elif user_input.lower().startswith('tokens '):
                try:
                    new_tokens = int(user_input.split()[1])
                    if 1 <= new_tokens <= 4096:
                        args.max_tokens = new_tokens
                        print(f"🎯 Max tokens set to {args.max_tokens}")
                    else:
                        print("⚠️  Max tokens must be between 1 and 4096")
                except (ValueError, IndexError):
                    print("⚠️  Usage: tokens <value>")
                continue
            elif not user_input:
                continue
            
            # Format prompt based on model
            formatted_prompt = format_chat_prompt(user_input, args.model)
            
            print("🤖 Assistant: ", end="", flush=True)
            
            # Generate response with timing
            start_time = time.time()
            try:
                # Create sampler with temperature
                sampler = make_sampler(temp=args.temp)
                
                if args.stream:
                    # Streaming generation
                    response_tokens = []
                    for chunk in stream_generate(
                        model, tokenizer, 
                        prompt=formatted_prompt,
                        max_tokens=args.max_tokens,
                        sampler=sampler
                    ):
                        # Print token as it's generated
                        token_text = chunk.text
                        print(token_text, end="", flush=True)
                        response_tokens.append(token_text)
                    
                    # Combine all tokens for the full response
                    response = "".join(response_tokens)
                    print()  # New line after streaming
                    
                else:
                    # Non-streaming generation
                    response = generate(
                        model, tokenizer, 
                        prompt=formatted_prompt,
                        max_tokens=args.max_tokens,
                        sampler=sampler,
                        verbose=False
                    )
                    
                    # Clean up response formatting
                    if formatted_prompt in response:
                        response = response.replace(formatted_prompt, "").strip()
                    
                    print(response)
                
                generation_time = time.time() - start_time
                
                # Show generation stats
                words = len(response.split())
                tokens_estimated = len(response.split()) * 1.3  # Rough estimate
                tokens_per_sec = tokens_estimated / generation_time if generation_time > 0 else 0
                
                stream_indicator = "🌊" if args.stream else "⚡"
                print(f"\n{stream_indicator} Generated {words} words in {generation_time:.2f}s ({tokens_per_sec:.1f} tokens/sec)")
                
            except Exception as e:
                print(f"❌ Generation error: {e}")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    exit(main())