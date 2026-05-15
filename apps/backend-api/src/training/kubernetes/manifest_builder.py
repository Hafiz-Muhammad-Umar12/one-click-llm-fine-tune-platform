from typing import Dict, Any, List

class KubernetesManifestBuilder:
    """
    Builds Kubernetes Job manifests dynamically based on training requirements.
    """
    def __init__(self, namespace: str = "tenant-workloads"):
        self.namespace = namespace

    def build_job_manifest(
        self, 
        job_id: str, 
        command: List[str], 
        env_vars: Dict[str, str], 
        gpu_type: str, 
        gpu_count: int,
        docker_image: str = "ai-platform-worker:latest"
    ) -> Dict[str, Any]:
        """
        Constructs the K8s Job YAML (as a Python Dict) for submission.
        """
        # Format env vars for K8s
        k8s_env = [{"name": k, "value": str(v)} for k, v in env_vars.items()]

        manifest = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": f"train-job-{job_id[:8]}",
                "namespace": self.namespace,
                "labels": {
                    "app": "ai-platform-worker",
                    "job_id": job_id
                }
            },
            "spec": {
                "backoffLimit": 2, # Number of retries before marking as Failed
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "ai-platform-worker",
                            "job_id": job_id
                        }
                    },
                    "spec": {
                        "restartPolicy": "Never",
                        # Node Selector enforces execution on specific GPU hardware
                        "nodeSelector": {
                            "node.kubernetes.io/instance-type": gpu_type 
                        },
                        "containers": [
                            {
                                "name": "training-worker",
                                "image": docker_image,
                                "imagePullPolicy": "Always",
                                "command": command,
                                "env": k8s_env,
                                "resources": {
                                    "limits": {
                                        "nvidia.com/gpu": gpu_count,
                                        # "memory": "64Gi",
                                        # "cpu": "16"
                                    }
                                },
                                # Mount shared volume for checkpoints
                                "volumeMounts": [
                                    {
                                        "name": "checkpoint-vol",
                                        "mountPath": "/checkpoints"
                                    }
                                ]
                            }
                        ],
                        "volumes": [
                            {
                                "name": "checkpoint-vol",
                                "emptyDir": {} # In production, use a PersistentVolumeClaim
                            }
                        ]
                    }
                }
            }
        }
        return manifest
