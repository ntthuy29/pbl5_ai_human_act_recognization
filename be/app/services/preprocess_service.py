import numpy as np
from scipy.signal import butter, filtfilt


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


class PreprocessService:
    def __init__(
        self,
        hampel_window_size: int = 5,
        hampel_n_sigmas: float = 3.0,
        butter_order: int = 4,
        butter_cutoff: float = 0.1,
    ):
        self.hampel_window_size = hampel_window_size
        self.hampel_n_sigmas = hampel_n_sigmas
        self.butter_order = butter_order
        self.butter_cutoff = butter_cutoff

    def process(self, window):
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

        # 3) Normalize global
        arr = normalize_global(arr)

        return arr.astype(np.float32)


preprocess_service = PreprocessService()