import torch

try:
    ckpt = torch.load('models/lstmcnn.pt', map_location='cpu', weights_only=False)
    
    print("=== MODEL INFO ===")
    print(f"input_shape: {ckpt.get('input_shape')}")
    print(f"num_classes: {ckpt.get('num_classes')}")
    print(f"class_names: {ckpt.get('class_names')}")
    
    print("\n=== STANDARDIZERS ===")
    has_mu = 'standardizer_mu' in ckpt
    has_sigma = 'standardizer_sigma' in ckpt
    has_max = 'global_max_abs' in ckpt
    
    print(f"standardizer_mu: {'✓' if has_mu else '✗'}")
    print(f"standardizer_sigma: {'✓' if has_sigma else '✗'}")
    print(f"global_max_abs: {'✓' if has_max else '✗'}")
    
    if has_mu:
        print(f"  mu shape: {ckpt['standardizer_mu'].shape}")
    if has_sigma:
        print(f"  sigma shape: {ckpt['standardizer_sigma'].shape}")
    if has_max:
        print(f"  max_abs: {ckpt['global_max_abs']}")
    
    print("\n=== ALL KEYS ===")
    print(list(ckpt.keys()))
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
