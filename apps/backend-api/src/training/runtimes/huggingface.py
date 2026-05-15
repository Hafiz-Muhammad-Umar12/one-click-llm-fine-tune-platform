import json
from typing import Dict, Any, List
from src.training.runtimes.base import BaseRuntime, BaseLauncher

class TRLRuntime(BaseRuntime):
    """
    Concrete runtime for HuggingFace TRL (SFTTrainer / DPOTrainer).
    """
    def generate_command(self, job_context: Dict[str, Any]) -> List[str]:
        # Path to the actual python script that runs the TRL training loop
        # In a real environment, this script is baked into the worker Docker image.
        script_path = "/app/training/scripts/trl_trainer.py"
        
        # Serialize config to JSON to pass cleanly to the script
        config_payload = json.dumps({
            "model_name": job_context.get("model_name"),
            "dataset_uri": job_context.get("dataset_uri"),
            "hyperparameters": job_context.get("hyperparameters", {}),
            "checkpoint_dir": job_context.get("checkpoint_dir")
        })
        
        return ["python", script_path, "--config", config_payload]

    def prepare_environment(self, job_context: Dict[str, Any]) -> Dict[str, str]:
        env = {
            "PYTHONUNBUFFERED": "1",
            "TOKENIZERS_PARALLELISM": "true",
            "REDIS_STREAM_URL": job_context.get("redis_url", "redis://localhost:6379/0"),
            "JOB_ID": str(job_context.get("job_id"))
        }
        
        # Disable W&B if we are using our own tracking
        if not job_context.get("use_wandb"):
            env["WANDB_DISABLED"] = "true"
            
        return env

    def parse_logs_for_errors(self, logs: str) -> Dict[str, Any]:
        if "CUDA out of memory" in logs:
            return {"error_code": "CUDA_OOM", "is_recoverable": True} # Recoverable by lowering batch size / enabling gradient checkpointing
        if "Loss is NaN" in logs:
            return {"error_code": "NAN_LOSS", "is_recoverable": False}
        return {"error_code": "UNKNOWN_ERROR", "is_recoverable": False}

class AccelerateLauncher(BaseLauncher):
    """
    Launcher for multi-GPU using HuggingFace Accelerate.
    """
    def wrap_command(self, base_command: List[str], hardware_context: Dict[str, Any]) -> List[str]:
        num_processes = hardware_context.get("num_gpus", 1)
        
        launch_cmd = [
            "accelerate", "launch",
            "--num_processes", str(num_processes)
        ]
        
        # If FSDP or DeepSpeed is configured, add corresponding accelerate arguments here
        if hardware_context.get("use_deepspeed"):
            launch_cmd.extend(["--use_deepspeed", "--deepspeed_config_file", "ds_config.json"])
            
        launch_cmd.extend(base_command)
        return launch_cmd
