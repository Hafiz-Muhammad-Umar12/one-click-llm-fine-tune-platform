import os
import requests
from typing import Optional, Dict, Any, List
from tqdm import tqdm

class AIPlatformClient:
    """
    Python SDK for interacting with the AI Fine-Tuning Platform.
    """
    def __init__(self, api_key: str, base_url: str = "https://api.platform.com/api/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response.json()

    # Datasets
    def upload_dataset(self, file_path: str, name: str) -> Dict[str, Any]:
        """
        Uploads a local file to the platform as a dataset.
        """
        # 1. Get Presigned URL
        file_size = os.path.getsize(file_path)
        payload = {"name": name, "file_size": file_size}
        res = self._request("POST", "/datasets", json=payload)
        
        upload_url = res["upload_url"]
        dataset_id = res["id"]
        
        # 2. Upload to S3 directly
        print(f"Uploading {name} ({file_size / 1024 / 1024:.2f} MB)...")
        with open(file_path, 'rb') as f:
            upload_res = requests.put(upload_url, data=f)
            upload_res.raise_for_status()
            
        # 3. Notify backend of completion
        self._request("PUT", f"/datasets/{dataset_id}/status", json={"status": "uploaded"})
        return {"id": dataset_id, "status": "processing"}

    def list_datasets(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/datasets")

    # Training
    def create_training_job(
        self, 
        dataset_id: str, 
        base_model: str, 
        hyperparameters: Dict[str, Any],
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            "name": name,
            "dataset_id": dataset_id,
            "base_model": base_model,
            "hyperparameters": hyperparameters
        }
        return self._request("POST", "/training/jobs", json=payload)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/training/jobs/{job_id}")

    # Deployments
    def deploy_model(self, model_version_id: str, hardware_tier: str) -> Dict[str, Any]:
        payload = {
            "model_version_id": model_version_id,
            "hardware_tier": hardware_tier
        }
        return self._request("POST", "/deployments", json=payload)

    # Inference (OpenAI Compatible)
    def chat_completion(self, endpoint_id: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        payload = {
            "messages": messages,
            **kwargs
        }
        return self._request("POST", f"/inference/{endpoint_id}/completions", json=payload)
