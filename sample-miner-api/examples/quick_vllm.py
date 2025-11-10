#!/usr/bin/env python3
"""
Ultra-Simple vLLM Server - One Command Deployment
Deploys Llama 3.1 8B Instruct (Quantized) with minimal VRAM usage

Just run: python quick_vllm.py
"""

if __name__ == "__main__":
    import subprocess
    import sys
    
    # Configuration - Using quantized model for minimal VRAM
    MODEL = "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4"  # 4-bit quantized
    PORT = 8000
    MAX_MODEL_LEN = 8192  # Reasonable context length
    GPU_MEMORY_UTILIZATION = 0.9  # Use 90% of available GPU memory
    
    print(f"🚀 Starting vLLM server with quantized model...")
    print(f"📦 Model: {MODEL}")
    print(f"📍 Server will be at: http://localhost:{PORT}")
    print(f"📖 API docs at: http://localhost:{PORT}/docs")
    print(f"🔧 Max model length: {MAX_MODEL_LEN} tokens")
    print(f"💾 GPU memory utilization: {GPU_MEMORY_UTILIZATION * 100}%")
    print("⏸️  Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "vllm.entrypoints.openai.api_server",
            "--model", MODEL,
            "--host", "0.0.0.0",
            "--port", str(PORT),
            "--max-model-len", str(MAX_MODEL_LEN),
            "--gpu-memory-utilization", str(GPU_MEMORY_UTILIZATION),
            "--quantization", "awq",  # Use AWQ quantization
        ])
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
