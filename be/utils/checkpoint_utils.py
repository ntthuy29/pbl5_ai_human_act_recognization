"""
Utilities để save/load checkpoint với training parameters (standardizers, v.v.)
"""
import torch
import numpy as np
from pathlib import Path


def save_checkpoint(
    model,
    optimizer,
    epoch,
    save_path: str,
    input_shape: tuple,
    num_classes: int,
    class_names: list,
    standardizer_mu: np.ndarray = None,
    standardizer_sigma: np.ndarray = None,
    global_max_abs: float = None,
    training_config: dict = None,
):
    """
    Save checkpoint với đầy đủ training parameters.
    
    Args:
        model: PyTorch model
        optimizer: Training optimizer
        epoch: Epoch hiện tại
        save_path: Đường dẫn save checkpoint
        input_shape: Shape của input (e.g., (128, 30) = window_size x feature_dim)
        num_classes: Số class (e.g., 2 cho person/no_person)
        class_names: Danh sách tên class
        standardizer_mu: Mean của từng feature từ training data (shape: feature_dim,)
        standardizer_sigma: Std của từng feature từ training data (shape: feature_dim,)
        global_max_abs: Max absolute value của training data (dùng cho global normalization)
        training_config: Dict với các tham số training (hampel_window, butter_cutoff, v.v.)
    
    Example:
        >>> from app.services.model_service import model_service
        >>> save_checkpoint(
        ...     model=model_service.model,
        ...     optimizer=optimizer,
        ...     epoch=50,
        ...     save_path="models/lstmcnn_v2.pt",
        ...     input_shape=(128, 30),
        ...     num_classes=2,
        ...     class_names=["person", "no_person"],
        ...     standardizer_mu=train_mu,  # np.array shape (30,)
        ...     standardizer_sigma=train_sigma,  # np.array shape (30,)
        ...     global_max_abs=train_max,  # float
        ...     training_config={
        ...         "hampel_window": 5,
        ...         "hampel_n_sigmas": 3.0,
        ...         "butter_order": 4,
        ...         "butter_cutoff": 0.1,
        ...     }
        ... )
    """
    checkpoint = {
        "epoch": epoch,
        "state_dict": model.state_dict(),
        "optimizer": optimizer.state_dict() if optimizer else None,
        "model_state_dict": model.state_dict(),  # Redundant nhưng backward-compatible
        
        # ===== Model metadata =====
        "input_shape": input_shape,
        "num_classes": num_classes,
        "class_names": class_names,
        
        # ===== CRITICAL: Standardizers từ training =====
        "standardizer_mu": standardizer_mu,
        "standardizer_sigma": standardizer_sigma,
        "global_max_abs": global_max_abs,
        
        # ===== Training config (preprocessing params) =====
        "training_config": training_config or {},
    }
    
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, save_path)
    print(f"[CHECKPOINT] ✓ Saved to {save_path}")
    print(f"  - model_state_dict: ✓")
    print(f"  - standardizer_mu: {'✓' if standardizer_mu is not None else '✗'}")
    print(f"  - standardizer_sigma: {'✓' if standardizer_sigma is not None else '✗'}")
    print(f"  - global_max_abs: {'✓' if global_max_abs is not None else '✗'}")
    print(f"  - training_config: {training_config if training_config else 'N/A'}")


def compute_standardizers_from_dataset(dataset_loader):
    """
    Tính standardizers (mean, std, max_abs) từ training dataset.
    
    Args:
        dataset_loader: DataLoader hoặc list của training samples
        
    Returns:
        tuple: (mu, sigma, global_max_abs)
        
    Example:
        >>> from torch.utils.data import DataLoader
        >>> train_loader = DataLoader(dataset, batch_size=32)
        >>> mu, sigma, max_abs = compute_standardizers_from_dataset(train_loader)
    """
    all_samples = []
    
    # Lặp qua dataset
    if hasattr(dataset_loader, "__iter__"):
        for batch in dataset_loader:
            if isinstance(batch, (tuple, list)):
                # DataLoader format: (X, y)
                x = batch[0]
            else:
                x = batch
            
            if hasattr(x, "numpy"):
                x = x.numpy()
            
            # Flatten batch → (n_samples * n_time, feature_dim)
            if x.ndim == 3:  # (batch, time, features)
                x = x.reshape(-1, x.shape[-1])
            elif x.ndim > 3:
                x = x.reshape(-1, x.shape[-1])
            
            all_samples.append(x)
    
    # Concatenate
    all_data = np.vstack(all_samples).astype(np.float32)
    
    # Compute standardizers
    mu = np.mean(all_data, axis=0)
    sigma = np.std(all_data, axis=0)
    global_max_abs = np.max(np.abs(all_data))
    
    print(f"[STANDARDIZERS] Computed from {len(all_data)} samples:")
    print(f"  - mu shape: {mu.shape}, sample: {mu[:5]}")
    print(f"  - sigma shape: {sigma.shape}, sample: {sigma[:5]}")
    print(f"  - global_max_abs: {global_max_abs:.6f}")
    
    return mu, sigma, global_max_abs


def update_checkpoint_with_standardizers(
    checkpoint_path: str,
    standardizer_mu: np.ndarray,
    standardizer_sigma: np.ndarray,
    global_max_abs: float,
    output_path: str = None,
):
    """
    Update checkpoint cũ với standardizers.
    
    Args:
        checkpoint_path: Path checkpoint hiện tại
        standardizer_mu: np.array shape (feature_dim,)
        standardizer_sigma: np.array shape (feature_dim,)
        global_max_abs: float value
        output_path: Save vào file mới (hoặc ghi đè nếu None)
    """
    if output_path is None:
        output_path = checkpoint_path
    
    print(f"[UPDATE] Loading checkpoint from {checkpoint_path}")
    ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    
    ckpt["standardizer_mu"] = standardizer_mu
    ckpt["standardizer_sigma"] = standardizer_sigma
    ckpt["global_max_abs"] = global_max_abs
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(ckpt, output_path)
    
    print(f"[UPDATE] ✓ Checkpoint updated and saved to {output_path}")
    print(f"  - Added standardizer_mu (shape: {standardizer_mu.shape})")
    print(f"  - Added standardizer_sigma (shape: {standardizer_sigma.shape})")
    print(f"  - Added global_max_abs ({global_max_abs:.6f})")
