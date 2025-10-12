"""
Model Compression Module
Techniques to reduce model size and improve inference speed.
"""

import logging
from typing import Dict, Optional, Any
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelCompressor:
    """Model compression techniques"""
    
    def __init__(self):
        """Initialize model compressor"""
        self.compression_history: list = []
    
    def quantize_weights(
        self,
        weights: Dict[str, Any],
        bits: int = 8
    ) -> Dict[str, Any]:
        """
        Quantize model weights to reduce precision.
        
        Args:
            weights: Model weights dictionary
            bits: Target bit precision (8, 16)
            
        Returns:
            Quantized weights dictionary
        """
        logger.info(f"Quantizing weights to {bits}-bit precision")
        
        quantized = {}
        original_size = 0
        compressed_size = 0
        
        for key, value in weights.items():
            if isinstance(value, (list, tuple)):
                # Simulate quantization
                if bits == 8:
                    quantized[key] = [int(v * 127) / 127 for v in value]
                    compressed_size += len(value) * 1  # 1 byte per value
                elif bits == 16:
                    quantized[key] = [int(v * 32767) / 32767 for v in value]
                    compressed_size += len(value) * 2  # 2 bytes per value
                
                original_size += len(value) * 4  # Original float32 = 4 bytes
            else:
                quantized[key] = value
        
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 1
        
        result = {
            "quantized_weights": quantized,
            "bits": bits,
            "original_size_bytes": original_size,
            "compressed_size_bytes": compressed_size,
            "compression_ratio": compression_ratio,
            "size_reduction_percent": (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        }
        
        self.compression_history.append({
            "technique": "quantization",
            "bits": bits,
            "compression_ratio": compression_ratio
        })
        
        logger.info(f"✅ Quantization complete: {compression_ratio:.2f}x compression")
        
        return result
    
    def prune_weights(
        self,
        weights: Dict[str, Any],
        threshold: float = 0.01
    ) -> Dict[str, Any]:
        """
        Prune small weights (set to zero).
        
        Args:
            weights: Model weights dictionary
            threshold: Absolute threshold for pruning
            
        Returns:
            Pruned weights dictionary
        """
        logger.info(f"Pruning weights with threshold {threshold}")
        
        pruned = {}
        original_params = 0
        remaining_params = 0
        
        for key, value in weights.items():
            if isinstance(value, (list, tuple)):
                pruned[key] = [v if abs(v) > threshold else 0 for v in value]
                original_params += len(value)
                remaining_params += sum(1 for v in pruned[key] if v != 0)
            else:
                pruned[key] = value
        
        sparsity = (original_params - remaining_params) / original_params * 100 if original_params > 0 else 0
        
        result = {
            "pruned_weights": pruned,
            "threshold": threshold,
            "original_params": original_params,
            "remaining_params": remaining_params,
            "pruned_params": original_params - remaining_params,
            "sparsity_percent": sparsity
        }
        
        self.compression_history.append({
            "technique": "pruning",
            "threshold": threshold,
            "sparsity_percent": sparsity
        })
        
        logger.info(f"✅ Pruning complete: {sparsity:.1f}% sparsity")
        
        return result
    
    def knowledge_distillation_config(
        self,
        teacher_model_id: str,
        student_model_id: str,
        temperature: float = 3.0,
        alpha: float = 0.5
    ) -> Dict[str, Any]:
        """
        Generate knowledge distillation configuration.
        
        Args:
            teacher_model_id: Teacher (large) model ID
            student_model_id: Student (small) model ID
            temperature: Distillation temperature
            alpha: Balance between hard and soft targets
            
        Returns:
            Distillation configuration
        """
        config = {
            "technique": "knowledge_distillation",
            "teacher_model": teacher_model_id,
            "student_model": student_model_id,
            "temperature": temperature,
            "alpha": alpha,
            "loss_function": f"alpha * hard_loss + (1-alpha) * distillation_loss",
            "instructions": [
                "1. Train teacher model to convergence",
                "2. Generate soft targets from teacher using temperature",
                "3. Train student model using combined loss",
                "4. Evaluate student model performance"
            ]
        }
        
        logger.info(
            f"Created distillation config: {teacher_model_id} -> {student_model_id}"
        )
        
        return config
    
    def get_compression_report(self) -> Dict[str, Any]:
        """Get compression history report"""
        if not self.compression_history:
            return {"message": "No compression operations performed"}
        
        techniques = {}
        for entry in self.compression_history:
            tech = entry["technique"]
            if tech not in techniques:
                techniques[tech] = []
            techniques[tech].append(entry)
        
        return {
            "total_operations": len(self.compression_history),
            "techniques_used": list(techniques.keys()),
            "by_technique": techniques
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("MODEL COMPRESSION DEMO")
    print("=" * 80)
    
    compressor = ModelCompressor()
    
    # Mock model weights
    mock_weights = {
        "layer1": [0.5, 0.3, -0.2, 0.8, 0.005, -0.003, 0.6],
        "layer2": [-0.4, 0.9, 0.001, -0.7, 0.2, 0.004, -0.1],
        "bias": [0.1, -0.05, 0.02]
    }
    
    # Weight Quantization
    print("\n" + "=" * 80)
    print("WEIGHT QUANTIZATION")
    print("=" * 80)
    
    quant_8bit = compressor.quantize_weights(mock_weights, bits=8)
    print(f"\n8-bit Quantization:")
    print(f"  Original Size: {quant_8bit['original_size_bytes']} bytes")
    print(f"  Compressed Size: {quant_8bit['compressed_size_bytes']} bytes")
    print(f"  Compression Ratio: {quant_8bit['compression_ratio']:.2f}x")
    print(f"  Size Reduction: {quant_8bit['size_reduction_percent']:.1f}%")
    
    quant_16bit = compressor.quantize_weights(mock_weights, bits=16)
    print(f"\n16-bit Quantization:")
    print(f"  Compression Ratio: {quant_16bit['compression_ratio']:.2f}x")
    print(f"  Size Reduction: {quant_16bit['size_reduction_percent']:.1f}%")
    
    # Weight Pruning
    print("\n" + "=" * 80)
    print("WEIGHT PRUNING")
    print("=" * 80)
    
    pruned_strict = compressor.prune_weights(mock_weights, threshold=0.01)
    print(f"\nStrict Pruning (threshold=0.01):")
    print(f"  Original Params: {pruned_strict['original_params']}")
    print(f"  Remaining Params: {pruned_strict['remaining_params']}")
    print(f"  Pruned Params: {pruned_strict['pruned_params']}")
    print(f"  Sparsity: {pruned_strict['sparsity_percent']:.1f}%")
    
    pruned_aggressive = compressor.prune_weights(mock_weights, threshold=0.1)
    print(f"\nAggressive Pruning (threshold=0.1):")
    print(f"  Sparsity: {pruned_aggressive['sparsity_percent']:.1f}%")
    
    # Knowledge Distillation
    print("\n" + "=" * 80)
    print("KNOWLEDGE DISTILLATION")
    print("=" * 80)
    
    distill_config = compressor.knowledge_distillation_config(
        teacher_model_id="large_transformer_model",
        student_model_id="small_lstm_model",
        temperature=3.0,
        alpha=0.5
    )
    
    print(f"\nTeacher: {distill_config['teacher_model']}")
    print(f"Student: {distill_config['student_model']}")
    print(f"Temperature: {distill_config['temperature']}")
    print(f"Alpha (hard/soft balance): {distill_config['alpha']}")
    print(f"\nInstructions:")
    for instruction in distill_config['instructions']:
        print(f"  {instruction}")
    
    # Compression Report
    print("\n" + "=" * 80)
    print("COMPRESSION REPORT")
    print("=" * 80)
    
    report = compressor.get_compression_report()
    print(f"\nTotal Operations: {report['total_operations']}")
    print(f"Techniques Used: {', '.join(report['techniques_used'])}")
    
    print("\n" + "=" * 80)
    print("Model Compression Demo Complete!")
    print("=" * 80)

