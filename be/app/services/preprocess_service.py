import numpy as np
from scipy.signal import butter, filtfilt, spectrogram

from app.services.amp_phase import prepare_model_feature_window

def hampel_filter_1d(
    signal: np.ndarray,
    window_size: int = 5,
    n_sigmas: float = 3.0,
) -> np.ndarray:
    filtered = signal.copy()

    for idx in range(window_size, len(signal) - window_size):
        window = signal[idx - window_size: idx + window_size]
        median = np.median(window)
        mad = np.median(np.abs(window - median))

        if mad == 0:
            continue

        threshold = n_sigmas * 1.4826 * mad
        if abs(signal[idx] - median) > threshold:
            filtered[idx] = median

    return filtered


def apply_hampel(
    csi: np.ndarray,
    window_size: int = 5,
    n_sigmas: float = 3.0,
) -> np.ndarray:
    output = np.zeros_like(csi)
    for col in range(csi.shape[1]):
        output[:, col] = hampel_filter_1d(
            csi[:, col],
            window_size=window_size,
            n_sigmas=n_sigmas,
        )
    return output


def butterworth_lowpass(
    csi: np.ndarray,
    order: int = 4,
    cutoff: float = 0.1,
) -> np.ndarray:
    b, a = butter(order, cutoff, btype="low")
    return filtfilt(b, a, csi, axis=0)


def normalize_global(x: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    max_abs = np.max(np.abs(x))
    return x / (max_abs + eps)


def apply_standardizer(x: np.ndarray, mu: np.ndarray, sigma: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Apply per-axis standardization: (x - mu) / (sigma + eps)"""
    return (x - mu) / (sigma + eps)


def apply_global_normalizer(x: np.ndarray, max_abs: float, eps: float = 1e-8) -> np.ndarray:
    """Apply global normalization using pre-computed max_abs from training"""
    if max_abs is None or max_abs <= 0:
        # Fallback: compute from data if not available
        max_abs = np.max(np.abs(x))
    return x / (max_abs + eps)


def convert_window_to_spectrogram(
    window: np.ndarray,
    nperseg: int = 128,
    noverlap: int | None = None,
) -> np.ndarray:
    """Convert a 2D CSI window into a 3D spectrogram tensor.

    Output shape: (freq_bins, time_bins, channels)
    """
    arr = np.asarray(window, dtype=np.float32)
    if arr.ndim != 2:
        raise ValueError(f"Window must be 2D before spectrogram conversion, got shape={arr.shape}")

    if arr.shape[0] < 2:
        raise ValueError("Window is too short for spectrogram conversion")

    nperseg = min(int(nperseg), arr.shape[0])
    if nperseg < 2:
        nperseg = 2
    if noverlap is None:
        noverlap = max(0, nperseg // 2)
    noverlap = min(int(noverlap), nperseg - 1)

    channel_specs: list[np.ndarray] = []
    for col in range(arr.shape[1]):
        _, _, spec = spectrogram(
            arr[:, col],
            nperseg=nperseg,
            noverlap=noverlap,
            scaling="density",
            mode="magnitude",
        )
        channel_specs.append(spec.astype(np.float32, copy=False))

    return np.stack(channel_specs, axis=-1).astype(np.float32, copy=False)


class PreprocessService:
    def __init__(
        self,
        hampel_window_size: int = 5,
        hampel_n_sigmas: float = 3.0,
        butter_order: int = 4,
        butter_cutoff: float = 0.1,
        spectrogram_nperseg: int = 128,
        standardizer_mu: np.ndarray | None = None,
        standardizer_sigma: np.ndarray | None = None,
        global_max_abs: float | None = None,
    ):
        self.hampel_window_size = hampel_window_size
        self.hampel_n_sigmas = hampel_n_sigmas
        self.butter_order = butter_order
        self.butter_cutoff = butter_cutoff
        self.spectrogram_nperseg = spectrogram_nperseg
        self.standardizer_mu = standardizer_mu
        self.standardizer_sigma = standardizer_sigma
        self.global_max_abs = global_max_abs

    def _filter_window(self, window):
        arr = np.array(window, dtype=np.float32)

        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)

        if arr.ndim != 2:
            raise ValueError(f"Window phải là mảng 2 chiều, nhưng nhận được shape={arr.shape}")

        if arr.shape[0] <= (self.hampel_window_size * 2 + 1):
            raise ValueError(
                f"Window quá ngắn cho Hampel filter. "
                f"Cần > {self.hampel_window_size * 2 + 1} dòng, nhưng nhận được {arr.shape[0]}"
            )

        # 1) Hampel filter
        arr = apply_hampel(
            arr,
            window_size=self.hampel_window_size,
            n_sigmas=self.hampel_n_sigmas,
        )

        # 2) Butterworth low-pass
        arr = butterworth_lowpass(
            arr,
            order=self.butter_order,
            cutoff=self.butter_cutoff,
        )

        return arr

    def _normalize_window(self, window):
        arr = np.array(window, dtype=np.float32)

        # 3) Apply standardizer (per-axis normalization from training)
        if self.standardizer_mu is not None and self.standardizer_sigma is not None:
            arr = apply_standardizer(arr, self.standardizer_mu, self.standardizer_sigma)

        # 4) Apply global normalization (using training max_abs)
        if self.global_max_abs is not None:
            arr = apply_global_normalizer(arr, self.global_max_abs)

        return arr.astype(np.float32)

    def process(
        self,
        window,
        model_type: str = "lstmcnn",
        target_feature_dim: int | None = None,
    ):
        arr = np.asarray(window, dtype=np.float32)
        if target_feature_dim is None and arr.ndim == 2:
            target_feature_dim = arr.shape[1]
        arr = prepare_model_feature_window(window, target_feature_dim=target_feature_dim)

        filtered = self._filter_window(arr)

        if model_type.lower() == "cnn2d":
            filtered = convert_window_to_spectrogram(
                filtered,
                nperseg=self.spectrogram_nperseg,
            )

        return self._normalize_window(filtered)


preprocess_service = PreprocessService()