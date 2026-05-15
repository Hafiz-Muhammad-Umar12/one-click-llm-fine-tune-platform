import logging
from typing import Dict, Any, Optional
from src.training.kubernetes.manifest_builder import KubernetesManifestBuilder

logger = logging.getLogger(__name__)

class KubernetesJobManager:
    """
    Interfaces with the Kubernetes API to orchestrate Training Jobs.
    In a real environment, this would use the `kubernetes` Python client.
    """
    def __init__(self):
        self.manifest_builder = KubernetesManifestBuilder()
        
    async def submit_job(self, manifest: Dict[str, Any]) -> str:
        """
        Submits the manifest to the K8s API server.
        Returns the created K8s Job name.
        """
        job_name = manifest["metadata"]["name"]
        logger.info(f"Submitting K8s Job: {job_name}")
        # Mocking the actual kubernetes.client.BatchV1Api().create_namespaced_job()
        return job_name

    async def get_job_status(self, job_name: str, namespace: str) -> str:
        """
        Queries the K8s API to determine the state of the job.
        Returns: pending, running, completed, failed
        """
        # Mocking kubernetes.client.BatchV1Api().read_namespaced_job_status()
        return "running"
        
    async def delete_job(self, job_name: str, namespace: str) -> bool:
        """
        Force terminates a job (Cancellation / Pause).
        """
        logger.info(f"Terminating K8s Job: {job_name}")
        return True

k8s_job_manager = KubernetesJobManager()
