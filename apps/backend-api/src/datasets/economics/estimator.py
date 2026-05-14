import math
from typing import Dict, Any

class GPUCostEstimator:
    """
    High-fidelity economic engine for AI infrastructure.
    Estimates VRAM, GPU requirements, and training costs based on dataset metrics.
    """
    GPU_SPECS = {
        "NVIDIA_L4": {"vram_gb": 24, "cost_per_hour": 0.70, "tflops": 242},
        "NVIDIA_A10G": {"vram_gb": 24, "cost_per_hour": 1.00, "tflops": 31.2}, # FP32
        "NVIDIA_A100_40GB": {"vram_gb": 40, "cost_per_hour": 3.00, "tflops": 312},
        "NVIDIA_A100_80GB": {"vram_gb": 80, "cost_per_hour": 4.50, "tflops": 624},
        "NVIDIA_H100_80GB": {"vram_gb": 80, "cost_per_hour": 6.00, "tflops": 1979}
    }

    def estimate(
        self, 
        total_tokens: int, 
        max_seq_length: int, 
        model_params_billions: float = 8.0, 
        epochs: int = 3,
        method: str = "qlora"
    ) -> Dict[str, Any]:
        """
        Calculates expected training resources.
        """
        # 1. VRAM Estimation (Simplified heuristic)
        # Model weights (4-bit QLoRA) + Gradients + Optimizer states + Activations
        if method == "qlora":
            vram_base = model_params_billions * 0.7  # ~0.7GB per 1B params in 4-bit
            vram_activation = (max_seq_length / 1024) * 2.0 # Roughly 2GB per 1k context
            estimated_vram_gb = vram_base + vram_activation
        else:
            # Full fine-tuning (16-bit)
            estimated_vram_gb = model_params_billions * 4 + (max_seq_length / 1024) * 8

        # 2. Select Recommended GPU
        recommended_gpu = "NVIDIA_L4"
        for gpu_name, specs in self.GPU_SPECS.items():
            if specs["vram_gb"] > (estimated_vram_gb + 4): # 4GB buffer
                recommended_gpu = gpu_name
                break

        # 3. Time Estimation
        # Tokens / (TFLOPS * efficiency_constant)
        efficiency = 0.3 # 30% MFU
        tflops_needed = total_tokens * epochs * model_params_billions * 6 # 6 FLOPs per param per token
        gpu_tflops = self.GPU_SPECS[recommended_gpu]["tflops"] * 10**12
        
        # Simple heuristic for duration
        tokens_per_second = (gpu_tflops * efficiency) / (model_params_billions * 10**9 * 6)
        duration_seconds = (total_tokens * epochs) / tokens_per_second
        duration_hours = duration_seconds / 3600

        # 4. Cost Calculation
        total_cost = duration_hours * self.GPU_SPECS[recommended_gpu]["cost_per_hour"]

        return {
            "estimated_vram_gb": round(estimated_vram_gb, 2),
            "recommended_gpu": recommended_gpu,
            "estimated_duration_hours": round(duration_hours, 2),
            "estimated_cost_usd": round(total_cost, 2),
            "suggested_batch_size": 4 if estimated_vram_gb < 20 else 16,
            "gradient_accumulation_steps": 4
        }
