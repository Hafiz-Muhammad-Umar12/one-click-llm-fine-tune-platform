import logging
from typing import Dict, Any, Optional
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from src.training.kubernetes.manifest_builder import KubernetesManifestBuilder

logger = logging.getLogger(__name__)

class KubernetesJobManager:
    """
    Interfaces with the Kubernetes API to orchestrate Training Jobs.
    Uses the official kubernetes-python client.
    """
    def __init__(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            try:
                config.load_kube_config()
            except config.ConfigException:
                logger.warning("Could not load K8s config. Integration will run in offline/mock mode.")
                self.offline = True
            else:
                self.offline = False
        else:
            self.offline = False
            
        self.batch_v1 = client.BatchV1Api() if not getattr(self, 'offline', True) else None
        self.manifest_builder = KubernetesManifestBuilder()
        
    async def submit_job(self, manifest: Dict[str, Any], namespace: str = "default") -> str:
        """
        Submits the manifest to the K8s API server.
        """
        if self.offline:
            logger.info(f"[MOCK] Submitting Job: {manifest['metadata']['name']}")
            return manifest["metadata"]["name"]

        try:
            api_response = self.batch_v1.create_namespaced_job(
                body=manifest,
                namespace=namespace
            )
            return api_response.metadata.name
        except ApiException as e:
            logger.error(f"K8s API Exception: {e}")
            raise

    async def get_job_status(self, job_name: str, namespace: str) -> str:
        """
        Queries the K8s API to determine the state of the job.
        """
        if self.offline:
            return "running"

        try:
            job = self.batch_v1.read_namespaced_job_status(name=job_name, namespace=namespace)
            if job.status.succeeded:
                return "completed"
            if job.status.failed:
                return "failed"
            return "running"
        except ApiException:
            return "unknown"
        
    async def delete_job(self, job_name: str, namespace: str) -> bool:
        """
        Force terminates a job.
        """
        if self.offline:
            return True

        try:
            self.batch_v1.delete_namespaced_job(
                name=job_name,
                namespace=namespace,
                propagation_policy='Background'
            )
            return True
        except ApiException:
            return False

k8s_job_manager = KubernetesJobManager()
