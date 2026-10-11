"""Verbatim function extraction; source metadata in provenance/sources.json."""
from __future__ import annotations
from typing import Tuple
import numpy as np

def compute_cells(shape: Tuple[int, int], rows: int, cols: int):
    """Compute uniform grid cells as fallback."""
    height, width = shape
    cell_h = height // rows
    cell_w = width // cols
    boxes = []
    for r in range(rows):
        y0 = r * cell_h
        y1 = (r + 1) * cell_h if r < rows - 1 else height
        for c in range(cols):
            x0 = c * cell_w
            x1 = (c + 1) * cell_w if c < cols - 1 else width
            boxes.append(((y0, y1), (x0, x1)))
    return boxes

def compute_centroids(image: np.ndarray, boxes, rows: int, cols: int) -> np.ndarray:
    """Compute center-of-mass centroids for each beamlet."""
    centroids = np.zeros((rows, cols, 2), dtype=float)
    for idx, box in enumerate(boxes):
        (y0, y1), (x0, x1) = box
        patch = image[y0:y1, x0:x1]
        yy, xx = np.mgrid[0:patch.shape[0], 0:patch.shape[1]]
        total = float(patch.sum())
        if total <= 0:
            cy = (patch.shape[0] - 1) / 2.0
            cx = (patch.shape[1] - 1) / 2.0
        else:
            cy = float((patch * yy).sum() / total)
            cx = float((patch * xx).sum() / total)
        row = idx // cols
        col = idx % cols
        centroids[row, col, 0] = x0 + cx
        centroids[row, col, 1] = y0 + cy
    return centroids

def centroid_shifts(ref_centroids: np.ndarray, tgt_centroids: np.ndarray) -> np.ndarray:
    """
    Compute displacements from centroid differences.

    Parameters
    ----------
    ref_centroids, tgt_centroids : ndarray of shape (rows, cols, 2)

    Returns
    -------
    shifts : ndarray of shape (rows, cols, 2)
        Returned in `(dx_px, dy_px)` order.
    """
    return tgt_centroids - ref_centroids
