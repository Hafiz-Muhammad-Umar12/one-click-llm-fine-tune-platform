import logging
from typing import Dict, Any, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class KubernetesDeploymentOrchestrator:
    """
    Manages the lifecycle of Inference Endpoints on Kubernetes.
    Handles Deployment, Service, and HPA resources.
    """
    def __init__(self):
        try:
            config.load_incluster_config()
            self.offline = False
        except config.ConfigException:
            try:
                config.load_kube_config()
                self.offline = False
            except config.ConfigException:
                logger.warning("K8s config not found. Deployment integration will run in mock mode.")
                self.offline = True
                
        if not self.offline:
            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
            self.autoscaling_v2 = client.AutoscalingV2Api()

    async def deploy_endpoint(self, endpoint_id: str, image: str, command: list, replicas: int, gpu_count: int, autoscaling_config: Optional[dict] = None):
        """
        Creates or updates a K8s Deployment, Service, and KEDA ScaledObject.
        """
        if self.offline:
            logger.info(f"[MOCK] Deploying Endpoint with KEDA: {endpoint_id}")
            return f"svc-{endpoint_id}"

        namespace = "default"
        name = f"inference-{endpoint_id}"

        # 1. Container & Deployment (same as before)
        container = client.V1Container(
            name="inference-server",
            image=image,
            command=command,
            ports=[client.V1ContainerPort(container_port=8000)],
            resources=client.V1ResourceRequirements(
                limits={"nvidia.com/gpu": str(gpu_count)},
                requests={"nvidia.com/gpu": str(gpu_count)}
            )
        )

        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1DeploymentSpec(
                replicas=replicas,
                selector=client.V1LabelSelector(match_labels={"app": name}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": name}),
                    spec=client.V1PodSpec(containers=[container])
                )
            )
        )

        # 2. KEDA ScaledObject (CRD)
        # Scale to zero based on Prometheus metrics (e.g., active requests)
        scaled_object = {
            "apiVersion": "keda.sh/v1alpha1",
            "kind": "ScaledObject",
            "metadata": {"name": f"{name}-scaler", "namespace": namespace},
            "spec": {
                "scaleTargetRef": {"name": name},
                "minReplicaCount": autoscaling_config.get("min_replicas", 0) if autoscaling_config else 0,
                "maxReplicaCount": autoscaling_config.get("max_replicas", 3) if autoscaling_config else 3,
                "triggers": [
                    {
                        "type": "prometheus",
                        "metadata": {
                            "serverAddress": "http://prometheus-operated.monitoring.svc.cluster.local:9090",
                            "metricName": "inference_active_requests",
                            "query": f'sum(inference_active_requests{{app="{name}"}})',
                            "threshold": "1"
                        }
                    }
                ]
            }
        }

        # 3. Apply Resources
        try:
            self.apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
            self.core_v1.create_namespaced_service(
                namespace=namespace, 
                body=client.V1Service(
                    metadata=client.V1ObjectMeta(name=name),
                    spec=client.V1ServiceSpec(selector={"app": name}, ports=[client.V1ServicePort(port=80, target_port=8000)])
                )
            )
            
            # Apply KEDA ScaledObject via CustomObjectsApi
            custom_api = client.CustomObjectsApi()
            custom_api.create_namespaced_custom_object(
                group="keda.sh", version="v1alpha1", namespace=namespace, plural="scaledobjects", body=scaled_object
            )
            
            return name
        except ApiException as e:
            if e.status == 409:
                return name
            raise

k8s_deployer = KubernetesDeploymentOrchestrator()
