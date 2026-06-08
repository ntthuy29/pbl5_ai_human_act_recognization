"""
Script để update checkpoint hiện tại với standardizers.

Cách dùng:
  python update_checkpoint.py --checkpoint models/lstmcnn.pt --data train_data.npy --output models/lstmcnn_updated.pt

Hoặc dùng trong code:
  from utils.checkpoint_utils import update_checkpoint_with_standardizers
  import numpy as np
  
  # Giả sử bạn có training data
  train_data = np.load("train_data.npy")  # shape: (n_samples * n_time, feature_dim)
  mu = train_data.mean(axis=0)
  sigma = train_data.std(axis=0)
  max_abs = np.max(np.abs(train_data))
  
  update_checkpoint_with_standardizers(
      checkpoint_path="models/lstmcnn.pt",
      standardizer_mu=mu,
      standardizer_sigma=sigma,
      global_max_abs=max_abs,
      output_path="models/lstmcnn_updated.pt"
  )
"""

import argparse
import numpy as np
from pathlib import Path
from utils.checkpoint_utils import update_checkpoint_with_standardizers


def main():
    parser = argparse.ArgumentParser(
        description="Update checkpoint với standardizers từ training data"
    )
    parser.add_argument(
        "--checkpoint",
        required=True,
        help="Path checkpoint cũ (e.g., models/lstmcnn.pt)"
    )
    parser.add_argument(
        "--data",
        required=True,
        help="Path training data (numpy .npy file, shape: (n_samples, feature_dim))"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path save checkpoint mới (default: ghi đè checkpoint cũ)"
    )
    
    args = parser.parse_args()
    
    # Check files exist
    if not Path(args.checkpoint).exists():
        print(f"✗ Checkpoint not found: {args.checkpoint}")
        return
    
    if not Path(args.data).exists():
        print(f"✗ Data file not found: {args.data}")
        return
    
    print("=" * 60)
    print("UPDATING CHECKPOINT WITH STANDARDIZERS")
    print("=" * 60)
    
    # Load training data
    print(f"\n[STEP 1] Loading training data from {args.data}...")
    try:
        data = np.load(args.data).astype(np.float32)
        print(f"  ✓ Loaded shape: {data.shape}")
        
        if data.ndim == 3:  # (n_samples, time, features)
            n_samples, n_time, n_features = data.shape
            data = data.reshape(n_samples * n_time, n_features)
            print(f"  ℹ️  Reshaped from {(n_samples, n_time, n_features)} → {data.shape}")
        
    except Exception as e:
        print(f"  ✗ Failed to load data: {e}")
        return
    
    # Compute standardizers
    print(f"\n[STEP 2] Computing standardizers...")
    mu = np.mean(data, axis=0).astype(np.float32)
    sigma = np.std(data, axis=0).astype(np.float32)
    global_max_abs = float(np.max(np.abs(data)))
    
    print(f"  ✓ standardizer_mu: shape {mu.shape}, sample: {mu[:5]}")
    print(f"  ✓ standardizer_sigma: shape {sigma.shape}, sample: {sigma[:5]}")
    print(f"  ✓ global_max_abs: {global_max_abs:.6f}")
    
    # Update checkpoint
    print(f"\n[STEP 3] Updating checkpoint...")
    output_path = args.output or args.checkpoint
    try:
        update_checkpoint_with_standardizers(
            checkpoint_path=args.checkpoint,
            standardizer_mu=mu,
            standardizer_sigma=sigma,
            global_max_abs=global_max_abs,
            output_path=output_path,
        )
    except Exception as e:
        print(f"  ✗ Failed to update checkpoint: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✓ Checkpoint updated successfully!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"  1. Verify checkpoint: python be/check_model.py")
    print(f"  2. Restart backend to load new checkpoint")
    print(f"  3. Test predictions: curl http://localhost:8000/api/status")


if __name__ == "__main__":
    main()
