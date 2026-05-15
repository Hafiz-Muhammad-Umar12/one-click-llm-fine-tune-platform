import math
import logging
from typing import Dict, Any
from opentelemetry import trace
from src.datasets.schemas.economics import EconomicEstimate

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class GPUCostEstimator:
    """
    High-fidelity economic engine for AI infrastructure.
    Estimates VRAM, GPU requirements, and training costs based on dataset metrics.
    """
    # Industry standard estimates (AWS/GCP approximation)
    GPU_SPECS = {
        "NVIDIA_L4": {"vram_gb": 24, "cost_per_hour": 0.80, "tflops": 242, "memory_bw": 300},
        "NVIDIA_A10G": {"vram_gb": 24, "cost_per_hour": 1.20, "tflops": 125, "memory_bw": 600}, 
        "NVIDIA_A100_40GB": {"vram_gb": 40, "cost_per_hour": 3.50, "tflops": 312, "memory_bw": 1555},
        "NVIDIA_A100_80GB": {"vram_gb": 80, "cost_per_hour": 5.00, "tflops": 624, "memory_bw": 2039},
        "NVIDIA_H100_80GB": {"vram_gb": 80, "cost_per_hour": 8.00, "tflops": 1979, "memory_bw": 3350}
    }

    # Approximate parameters for popular base models
    KNOWN_MODELS = {
        "meta-llama/Llama-3-8b": 8.0,
        "mistralai/Mistral-7B-v0.1": 7.3,
        "google/gemma-7b": 8.5,
        "Qwen/Qwen1.5-7B": 7.7,
        "meta-llama/Llama-2-13b": 13.0,
        "meta-llama/Llama-2-70b": 70.0,
    }

    def estimate(
        self, 
        total_tokens: int, 
        max_seq_length: int, 
        base_model: str = "meta-llama/Llama-3-8b", 
        epochs: int = 3,
        method: str = "qlora"
    ) -> EconomicEstimate:
        
        with tracer.start_as_current_span("economic_estimation") as span:
            
            model_params_billions = self.KNOWN_MODELS.get(base_model, 8.0) # default to 8B
            span.set_attribute("model_params", model_params_billions)
            span.set_attribute("total_tokens", total_tokens)
            
            # Prevent extreme values from causing math errors
            total_tokens = min(total_tokens, 100_000_000_000)
            max_seq_length = min(max_seq_length, 32768)

            # 1. VRAM Estimation (Precise Heuristics)
            if method == "qlora":
                # 4-bit weights = 0.5 bytes per param. LoRA weights = small overhead. Gradients/States = 1.5 bytes per param.
                # Simplification: ~0.7GB per 1B params
                vram_base = model_params_billions * 0.7  
                # Activations scale with sequence length (FlashAttention helps, but still O(N))
                vram_activation = (max_seq_length / 1024) * (model_params_billions / 8.0) * 1.5 
                estimated_vram_gb = vram_base + vram_activation
            elif method == "lora":
                vram_base = model_params_billions * 2.2 # 16-bit base model
                vram_activation = (max_seq_length / 1024) * (model_params_billions / 8.0) * 1.5 
                estimated_vram_gb = vram_base + vram_activation
            else:
                # Full fine-tuning (16-bit)
                vram_base = model_params_billions * 16 # Adam optimizer states are huge
                vram_activation = (max_seq_length / 1024) * (model_params_billions / 8.0) * 6
                estimated_vram_gb = vram_base + vram_activation

            # 2. Select Recommended GPU
            recommended_gpu = "NVIDIA_H100_80GB" # Default to largest if everything fails
            multi_gpu_required = False
            
            if estimated_vram_gb > 75:
                multi_gpu_required = True
                recommended_gpu = "NVIDIA_A100_80GB" # Will need a node of 8x A100s
            else:
                # Find smallest GPU that fits the VRAM with a 20% safety buffer
                for gpu_name, specs in sorted(self.GPU_SPECS.items(), key=lambda x: x[1]["vram_gb"]):
                    if specs["vram_gb"] > (estimated_vram_gb * 1.2): 
                        recommended_gpu = gpu_name
                        break

            # 3. Time Estimation (Using standard MFU curves)
            efficiency = 0.35 if method == "full" else 0.45 # QLoRA is actually slightly slower on some hardware, but let's assume 45% MFU
            
            # 6 FLOPs per param per token is the industry standard heuristic for forward+backward pass
            tflops_needed = total_tokens * epochs * (model_params_billions * 1e9) * 6
            gpu_tflops = self.GPU_SPECS[recommended_gpu]["tflops"] * 1e12
            
            tokens_per_second = (gpu_tflops * efficiency) / ((model_params_billions * 1e9) * 6)
            
            # Multi-GPU speedup (assuming 8x node if multi is required, with 0.85 scaling efficiency)
            if multi_gpu_required:
                tokens_per_second *= (8 * 0.85)

            duration_seconds = (total_tokens * epochs) / max(tokens_per_second, 1.0)
            duration_hours = max(duration_seconds / 3600, 0.1) # Minimum 6 minutes for container spinup overhead

            # 4. Cost Calculation
            hourly_rate = self.GPU_SPECS[recommended_gpu]["cost_per_hour"]
            if multi_gpu_required:
                hourly_rate *= 8 # Cost of an 8x Node
                
            total_cost = duration_hours * hourly_rate

            # 5. Batch Size Recommendation
            # Batch size is bounded by leftover VRAM
            available_vram = self.GPU_SPECS[recommended_gpu]["vram_gb"] if not multi_gpu_required else self.GPU_SPECS[recommended_gpu]["vram_gb"] * 8
            leftover = available_vram - estimated_vram_gb
            
            if leftover > 20:
                suggested_batch_size = 16
                grad_acc = 1
            elif leftover > 10:
                suggested_batch_size = 8
                grad_acc = 2
            else:
                suggested_batch_size = 4
                grad_acc = 4

            span.set_attribute("estimated_cost", total_cost)
            span.set_attribute("recommended_gpu", recommended_gpu)

            return EconomicEstimate(
                estimated_vram_gb=round(estimated_vram_gb, 2),
                recommended_gpu=recommended_gpu,
                estimated_duration_hours=round(duration_hours, 2),
                estimated_cost_usd=round(total_cost, 2),
                suggested_batch_size=suggested_batch_size,
                gradient_accumulation_steps=grad_acc,
                multi_gpu_required=multi_gpu_required,
                assumptions={
                    "model_params_billions": model_params_billions,
                    "tokens_per_second": round(tokens_per_second, 2),
                    "mfu": efficiency
                }
            )
