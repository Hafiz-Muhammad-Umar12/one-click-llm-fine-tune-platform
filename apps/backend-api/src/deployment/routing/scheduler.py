import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class HardwareTier(BaseModel):
    name: str
    gpu_type: str
    gpu_count: int
    vram_per_gpu_gb: float
    cpu_cores: int
    memory_gb: int

# Standard Tiers
HARDWARE_TIERS = {
    "nvidia-l4-1x": HardwareTier(name="nvidia-l4-1x", gpu_type="L4", gpu_count=1, vram_per_gpu_gb=24, cpu_cores=4, memory_gb=16),
    "nvidia-a10g-1x": HardwareTier(name="nvidia-a10g-1x", gpu_type="A10G", gpu_count=1, vram_per_gpu_gb=24, cpu_cores=4, memory_gb=24),
    "nvidia-a100-40gb-1x": HardwareTier(name="nvidia-a100-40gb-1x", gpu_type="A100", gpu_count=1, vram_per_gpu_gb=40, cpu_cores=8, memory_gb=64),
    "nvidia-a100-80gb-1x": HardwareTier(name="nvidia-a100-80gb-1x", gpu_type="A100", gpu_count=1, vram_per_gpu_gb=80, cpu_cores=12, memory_gb=96),
    "nvidia-a100-80gb-4x": HardwareTier(name="nvidia-a100-80gb-4x", gpu_type="A100", gpu_count=4, vram_per_gpu_gb=80, cpu_cores=48, memory_gb=384),
}

class GPUScheduler:
    """
    Handles hardware tier selection and VRAM-aware scheduling logic.
    In a real system, this would also interface with K8s node capacity.
    """
    def validate_tier(self, tier_name: str) -> bool:
        return tier_name in HARDWARE_TIERS

    def get_tier_config(self, tier_name: str) -> HardwareTier:
        return HARDWARE_TIERS.get(tier_name)

    def calculate_tensor_parallelism(self, model_size_gb: float, tier_name: str) -> int:
        """
        Calculates required TP size based on model size and available VRAM.
        """
        tier = self.get_tier_config(tier_name)
        if not tier:
            return 1
            
        # Add 20% overhead for KV cache and activations
        required_vram = model_size_gb * 1.2
        
        # If model fits in 1 GPU, TP=1
        if required_vram <= tier.vram_per_gpu_gb:
            return 1
            
        # Otherwise, split across available GPUs
        needed_gpus = int(required_vram // tier.vram_per_gpu_gb) + 1
        
        if needed_gpus > tier.gpu_count:
            logger.warning(f"Model ({model_size_gb}GB) might not fit on {tier_name}")
            return tier.gpu_count
            
        return needed_gpus

gpu_scheduler = GPUScheduler()
