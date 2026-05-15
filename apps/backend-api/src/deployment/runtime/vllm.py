from typing import List, Dict
from src.deployment.runtime.base import BaseRuntime, RuntimeConfig

class VLLMRuntime(BaseRuntime):
    def get_container_image(self) -> str:
        # Default vLLM image
        return "vllm/vllm-openai:latest"

    def get_command(self) -> List[str]:
        cmd = [
            "python3", "-m", "vllm.entrypoints.openai.api_server",
            "--model", self.config.model_id,
            "--tensor-parallel-size", str(self.config.tensor_parallel_size),
            "--host", "0.0.0.0",
            "--port", str(self.config.port)
        ]
        
        if self.config.max_model_len:
            cmd.extend(["--max-model-len", str(self.config.max_model_len)])
            
        return cmd

    def get_env_vars(self) -> Dict[str, str]:
        env = {
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            "VLLM_LOGGING_LEVEL": "INFO"
        }
        env.update(self.config.env_vars)
        return env
