"""
TRAINING SCRIPT TEMPLATE
Ví dụ: Làm sao training script nên save standardizers vào checkpoint.

Cách dùng:
  1. Thay thế các biến DEVICE, NUM_EPOCHS, ... tương ứng
  2. Load training data của bạn vào train_loader
  3. Huấn luyện model
  4. Save checkpoint với standardizers bằng checkpoint_utils.save_checkpoint()
"""

import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from utils.checkpoint_utils import (
    save_checkpoint,
    compute_standardizers_from_dataset,
)
from models.model import LstmCnnClassifier

# ====================== CONFIG ======================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
FEATURE_DIM = 30
WINDOW_SIZE = 128
NUM_CLASSES = 3
CLASS_NAMES = ["person", "no_person"]
NUM_EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 1e-3
SAVE_PATH = "models/lstmcnn.pt"

# Preprocessing parameters dùng khi train
PREPROCESSING_CONFIG = {
    "hampel_window": 5,
    "hampel_n_sigmas": 3.0,
    "butter_order": 4,
    "butter_cutoff": 0.1,
}

# ====================== SETUP ======================

def main():
    print("=" * 60)
    print("TRAINING SCRIPT TEMPLATE")
    print("=" * 60)
    
    # 1. Load training data
    print("\n[STEP 1] Loading training data...")
    # TODO: Thay thế bằng code load dữ liệu thực của bạn
    # Giả sử: train_loader là DataLoader với batch shape (batch, window_size, feature_dim)
    # Hoặc: train_loader là list của tuples (X, y)
    
    # PLACEHOLDER:
    train_loader = None  # TODO: Load từ file hoặc database
    if train_loader is None:
        print("  ⚠️  TODO: Implement data loading")
        print("  Expected format: DataLoader hoặc list[tuple(X_batch, y_batch)]")
        return
    
    # 2. Compute standardizers từ training data
    print("\n[STEP 2] Computing standardizers from training data...")
    try:
        standardizer_mu, standardizer_sigma, global_max_abs = compute_standardizers_from_dataset(train_loader)
    except Exception as e:
        print(f"  ✗ Error computing standardizers: {e}")
        print("  → Fallback: Use placeholder standardizers")
        standardizer_mu = np.ones(FEATURE_DIM, dtype=np.float32)
        standardizer_sigma = np.ones(FEATURE_DIM, dtype=np.float32)
        global_max_abs = 1.0
    
    # 3. Initialize model
    print("\n[STEP 3] Initializing model...")
    model = LstmCnnClassifier(feature_dim=FEATURE_DIM, num_classes=NUM_CLASSES)
    model.to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    print(f"  ✓ Model: {model.__class__.__name__}")
    print(f"    Feature dim: {FEATURE_DIM}")
    print(f"    Num classes: {NUM_CLASSES}")
    print(f"    Device: {DEVICE}")
    
    # 4. Training loop
    print("\n[STEP 4] Starting training...")
    for epoch in range(1, NUM_EPOCHS + 1):
        model.train()
        total_loss = 0
        num_batches = 0
        
        for batch_idx, batch in enumerate(train_loader):
            if isinstance(batch, (tuple, list)):
                X, y = batch
            else:
                X = batch
                y = None  # Unsupervised, skip loss
            
            if hasattr(X, "to"):
                X = X.to(DEVICE)
            if hasattr(y, "to"):
                y = y.to(DEVICE)
            
            # Forward
            logits = model(X)
            if y is not None:
                loss = criterion(logits, y)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                num_batches += 1
        
        if epoch % 10 == 0:
            avg_loss = total_loss / max(1, num_batches)
            print(f"  Epoch {epoch}/{NUM_EPOCHS}, Loss: {avg_loss:.4f}")
    
    print(f"  ✓ Training complete")
    
    # 5. Save checkpoint với standardizers
    print("\n[STEP 5] Saving checkpoint with standardizers...")
    save_checkpoint(
        model=model,
        optimizer=optimizer,
        epoch=NUM_EPOCHS,
        save_path=SAVE_PATH,
        input_shape=(WINDOW_SIZE, FEATURE_DIM),
        num_classes=NUM_CLASSES,
        class_names=CLASS_NAMES,
        standardizer_mu=standardizer_mu,
        standardizer_sigma=standardizer_sigma,
        global_max_abs=global_max_abs,
        training_config=PREPROCESSING_CONFIG,
    )
    
    print("\n" + "=" * 60)
    print("✓ Training complete and checkpoint saved")
    print("=" * 60)
    print(f"\nCheckpoint saved to: {SAVE_PATH}")
    print(f"The backend will now:")
    print(f"  1. Load standardizers from checkpoint automatically")
    print(f"  2. Apply full preprocessing pipeline in realtime")
    print(f"  3. Use consistent preprocessing between training and inference")


if __name__ == "__main__":
    main()
