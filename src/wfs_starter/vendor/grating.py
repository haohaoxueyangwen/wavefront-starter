"""Verbatim function extraction; source metadata in provenance/sources.json."""
from __future__ import annotations
from typing import Tuple
import numpy as np

def build_rect_mask(shape: Tuple[int, int], center: Tuple[int, int], size: Tuple[int, int]) -> np.ndarray:
    """
    Construct a rectangular mask centered at specified position.

    Args:
        shape: Spectrum array shape (rows, cols)
        center: Center coordinates (row, col)
        size: Rectangle size (size_y, size_x), in pixels

    Returns:
        Mask array, dtype=float32, value range {0.0, 1.0}
    """
    rows, cols = shape
    cy, cx = center
    sy, sx = size

    # Defensive checks
    cy = int(np.clip(cy, 0, rows - 1))
    cx = int(np.clip(cx, 0, cols - 1))
    sy = int(max(1, sy))
    sx = int(max(1, sx))

    # Calculate half-size (floor), and generate boundaries (inclusive end)
    half_y = sy // 2
    half_x = sx // 2
    y_start = max(cy - half_y, 0)
    y_end = min(cy + half_y, rows - 1)
    x_start = max(cx - half_x, 0)
    x_end = min(cx + half_x, cols - 1)

    mask = np.zeros((rows, cols), dtype=np.float32)
    mask[y_start : y_end + 1, x_start : x_end + 1] = 1.0
    return mask

def apply_rect_filter(spectrum: np.ndarray, center: Tuple[int, int], size: Tuple[int, int]) -> np.ndarray:
    """
    Apply rectangular bandpass filter to input 2D spectrum, only keeping the region centered at center with size.

    Args:
        spectrum: 2D Spectrum (can be complex or real), shape (rows, cols)
        center: Center coordinates (row, col)
        size: Rectangle size (size_y, size_x)

    Returns:
        Filtered spectrum (same shape and dtype as input)
    """
    if spectrum.ndim != 2:
        raise ValueError("spectrum must be a 2D array")

    mask = build_rect_mask(spectrum.shape, center, size)
    # Preserve dtype and complex property
    if np.iscomplexobj(spectrum):
        return spectrum * mask.astype(spectrum.dtype)
    else:
        return spectrum * mask

def fft_spectrum(image: np.ndarray) -> np.ndarray:
    """
    Calculate and return 2D spectrum (after fftshift, DC at center)。
    适配 gttext.py of图像变量：frames[i] or acc。
    """
    if image.ndim != 2:
        raise ValueError("imagemust be a 2D array")
    return np.fft.fftshift(np.fft.fft2(image))

def shift_sideband_to_dc(F: np.ndarray, center: Tuple[int, int]) -> np.ndarray:
    """
    将InputSpectrumof选inSideband（以centercentered at）平移toDC位置（Arrayin心），保留原Size。
    Note：通常需要先用矩形掩膜选带after再平移，避免把整个Spectrum都移动。
    """
    rows, cols = F.shape
    dc = (rows // 2, cols // 2)
    dy = int(dc[0] - int(center[0]))
    dx = int(dc[1] - int(center[1]))
    F_shift = np.roll(np.roll(F, shift=dy, axis=0), shift=dx, axis=1)
    return F_shift

def phase_from_sideband(image: np.ndarray, center: Tuple[int, int], size: Tuple[int, int]) -> np.ndarray:
    """
    From spatial domain image: calculate spectrum, rectangular band selection, shift sideband to DC, perform inverse FFT and return phase.

    Args:
        image: Spatial domain 2D image (e.g. frames[i] or acc from gttext.py)
        center: Sideband center pixel coordinates (row, col) - index in fftshift display coordinates
        size: Rectangle size (size_y, size_x)

    Returns:
        phi: Phase array (2D), from the angle of the complex envelope of the selected sideband component
    """
    F = fft_spectrum(image)
    F_sel = apply_rect_filter(F, center, size)
    F_to_dc = shift_sideband_to_dc(F_sel, center)
    g = np.fft.ifft2(np.fft.ifftshift(F_to_dc))
    phi = np.angle(g)
    return phi

def unwrap_phase_2d(phi: np.ndarray) -> np.ndarray:
    """
    2D phase unwrapping: first unwrap along rows, then along columns to reduce jumps.
    """
    phi_u = np.unwrap(phi, axis=0)
    phi_u = np.unwrap(phi_u, axis=1)
    return phi_u

def frankot_chellappa(Gx: np.ndarray, Gy: np.ndarray) -> np.ndarray:
    """
    Frankot–Chellappa integration, projects gradient field to integrable space and reconstructs wavefront in frequency domain.
    Returns real-valued wavefront W (missing a constant, can be zero-mean processed later).
    """
    M, N = Gx.shape
    wx = 2.0 * np.pi * np.fft.fftfreq(N)
    wy = 2.0 * np.pi * np.fft.fftfreq(M)
    WX, WY = np.meshgrid(wx, wy)
    Gx_hat = np.fft.fft2(Gx)
    Gy_hat = np.fft.fft2(Gy)
    denom = WX**2 + WY**2
    # 避免除零：令零频处分母asinf（对应加常数of自由度）
    denom[denom == 0] = np.inf
    W_hat = (-1j * (WX * Gx_hat + WY * Gy_hat)) / denom
    W = np.real(np.fft.ifft2(W_hat))
    return W
