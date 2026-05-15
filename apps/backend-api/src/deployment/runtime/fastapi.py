from typing import List, Dict
from src.deployment.runtime.base import BaseRuntime, RuntimeConfig

class FastAPIRuntime(BaseRuntime):
    def get_container_image(self) -> str:
        # A generic base image for custom FastAPI inference
        return "python:3.10-slim"

    def get_command(self) -> List[str]:
        return [
            "uvicorn", "main:app",
            "--host", "0.0.0.0",
            "--port", str(self.config.port)
        ]

    def get_env_vars(self) -> Dict[str, str]:
        env = {
            "MODEL_ID": self.config.model_id,
            "MODEL_VERSION_ID": self.config.model_version_id
        }
        env.update(self.config.env_vars)
        return env
