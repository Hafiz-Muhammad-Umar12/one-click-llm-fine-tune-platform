from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class RuntimeConfig(BaseModel):
    model_id: str
    model_version_id: str
    organization_id: str
    hardware_tier: str
    tensor_parallel_size: int = 1
    max_model_len: Optional[int] = None
    env_vars: Dict[str, str] = {}
    port: int = 8000

class BaseRuntime(ABC):
    def __init__(self, config: RuntimeConfig):
        self.config = config

    @abstractmethod
    def get_container_image(self) -> str:
        """Returns the docker image for the runtime."""
        pass

    @abstractmethod
    def get_command(self) -> List[str]:
        """Returns the startup command for the container."""
        pass

    @abstractmethod
    def get_env_vars(self) -> Dict[str, str]:
        """Returns extra environment variables."""
        pass

    def get_resources(self) -> Dict[str, Any]:
        """Returns Kubernetes resource requirements based on hardware tier."""
        # This will be refined based on Hardware Tier mapping
        return {
            "requests": {"cpu": "2", "memory": "8Gi", "nvidia.com/gpu": "1"},
            "limits": {"cpu": "4", "memory": "16Gi", "nvidia.com/gpu": "1"}
        }
