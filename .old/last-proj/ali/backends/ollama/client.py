"""Ollama HTTP client for API interactions."""

import json
import subprocess
import time
from typing import Dict, List, Optional, Iterator, Any
import requests
from pathlib import Path

from ...exceptions import BackendConnectionError, BackendTimeoutError, OllamaError
from ...logging import get_logger
from ..base import BaseBackend, ModelInfo, ChatMessage, GenerationConfig

logger = get_logger("backends.ollama.client")


class OllamaClient(BaseBackend):
    """Ollama HTTP client for API-based interactions."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        
    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        timeout: Optional[float] = None
    ) -> requests.Response:
        """Make HTTP request to Ollama API."""
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                stream=stream,
                timeout=timeout or 30
            )
            
            if not stream and not response.ok:
                error_msg = f"Ollama API error: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('error', response.text)}"
                    except json.JSONDecodeError:
                        error_msg += f" - {response.text}"
                
                raise OllamaError(error_msg, status_code=response.status_code)
            
            return response
            
        except requests.Timeout:
            raise BackendTimeoutError("ollama", f"API request to {endpoint}", timeout or 30)
        except requests.ConnectionError as e:
            raise BackendConnectionError("ollama", self.base_url, cause=e)
        except requests.RequestException as e:
            raise OllamaError(f"Request failed: {e}", cause=e)
    
    def list_models(self) -> List[ModelInfo]:
        """List all installed models via API."""
        try:
            response = self._make_request("GET", "tags")
            data = response.json()
            
            models = []
            for model_data in data.get("models", []):
                models.append(ModelInfo(
                    id=model_data["name"],
                    name=model_data["name"],
                    size=self._format_size(model_data.get("size", 0)),
                    family=model_data.get("details", {}).get("family"),
                    format="ollama",
                    installed=True
                ))
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to list models via API: {e}")
            return []
    
    def search_models(self, query: Optional[str] = None) -> List[ModelInfo]:
        """Search available models."""
        # For now, return curated list since Ollama doesn't have search API
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
        """Download model via API with progress tracking."""
        try:
            data = {"name": model_id}
            response = self._make_request("POST", "pull", data=data, stream=True, timeout=None)
            
            total_size = 0
            downloaded = 0
            
            for line in response.iter_lines():
                if line:
                    try:
                        progress_data = json.loads(line)
                        
                        if "total" in progress_data:
                            total_size = progress_data["total"]
                        
                        if "completed" in progress_data:
                            downloaded = progress_data["completed"]
                        
                        if progress_callback and "status" in progress_data:
                            status = progress_data["status"]
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                progress_callback(f"{status}: {percent:.1f}%")
                            else:
                                progress_callback(status)
                        
                        # Check for completion
                        if progress_data.get("status") == "success":
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            return ModelInfo(
                id=model_id,
                name=model_id,
                format="ollama",
                installed=True
            )
            
        except Exception as e:
            logger.error(f"Failed to download model {model_id}: {e}")
            raise
    
    def remove_model(self, model_id: str) -> bool:
        """Remove model via API."""
        try:
            data = {"name": model_id}
            self._make_request("DELETE", "delete", data=data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove model {model_id}: {e}")
            return False
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get model information via API."""
        try:
            data = {"name": model_id}
            response = self._make_request("POST", "show", data=data)
            model_data = response.json()
            
            return ModelInfo(
                id=model_id,
                name=model_id,
                description=model_data.get("license"),
                parameters=model_data.get("details", {}).get("parameter_size"),
                family=model_data.get("details", {}).get("family"),
                format="ollama",
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
        """Generate text via API."""
        try:
            # Convert messages to Ollama format
            ollama_messages = []
            for msg in messages:
                ollama_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            data = {
                "model": model_id,
                "messages": ollama_messages,
                "stream": config.stream,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens,
                    "top_p": config.top_p,
                }
            }
            
            if config.stop_sequences:
                data["options"]["stop"] = config.stop_sequences
            
            response = self._make_request("POST", "chat", data=data, stream=config.stream, timeout=None)
            
            if config.stream:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line)
                            if "message" in chunk_data:
                                content = chunk_data["message"].get("content", "")
                                if content:
                                    yield content
                                
                                # Check if done
                                if chunk_data.get("done", False):
                                    break
                        except json.JSONDecodeError:
                            continue
            else:
                result = response.json()
                if "message" in result:
                    yield result["message"]["content"]
                    
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            yield f"Error: {e}"
    
    def load_model(self, model_id: str) -> bool:
        """Load model (Ollama loads automatically)."""
        # Ollama loads models automatically on first use
        return True
    
    def unload_model(self, model_id: str) -> bool:
        """Unload model (Ollama manages automatically)."""
        # Ollama manages memory automatically
        return True
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"