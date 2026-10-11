"""Verbatim function extraction; source metadata in provenance/sources.json."""
from __future__ import annotations
import math
import numpy as np

def zernike_radial(rho, n, m):
    m_abs = abs(m)
    if (n - m_abs) % 2 != 0: return np.zeros_like(rho)
    R = np.zeros_like(rho)
    for k in range((n - m_abs) // 2 + 1):
        coeff = ((-1)**k * math.factorial(n - k) / (math.factorial(k) * math.factorial((n + m_abs) // 2 - k) * math.factorial((n - m_abs) // 2 - k)))
        R += coeff * rho**(n - 2 * k)
    return R

def zernike(rho, theta, n, m):
    m_abs = abs(m)
    if (n - m_abs) % 2 != 0: return np.zeros_like(rho)
    radial_part = zernike_radial(rho, n, m_abs)
    if m == 0: return math.sqrt(n + 1) * radial_part
    norm_factor = math.sqrt(2 * (n + 1))
    if m > 0: return norm_factor * radial_part * np.cos(m * theta)
    else: return norm_factor * radial_part * np.sin(m_abs * theta)
