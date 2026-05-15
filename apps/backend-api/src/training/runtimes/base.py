from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseRuntime(ABC):
    """
    Abstract interface for ML training runtimes (e.g., HuggingFace Trainer, TRL, Custom).
    Decouples the orchestrator from the specific training framework.
    """
    
    @abstractmethod
    def generate_command(self, job_context: Dict[str, Any]) -> List[str]:
        """
        Translates a training configuration into a concrete CLI command.
        Must handle hyperparameter injection safely.
        """
        pass

    @abstractmethod
    def prepare_environment(self, job_context: Dict[str, Any]) -> Dict[str, str]:
        """
        Generates required environment variables for the training process.
        Injects secrets, node ranks, and observability hooks.
        """
        pass

    @abstractmethod
    def parse_logs_for_errors(self, logs: str) -> Dict[str, Any]:
        """
        Analyzes standard output/error to identify known failure modes (e.g., OOM).
        Returns a structured dictionary mapping to TrainingFailureReport fields.
        """
        pass

class BaseLauncher(ABC):
    """
    Abstract interface for distributed launchers (e.g., Accelerate, Torchrun).
    Wraps the BaseRuntime command.
    """
    
    @abstractmethod
    def wrap_command(self, base_command: List[str], hardware_context: Dict[str, Any]) -> List[str]:
        """
        Wraps the runtime command with distributed execution arguments.
        """
        pass
