import pytest
from httpx import AsyncClient
from src.main import app
from src.core.config import settings

@pytest.mark.asyncio
async def test_create_and_launch_training_run():
    # This is a conceptual test. In reality, it requires a DB with an organization and a contract.
    # It demonstrates the API boundary of the Orchestration Engine.
    pass

def test_kubernetes_manifest_builder():
    from src.training.kubernetes.manifest_builder import KubernetesManifestBuilder
    
    builder = KubernetesManifestBuilder(namespace="test-ns")
    manifest = builder.build_job_manifest(
        job_id="test-job-1234",
        command=["python", "train.py"],
        env_vars={"WANDB_DISABLED": "true"},
        gpu_type="nvidia.com/gpu",
        gpu_count=2
    )
    
    assert manifest["kind"] == "Job"
    assert manifest["metadata"]["namespace"] == "test-ns"
    assert manifest["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]["nvidia.com/gpu"] == 2
    assert {"name": "WANDB_DISABLED", "value": "true"} in manifest["spec"]["template"]["spec"]["containers"][0]["env"]

def test_hf_runtime_generation():
    from src.training.runtimes.huggingface import TRLRuntime, AccelerateLauncher
    
    runtime = TRLRuntime()
    launcher = AccelerateLauncher()
    
    job_context = {
        "job_id": "job-123",
        "model_name": "Qwen/Qwen1.5-7B",
        "dataset_uri": "s3://bucket/data.parquet",
        "use_wandb": False
    }
    
    base_cmd = runtime.generate_command(job_context)
    assert "trl_trainer.py" in base_cmd[1]
    
    hardware_context = {"num_gpus": 4}
    launch_cmd = launcher.wrap_command(base_cmd, hardware_context)
    
    assert launch_cmd[0] == "accelerate"
    assert launch_cmd[1] == "launch"
    assert launch_cmd[2] == "--num_processes"
    assert launch_cmd[3] == "4"
