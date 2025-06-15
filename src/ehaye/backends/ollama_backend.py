"""Ollama backend implementation."""

import json
import subprocess
import time
from typing import List, Dict, Optional, Iterator
from pathlib import Path

from ..core.logging import get_logger
from .base import BaseBackend, ModelInfo, ChatMessage, GenerationConfig

logger = get_logger("backends.ollama")


class OllamaBackend(BaseBackend):
    """Ollama backend for LLM operations."""
    
    def __init__(self):
        self.service_url = "http://localhost:11434"
        
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            result = subprocess.run(
                ["ollama", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _run_ollama_cmd(self, args: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """Run an Ollama command and return the result."""
        try:
            cmd = ["ollama"] + args
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode != 0:
                logger.error(f"Ollama command failed: {result.stderr}")
                
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Ollama command timed out: {args}")
            raise
        except FileNotFoundError:
            logger.error("Ollama command not found")
            raise
    
    def list_models(self) -> List[ModelInfo]:
        """List all installed models."""
        try:
            result = self._run_ollama_cmd(["list"])
            if result.returncode != 0:
                return []
            
            models = []
            lines = result.stdout.strip().split('\n')
            
            # Skip header line if present
            for i, line in enumerate(lines):
                if i == 0 and ('NAME' in line.upper() or 'MODEL' in line.upper()):
                    continue  # Skip header
                    
                if not line.strip():
                    continue
                    
                # Split by whitespace (spaces/tabs)
                parts = line.split()
                
                if len(parts) >= 4:
                    model_name = parts[0].strip()
                    size = f"{parts[2]} {parts[3]}"  # Combine number and unit
                    
                    models.append(ModelInfo(
                        id=model_name,
                        name=model_name,
                        size=size,
                        installed=True
                    ))
            return models
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def search_models(self, query: Optional[str] = None) -> List[ModelInfo]:
        """Search available models for download."""
        # Ollama doesn't have a built-in search, so we'll provide a curated list
        popular_models = [
            ModelInfo(id="llama3.2", name="Llama 3.2", size="2.0B", family="llama"),
            ModelInfo(id="llama3.2:1b", name="Llama 3.2 1B", size="1.3B", family="llama"),
            ModelInfo(id="llama3.1", name="Llama 3.1", size="8.0B", family="llama"),
            ModelInfo(id="phi3", name="Phi-3", size="3.8B", family="phi"),
            ModelInfo(id="phi3:mini", name="Phi-3 Mini", size="2.3B", family="phi"),
            ModelInfo(id="gemma2", name="Gemma 2", size="9.0B", family="gemma"),
            ModelInfo(id="gemma2:2b", name="Gemma 2 2B", size="2.6B", family="gemma"),
            ModelInfo(id="qwen2", name="Qwen 2", size="7.6B", family="qwen"),
            ModelInfo(id="qwen2:1.5b", name="Qwen 2 1.5B", size="1.5B", family="qwen"),
            ModelInfo(id="mistral", name="Mistral", size="7.2B", family="mistral"),
            ModelInfo(id="codellama", name="Code Llama", size="7.0B", family="llama"),
            ModelInfo(id="codellama:7b-python", name="Code Llama Python", size="7.0B", family="llama"),
            ModelInfo(id="deepseek-coder", name="DeepSeek Coder", size="6.7B", family="deepseek"),
            ModelInfo(id="nomic-embed-text", name="Nomic Embed Text", size="274M", family="nomic"),
        ]
        
        if query:
            query_lower = query.lower()
            return [m for m in popular_models if query_lower in m.name.lower() or query_lower in m.id.lower()]
        
        return popular_models
    
    def download_model(self, model_id: str, progress_callback: Optional[callable] = None) -> ModelInfo:
        """Download and install a model."""
        logger.info(f"Downloading model: {model_id}")
        
        try:
            # Use subprocess.Popen for real-time output
            # Combine stdout and stderr since Ollama outputs progress to stderr
            process = subprocess.Popen(
                ["ollama", "pull", model_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                text=True,
                bufsize=0,  # Unbuffered for real-time output
                universal_newlines=True
            )
            
            # Monitor progress
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    if progress_callback:
                        progress_callback(line)
                    logger.debug(f"Download progress: {line}")
            
            # Wait for completion
            return_code = process.wait()
            
            if return_code == 0:
                logger.info(f"Successfully downloaded model: {model_id}")
                return ModelInfo(
                    id=model_id,
                    name=model_id,
                    installed=True
                )
            else:
                # Error details were already captured in progress output
                logger.error(f"Failed to download model {model_id}")
                raise RuntimeError(f"Download failed with exit code {return_code}")
                
        except Exception as e:
            logger.error(f"Error downloading model {model_id}: {e}")
            raise
    
    def remove_model(self, model_id: str) -> bool:
        """Remove an installed model."""
        try:
            result = self._run_ollama_cmd(["rm", model_id])
            if result.returncode == 0:
                logger.info(f"Successfully removed model: {model_id}")
                return True
            else:
                logger.error(f"Failed to remove model {model_id}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error removing model {model_id}: {e}")
            return False
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get detailed information about a model."""
        try:
            result = self._run_ollama_cmd(["show", model_id])
            if result.returncode != 0:
                return None
            
            # Parse the output for model information
            info_text = result.stdout
            
            # Extract basic info from the output
            return ModelInfo(
                id=model_id,
                name=model_id,
                description=info_text.split('\n')[0] if info_text else None,
                installed=True
            )
            
        except Exception as e:
            logger.error(f"Failed to get model info for {model_id}: {e}")
            return None
    
    def generate(
        self, 
        model_id: str, 
        messages: List[ChatMessage], 
        config: GenerationConfig
    ) -> Iterator[str]:
        """Generate text response from the model."""
        try:
            # Convert messages to Ollama format
            prompt = self._format_messages(messages)
            
            # Build the command
            cmd = ["ollama", "generate", model_id, prompt]
            
            # Add temperature if specified
            if config.temperature != 0.7:
                cmd.extend(["--temperature", str(config.temperature)])
            
            if config.stream:
                # Streaming generation
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        yield output.rstrip('\n')
            else:
                # Non-streaming generation
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    yield result.stdout
                else:
                    logger.error(f"Generation failed: {result.stderr}")
                    yield f"Error: {result.stderr}"
                    
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            yield f"Error: {e}"
    
    def _format_messages(self, messages: List[ChatMessage]) -> str:
        """Format messages for Ollama."""
        if len(messages) == 1:
            return messages[0].content
        
        # For multi-turn conversations, format as a simple prompt
        formatted = []
        for msg in messages:
            if msg.role == "user":
                formatted.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                formatted.append(f"Assistant: {msg.content}")
            elif msg.role == "system":
                formatted.append(f"System: {msg.content}")
        
        return "\n".join(formatted) + "\nAssistant:"
    
    def load_model(self, model_id: str) -> bool:
        """Load a model into memory for inference."""
        # Ollama loads models automatically when needed
        try:
            # Test if model is available by running a simple query
            result = self._run_ollama_cmd(["generate", model_id, "Hello", "--verbose"], timeout=10)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory."""
        # Ollama manages memory automatically
        logger.info(f"Ollama manages model memory automatically for {model_id}")
        return True