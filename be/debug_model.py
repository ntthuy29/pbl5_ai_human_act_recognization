"""
Debug script để diagnose model prediction issues.
Chạy: python debug_model.py
"""
import torch
import numpy as np
from pathlib import Path
from models.model import LstmCnnClassifier
from app.services.preprocess_service import PreprocessService

print("=" * 60)
print("MODEL DIAGNOSIS")
print("=" * 60)

# Step 1: Check checkpoint
print("\n[STEP 1] Loading checkpoint...")
model_path = "models/lstmcnn.pt"
try:
    ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
    print(f"✓ Checkpoint loaded from {model_path}")
    print(f"  Keys: {list(ckpt.keys())}")
except Exception as e:
    print(f"✗ Failed to load checkpoint: {e}")
    exit(1)

# Step 2: Extract metadata
print("\n[STEP 2] Extracting metadata...")
input_shape = ckpt.get("input_shape", (128, 30))  # default window_size=128, feature_dim=30
num_classes = ckpt.get("num_classes", 3)
class_names = ckpt.get("class_names", ["person", "no_person"])
feature_dim = input_shape[-1] if isinstance(input_shape, (tuple, list)) else 30

print(f"  input_shape: {input_shape}")
print(f"  num_classes: {num_classes}")
print(f"  class_names: {class_names}")
print(f"  feature_dim: {feature_dim}")

# Step 3: Check standardizers
print("\n[STEP 3] Checking standardizers (CRITICAL)...")
has_mu = "standardizer_mu" in ckpt
has_sigma = "standardizer_sigma" in ckpt
has_max = "global_max_abs" in ckpt

print(f"  standardizer_mu: {'✓' if has_mu else '✗'}")
if has_mu:
    print(f"    shape: {ckpt['standardizer_mu'].shape}")
    print(f"    sample values: {ckpt['standardizer_mu'][:5]}")

print(f"  standardizer_sigma: {'✓' if has_sigma else '✗'}")
if has_sigma:
    print(f"    shape: {ckpt['standardizer_sigma'].shape}")
    print(f"    sample values: {ckpt['standardizer_sigma'][:5]}")

print(f"  global_max_abs: {'✓' if has_max else '✗'}")
if has_max:
    print(f"    value: {ckpt['global_max_abs']}")

if not (has_mu and has_sigma and has_max):
    print(f"\n  ⚠️  WARNING: Standardizers missing! This WILL cause prediction mismatch.")
    print(f"     → Preprocessing will only use Hampel + Butterworth (no per-axis normalization)")
    print(f"     → Model was likely trained WITH standardizers but inference WITHOUT")
    print(f"     → SOLUTION: Retrain model and save standardizers to checkpoint")

# Step 4: Load model
print("\n[STEP 4] Loading model architecture...")
try:
    state_dict = ckpt.get("state_dict") or ckpt.get("model_state_dict") or ckpt
    model = LstmCnnClassifier(feature_dim=feature_dim, num_classes=num_classes)
    model.load_state_dict(state_dict)
    model.eval()
    print(f"✓ Model loaded successfully")
except Exception as e:
    print(f"✗ Failed to load model: {e}")
    exit(1)

# Step 5: Create dummy window and test inference
print("\n[STEP 5] Testing inference with dummy data...")
dummy_window = np.random.randn(input_shape[0], feature_dim).astype(np.float32)
print(f"  Dummy window shape: {dummy_window.shape}")
print(f"  Mean: {dummy_window.mean():.6f}, Std: {dummy_window.std():.6f}")
print(f"  Min: {dummy_window.min():.6f}, Max: {dummy_window.max():.6f}")

# Test preprocessing
print("\n[STEP 5a] Preprocessing...")
try:
    if has_mu and has_sigma and has_max:
        preproc = PreprocessService(
            standardizer_mu=ckpt["standardizer_mu"],
            standardizer_sigma=ckpt["standardizer_sigma"],
            global_max_abs=ckpt["global_max_abs"],
        )
        print(f"  Using FULL preprocessing (Hampel → Butterworth → Standardizer → GlobalNorm)")
    else:
        preproc = PreprocessService()
        print(f"  Using BASE preprocessing (Hampel → Butterworth ONLY)")
    
    processed = preproc.process(dummy_window)
    print(f"  ✓ Processed window shape: {processed.shape}")
    print(f"    Mean: {processed.mean():.6f}, Std: {processed.std():.6f}")
    print(f"    Min: {processed.min():.6f}, Max: {processed.max():.6f}")
except Exception as e:
    print(f"  ✗ Preprocessing failed: {e}")
    exit(1)

# Test model predict
print("\n[STEP 5b] Model inference...")
try:
    x = torch.tensor(processed, dtype=torch.float32)
    if x.ndim == 2:
        x = x.unsqueeze(0)  # Add batch dim
    
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=-1).numpy()[0]
    
    idx = int(np.argmax(probs))
    presence = class_names[idx]
    confidence = float(probs[idx])
    
    print(f"  ✓ Inference successful")
    print(f"    Detected presence: {presence}")
    print(f"    Confidence: {confidence:.4f}")
    print(f"    Probabilities:")
    for i, name in enumerate(class_names):
        print(f"      {name}: {probs[i]:.6f}")
except Exception as e:
    print(f"  ✗ Inference failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 6: Recommendations
print("\n" + "=" * 60)
print("RECOMMENDATIONS")
print("=" * 60)

if not (has_mu and has_sigma and has_max):
    print("🔴 CRITICAL ISSUE: Standardizers missing from checkpoint")
    print("   Action: Retrain model with standardizers and update checkpoint")
    print("   Likelihood of detection errors: VERY HIGH")
else:
    print("✓ Checkpoint contains all standardizers")
    print("✓ Model loaded successfully")
    print("✓ Inference pipeline works")
    print("\nIf predictions are still wrong:")
    print("  1. Check ESP32 sensor data (are values reasonable?)")
    print("  2. Verify FEATURE_DIM matches (run /api/status)")
    print("  3. Check if training data distribution changed")
    print("  4. Try retraining with current sensor data")

print("\n" + "=" * 60)
