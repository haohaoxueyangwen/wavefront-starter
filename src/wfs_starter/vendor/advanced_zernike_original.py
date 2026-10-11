#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Wavefront Analysis with Zernike Polynomials

This tool performs a detailed wavefront analysis, providing a comprehensive
set of quantitative metrics, a professional visualization report, and
high-quality TIFF exports of each phase map.

【Analysis Steps】
1.  Load Phase Data & Define Parameters.
2.  Interactively Select Circular ROI.
3.  Fit Zernike Polynomials to the ROI data.
4.  Calculate Curvature Radii (Rx, Ry, and Mean).
5.  Quantify Wavefront Error (Overall and Higher-Order).
6.  Generate a detailed, centered visualization report with a dedicated text panel.
7.  Export individual phase maps with colorbars as TIFF files.

Author: Assistant (Customized based on user request)
Version: 6.0 (TIFF Export, Centered ROI, Dedicated Report Panel)
Date: 2024
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import least_squares
import os
import math
import warnings

# --- Basic Settings ---
warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False

# ==================== Utility Functions ====================

def prColor(text, color='white'):
    """Prints colored text to the terminal."""
    colors = {
        'red': '\033[31m', 'green': '\033[32m', 'yellow': '\033[33m',
        'cyan': '\033[36m', 'white': '\033[37m', 'reset': '\033[0m'
    }
    color_code = colors.get(color.lower(), colors['white'])
    print(f"{color_code}{text}{colors['reset']}")

def save_map_as_tiff(data_map, colormap, title, filename, vmin=None, vmax=None, progress_callback=None):
    """
    Saves a 2D data map as a TIFF file with a colorbar.
    A temporary figure is created and closed to achieve this.
    """
    message = f"  > Saving {title} to {filename}..."
    if progress_callback:
        progress_callback(message)
    else:
        prColor(message, 'yellow')
    fig_temp, ax_temp = plt.subplots(figsize=(8, 6))
    im = ax_temp.imshow(data_map, cmap=colormap, origin='upper', vmin=vmin, vmax=vmax)
    fig_temp.colorbar(im, ax=ax_temp, label='Phase (rad)')
    ax_temp.set_title(title)
    ax_temp.set_xlabel("X (pixels)")
    ax_temp.set_ylabel("Y (pixels)")
    fig_temp.savefig(filename, format='tiff', dpi=300, bbox_inches='tight', pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig_temp)
    message = f"  ✓ Saved."
    if progress_callback:
        progress_callback(message)
    else:
        prColor(message, 'green')

def select_circular_roi_on_image(phase_data, title="Select ROI"):
    prColor("--- Interactive ROI Selection ---", 'cyan')
    prColor("1. Click on the image to set the circle's center.", 'yellow')
    prColor("2. Drag the mouse to define the radius.", 'yellow')
    prColor("3. Press [Enter] to confirm the selection and close the window.", 'yellow')

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(phase_data, cmap='RdYlGn', origin='upper')
    ax.set_title(f"{title}\nClick to set center, drag for radius, press Enter to confirm")
    plt.colorbar(im, ax=ax, label='Phase (rad)')
    roi_params = {'center': None, 'radius': None, 'circle': None}
    def on_click(event):
        if event.inaxes != ax or roi_params['center'] is not None: return
        roi_params['center'] = (event.xdata, event.ydata)
        ax.plot(event.xdata, event.ydata, 'r+', markersize=15, markeredgewidth=3)
        ax.set_title("Center selected. Drag to set radius.")
        plt.draw()
    def on_motion(event):
        if event.inaxes != ax or roi_params['center'] is None: return
        cx, cy = roi_params['center']
        radius = np.sqrt((event.xdata - cx)**2 + (event.ydata - cy)**2)
        if roi_params['circle']: roi_params['circle'].remove()
        circle = Circle((cx, cy), radius, fill=False, color='red', linewidth=2)
        ax.add_patch(circle)
        roi_params['circle'] = circle
        roi_params['radius'] = radius
        ax.set_title(f"Radius: {radius:.1f} pixels. Press Enter to confirm.")
        plt.draw()
    def on_key(event):
        if event.key == 'enter' and all(roi_params.values()): plt.close(fig)
    fig.canvas.mpl_connect('button_press_event', on_click)
    fig.canvas.mpl_connect('motion_notify_event', on_motion)
    fig.canvas.mpl_connect('key_press_event', on_key)
    plt.show()
    if not all(roi_params.values()): raise ValueError("ROI selection was not completed.")
    center_x, center_y = roi_params['center']
    radius = roi_params['radius']
    prColor(f"✓ ROI Selection Complete: Center({center_x:.1f}, {center_y:.1f}), Radius({radius:.1f})", 'green')
    return center_x, center_y, radius

# ==================== Zernike Core Functions ====================
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
def noll_to_nm(j):
    if j < 1: raise ValueError("Noll index j must be a positive integer.")
    n = int(np.ceil((-3 + np.sqrt(9 + 8 * (j - 1))) / 2))
    m_rem = j - (n * (n + 1) // 2) - 1
    if n % 4 < 2:
        m = 2 * ((m_rem + 2) // 2) if m_rem % 2 == 0 else -2 * ((m_rem + 1) // 2)
    else:
        m = -2 * ((m_rem + 2) // 2) if m_rem % 2 == 0 else 2 * ((m_rem + 1) // 2)
    return n, m
def calculate_roc_from_zernike(coeffs, roi_radius_um, wavelength_um):
    c4 = coeffs[3] if len(coeffs) > 3 else 0
    c6 = coeffs[5] if len(coeffs) > 5 else 0
    lambda_m = wavelength_um * 1e-6
    roi_radius_m = roi_radius_um * 1e-6
    term_defocus_curv = 2 * np.sqrt(3) * c4
    term_astig_curv = np.sqrt(6) * c6
    denominator_x = term_defocus_curv + term_astig_curv
    roc_x_mm = (np.pi * roi_radius_m**2) / (lambda_m * denominator_x) * 1000 if not np.isclose(denominator_x, 0) else float('inf')
    denominator_y = term_defocus_curv - term_astig_curv
    roc_y_mm = (np.pi * roi_radius_m**2) / (lambda_m * denominator_y) * 1000 if not np.isclose(denominator_y, 0) else float('inf')
    denominator_mean = term_defocus_curv
    roc_mean_mm = (np.pi * roi_radius_m**2) / (lambda_m * denominator_mean) * 1000 if not np.isclose(denominator_mean, 0) else float('inf')
    return roc_x_mm, roc_y_mm, roc_mean_mm

# ==================== Analysis Function for GUI Integration ====================

def perform_advanced_zernike_analysis(phase_data, pixel_size_um, wavelength_um, center_x, center_y, radius, zernike_terms_to_fit=15, max_order_remove=2, output_dir=None, base_filename=None, progress_callback=None):
    """
    Perform advanced Zernike analysis on phase data.
    
    Args:
        phase_data: 2D numpy array of phase data
        pixel_size_um: Pixel size in micrometers
        wavelength_um: Wavelength in micrometers
        zernike_terms_to_fit: Number of Zernike terms to fit
        output_dir: Output directory for saving results
        base_filename: Base filename for saving results

    Returns:
        dict: Analysis results including the path to the report figure.
    """
    def report_progress(message, color='white'):
        if progress_callback:
            progress_callback(message)
        else:
            prColor(message, color)

    try:
        report_progress("--- Preparing Data & Fitting ---", 'cyan')
        h, w = phase_data.shape
        y_coords, x_coords = np.indices((h, w))
        mask = (x_coords - center_x)**2 + (y_coords - center_y)**2 <= radius**2
        rho_normalized = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2) / radius
        theta = np.arctan2(y_coords - center_y, x_coords - center_x)
        
        phase_roi = phase_data[mask]
        A = np.zeros((len(phase_roi), zernike_terms_to_fit))
        for j in range(1, zernike_terms_to_fit + 1):
            n, m = noll_to_nm(j); A[:, j - 1] = zernike(rho_normalized[mask], theta[mask], n, m)
        result = least_squares(lambda coeffs: phase_roi - (A @ coeffs), np.zeros(zernike_terms_to_fit))
        fit_coeffs = result.x
        report_progress("✓ Fitting complete!", 'green')

        prColor("\n--- Quantifying Wavefront Errors ---", 'cyan')
        phase_roi_piston_removed = phase_roi - np.mean(phase_roi)
        pv_original = np.ptp(phase_roi_piston_removed); rms_original = np.std(phase_roi_piston_removed)
        report_progress(f"✓ Overall Error (P-V): {pv_original:.4f} rad, (RMS): {rms_original:.4f} rad", 'green')
        
        # Dynamically determine terms to remove up to max_order_remove
        j_max_remove = 0
        for j in range(1, zernike_terms_to_fit + 1):
            n, _ = noll_to_nm(j)
            if n > max_order_remove:
                break
            j_max_remove = j
        second_order_coeffs = np.zeros_like(fit_coeffs)
        if j_max_remove > 0:
            second_order_coeffs[0:j_max_remove] = fit_coeffs[0:j_max_remove]
        phase_error_roi = phase_roi - (A @ second_order_coeffs)
        pv_higher_order = np.ptp(phase_error_roi); rms_higher_order = np.std(phase_error_roi)
        report_progress(f"✓ Higher-Order Error (P-V): {pv_higher_order:.4f} rad, (RMS): {rms_higher_order:.4f} rad", 'green')

        report_progress("--- Calculating Curvature ---", 'cyan')
        roi_radius_um = radius * pixel_size_um
        roc_x, roc_y, roc_mean = calculate_roc_from_zernike(fit_coeffs, roi_radius_um, wavelength_um)
        report_progress(f"✓ Mean ROC: {roc_mean:,.3f} mm | Rx: {roc_x:,.3f} mm | Ry: {roc_y:,.3f} mm", 'green')
        
            # Create full-size maps for analysis and visualization
        original_masked = np.full((h, w), np.nan)
        original_masked[mask] = phase_roi

        fitted_background_2d = np.full((h, w), np.nan)
        fitted_background_2d[mask] = A @ fit_coeffs

        residual_2d = np.full((h, w), np.nan)
        residual_2d[mask] = phase_roi - (A @ fit_coeffs)

        phase_error_2d = np.full((h, w), np.nan)
        phase_error_2d[mask] = phase_error_roi

        # --- Generate Visualization Report ---
        report_progress("--- Generating Visualization Report ---", 'cyan')
        
        # Define optimized bounding box for centered display with padding
        padding = max(10, int(radius * 0.1))  # Add 10% padding or minimum 10 pixels
        x_min, x_max = int(center_x - radius - padding), int(center_x + radius + padding)
        y_min, y_max = int(center_y - radius - padding), int(center_y + radius + padding)
        
        # Ensure bounds are within image limits
        x_min, y_min = max(0, x_min), max(0, y_min)
        x_max, y_max = min(w, x_max), min(h, y_max)
        
        # Crop all maps to the optimized bounding box for display
        original_crop = original_masked[y_min:y_max, x_min:x_max]
        fitted_crop = fitted_background_2d[y_min:y_max, x_min:x_max]
        residual_crop = residual_2d[y_min:y_max, x_min:x_max]
        error_crop = phase_error_2d[y_min:y_max, x_min:x_max]
        
        # Enhanced Visualization
        COLORMAP_SEQ = 'RdYlGn'
        COLORMAP_DIV = 'RdYlGn'
        fig = plt.figure(figsize=(20, 14))
        fig.suptitle("Advanced Zernike Analysis: Comprehensive Report", fontsize=20, y=0.98, weight='bold')
        
        from matplotlib.gridspec import GridSpec
        gs = GridSpec(3, 4, figure=fig, height_ratios=[1, 1, 0.8], width_ratios=[1, 1, 1, 1], 
                     hspace=0.4, wspace=0.3)

        extent = [x_min, x_max, y_min, y_max]
        from matplotlib.patches import Circle

        # Plot 1: Original Phase (Full View)
        ax0 = fig.add_subplot(gs[0, 0])
        ax0.set_title("1. Original Phase (Full)", fontsize=12, weight='bold')
        im0 = ax0.imshow(phase_data, cmap=COLORMAP_SEQ, origin='upper', aspect='auto')
        fig.colorbar(im0, ax=ax0, shrink=0.8).set_label('Phase (rad)', fontsize=9)
        ax0.set_xlabel('X (pixels)', fontsize=9)
        ax0.set_ylabel('Y (pixels)', fontsize=9)
        circle0 = Circle((center_x, center_y), radius, fill=False, color='red', linewidth=2, alpha=0.8)
        ax0.add_patch(circle0)

        # Plot 2: Original Phase (Cropped & Centered)
        ax1 = fig.add_subplot(gs[0, 1])
        ax1.set_title("2. Original Phase (ROI)", fontsize=12, weight='bold')
        im1 = ax1.imshow(original_crop, cmap=COLORMAP_SEQ, origin='upper', extent=extent, aspect='equal')
        fig.colorbar(im1, ax=ax1, shrink=0.8).set_label('Phase (rad)', fontsize=9)
        ax1.set_xlabel('X (pixels)', fontsize=9)
        ax1.set_ylabel('Y (pixels)', fontsize=9)
        circle1 = Circle((center_x, center_y), radius, fill=False, color='red', linewidth=2, alpha=0.8)
        ax1.add_patch(circle1)

        # Plot 3: Fitted Zernike Surface (All terms)
        ax2 = fig.add_subplot(gs[0, 2])
        ax2.set_title("3. Fitted Zernike Surface", fontsize=12, weight='bold')
        im2 = ax2.imshow(fitted_crop, cmap=COLORMAP_SEQ, origin='upper', extent=extent, aspect='equal')
        fig.colorbar(im2, ax=ax2, shrink=0.8).set_label('Phase (rad)', fontsize=9)
        ax2.set_xlabel('X (pixels)', fontsize=9)
        ax2.set_ylabel('Y (pixels)', fontsize=9)
        circle2 = Circle((center_x, center_y), radius, fill=False, color='red', linewidth=2, alpha=0.8)
        ax2.add_patch(circle2)

        # Plot 4: Higher-Order Aberrations
        ax3 = fig.add_subplot(gs[0, 3])
        ax3.set_title(f"4. Aberrations after Removing Orders 0-{max_order_remove}", fontsize=12, weight='bold')
        vmax_err = np.nanmax(np.abs(error_crop))
        im3 = ax3.imshow(error_crop, cmap=COLORMAP_DIV, origin='upper', extent=extent, 
                        vmin=-vmax_err, vmax=vmax_err, aspect='equal')
        fig.colorbar(im3, ax=ax3, shrink=0.8).set_label('Phase (rad)', fontsize=9)
        ax3.set_xlabel('X (pixels)', fontsize=9)
        ax3.set_ylabel('Y (pixels)', fontsize=9)
        circle3 = Circle((center_x, center_y), radius, fill=False, color='black', linewidth=2, alpha=0.8)
        ax3.add_patch(circle3)

        # Plot 5: Fitting Residual
        ax4 = fig.add_subplot(gs[1, 0])
        ax4.set_title("5. Fitting Residual", fontsize=12, weight='bold')
        vmax_res = np.nanmax(np.abs(residual_crop))
        im4 = ax4.imshow(residual_crop, cmap=COLORMAP_DIV, origin='upper', extent=extent, 
                        vmin=-vmax_res, vmax=vmax_res, aspect='equal')
        fig.colorbar(im4, ax=ax4, shrink=0.8).set_label('Phase (rad)', fontsize=9)
        ax4.set_xlabel('X (pixels)', fontsize=9)
        ax4.set_ylabel('Y (pixels)', fontsize=9)
        circle4 = Circle((center_x, center_y), radius, fill=False, color='black', linewidth=2, alpha=0.8)
        ax4.add_patch(circle4)

        # Plot 6: Zernike Coefficients
        ax5 = fig.add_subplot(gs[1, 1:3])
        ax5.set_title("6. Zernike Coefficients (Noll Indexing)", fontsize=12, weight='bold')
        j_indices = np.arange(1, zernike_terms_to_fit + 1)
        bars = ax5.bar(j_indices, fit_coeffs, alpha=0.7, edgecolor='black', linewidth=0.5)
        max_coeff = np.max(np.abs(fit_coeffs))
        for i, bar in enumerate(bars):
            normalized_height = abs(fit_coeffs[i]) / max_coeff if max_coeff > 0 else 0
            bar.set_color(plt.cm.plasma(normalized_height))
        ax5.grid(True, axis='y', linestyle='--', alpha=0.7)
        ax5.axhline(0, color='black', linewidth=1.0)
        ax5.set_xticks(j_indices)
        ax5.set_xlabel("Noll Index (j)", fontsize=10)
        ax5.set_ylabel("Coefficient Amplitude", fontsize=10)
        ax5.tick_params(axis='both', which='major', labelsize=9)

        # Plot 7: 3D view of Original Phase
        try:
            from mpl_toolkits.mplot3d import Axes3D
            ax6 = fig.add_subplot(gs[1, 3], projection='3d')
            ax6.set_title("7. 3D View: Original", fontsize=12, weight='bold')
            X, Y = np.meshgrid(np.arange(original_crop.shape[1]), np.arange(original_crop.shape[0]))
            ax6.plot_surface(X, Y, original_crop, cmap=COLORMAP_SEQ, edgecolor='none', alpha=0.8)
            ax6.set_xlabel('X', fontsize=8)
            ax6.set_ylabel('Y', fontsize=8)
            ax6.set_zlabel('Phase', fontsize=8)
        except:
            # Fallback if 3D plotting fails
            ax6 = fig.add_subplot(gs[1, 3])
            ax6.text(0.5, 0.5, '3D View\nUnavailable', ha='center', va='center', fontsize=10)
            ax6.set_title("7. 3D View: Original", fontsize=12, weight='bold')
            ax6.axis('off')

        # Plot 8: Enhanced Text Report Panel
        ax7 = fig.add_subplot(gs[2, :])
        ax7.axis('off')
        ax7.set_title("Quantitative Analysis Summary", fontsize=14, weight='bold')
        
        pv_fit_residual = np.ptp(residual_crop[~np.isnan(residual_crop)])
        rms_fit_residual = np.nanstd(residual_crop)
        
        stats_text = (
            f"📊 CURVATURE ANALYSIS\n"
            f"  Mean ROC: {roc_mean:12,.2f} mm (Spherical Equivalent)\n"
            f"  Rx (Meridional): {roc_x:8,.2f} mm\n"
            f"  Ry (Sagittal):   {roc_y:8,.2f} mm\n\n"
            f"📈 OVERALL WAVEFRONT ERROR (ROI)\n"
            f"  Peak-to-Valley:   {pv_original:8.4f} rad\n"
            f"  RMS:              {rms_original:8.4f} rad\n\n"
            f"  Aberrations after Removing Orders 0-{max_order_remove}\n"
            f"  Peak-to-Valley:   {pv_higher_order:8.4f} rad\n"
            f"  RMS:              {rms_higher_order:8.4f} rad\n\n"
            f"📉 FITTING RESIDUAL (Data vs Zernike Fit)\n"
            f"  Peak-to-Valley:   {pv_fit_residual:8.4f} rad\n"
            f"  RMS:              {rms_fit_residual:8.4f} rad\n\n"
            f"⚙️ ANALYSIS PARAMETERS\n"
            f"  ROI Center: ({center_x:.1f}, {center_y:.1f})\n"
            f"  ROI Radius: {radius:.1f} pixels\n"
            f"  Zernike Terms: {zernike_terms_to_fit}\n"
            f"  Pixel Size: {pixel_size_um:.3f} μm"
        )
        ax7.text(0.05, 0.95, stats_text, ha='left', va='top', fontsize=10, 
                fontfamily='monospace', transform=ax7.transAxes,
                bbox=dict(boxstyle='round,pad=1', facecolor='lightblue', alpha=0.2, edgecolor='navy'))
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # --- Save Results and Return --- 
        report_figure_path = None
        higher_order_path = None
        if output_dir and base_filename:
            os.makedirs(output_dir, exist_ok=True)
            report_figure_path = os.path.join(output_dir, f"{base_filename}_advanced_zernike_report.png")
            fig.savefig(report_figure_path, dpi=300, bbox_inches='tight')
            report_progress(f"✓ Report saved to {report_figure_path}", 'green')
            plt.close(fig)

            # Save higher-order aberration map separately
            try:
                higher_order_fig = plt.figure(figsize=(8, 6))
                ax_ho = higher_order_fig.add_subplot(111)
                vmax_err = np.nanmax(np.abs(error_crop))
                im_ho = ax_ho.imshow(error_crop, cmap=COLORMAP_DIV, origin='upper', extent=extent,
                                    vmin=-vmax_err, vmax=vmax_err, aspect='equal')
                higher_order_fig.colorbar(im_ho, ax=ax_ho, label='Phase (rad)')
                ax_ho.set_title(f"Aberrations after Removing Orders 0-{max_order_remove}")
                ax_ho.set_xlabel("X (pixels)")
                ax_ho.set_ylabel("Y (pixels)")
                circle_ho = Circle((center_x, center_y), radius, fill=False, color='black', linewidth=2, alpha=0.8)
                ax_ho.add_patch(circle_ho)
                higher_order_fig.tight_layout()
                
                higher_order_path = os.path.join(output_dir, f"{base_filename}_higher_order_aberrations.png")
                higher_order_fig.savefig(higher_order_path, dpi=300, bbox_inches='tight')
                plt.close(higher_order_fig)
                report_progress(f"✓ Higher-order aberration map saved to {higher_order_path}", 'green')
            except Exception as e:
                report_progress(f"Warning: Could not save higher order aberration figure: {e}", 'yellow')
        else:
            plt.show()

        return {
            'status': 'success',
            'report_figure_path': report_figure_path,
            'higher_order_path': higher_order_path,
            'pv_original_rad': pv_original,
            'rms_original_rad': rms_original,
            'pv_higher_order_rad': pv_higher_order,
            'rms_higher_order_rad': rms_higher_order,
            'roc_mean_mm': roc_mean,
            'roc_x_mm': roc_x,
            'roc_y_mm': roc_y,
            'zernike_coeffs': fit_coeffs.tolist()
        }

       
        
    except Exception as e:
        error_message = f"An error occurred during analysis: {e}"
        report_progress(error_message, 'red')
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'message': str(e)
        }

# ==================== Main Function ====================

def main():
    prColor("\n" + "="*60, 'cyan')
    prColor("   Advanced Wavefront Analysis with Zernike Polynomials   ", 'cyan')
    prColor("="*60, 'cyan')

    PHASE_FILE_PATH = "Run 1_phase.npy"
    PIXEL_SIZE_UM = 0.65
    WAVELENGTH_UM = 0.082656
    ZERNIKE_TERMS_TO_FIT = 15

    try:
        prColor("\n--- Loading Data ---", 'cyan')
        if not os.path.exists(PHASE_FILE_PATH):
            prColor(f"Warning: File not found. Creating dummy data '{PHASE_FILE_PATH}'.", 'yellow')
            y, x = np.ogrid[-511:512, -511:512]; dummy_phase = ((x**2 + y**2)/15000.0 + (x**2 - y**2)/30000.0 + (x**3 - 3*x*y**2)/8e7) + np.random.rand(1023, 1023) * 0.2
            np.save(PHASE_FILE_PATH, dummy_phase)
        phase_data = np.load(PHASE_FILE_PATH)
        prColor(f"✓ Data loaded, shape: {phase_data.shape}", 'green')

        center_x, center_y, radius = select_circular_roi_on_image(phase_data)
        
        prColor("\n--- Preparing Data & Fitting ---", 'cyan')
        h, w = phase_data.shape
        y_coords, x_coords = np.indices((h, w))
        mask = (x_coords - center_x)**2 + (y_coords - center_y)**2 <= radius**2
        rho_normalized = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2) / radius
        theta = np.arctan2(y_coords - center_y, x_coords - center_x)
        
        phase_roi = phase_data[mask]
        A = np.zeros((len(phase_roi), ZERNIKE_TERMS_TO_FIT))
        for j in range(1, ZERNIKE_TERMS_TO_FIT + 1):
            n, m = noll_to_nm(j); A[:, j - 1] = zernike(rho_normalized[mask], theta[mask], n, m)
        result = least_squares(lambda coeffs: phase_roi - (A @ coeffs), np.zeros(ZERNIKE_TERMS_TO_FIT))
        fit_coeffs = result.x
        prColor("✓ Fitting complete!", 'green')

        prColor("\n--- Quantifying Wavefront Errors ---", 'cyan')
        phase_roi_piston_removed = phase_roi - np.mean(phase_roi)
        pv_original = np.ptp(phase_roi_piston_removed); rms_original = np.std(phase_roi_piston_removed)
        prColor(f"✓ Overall Error (P-V): {pv_original:.4f} rad, (RMS): {rms_original:.4f} rad", 'green')
        
        second_order_coeffs = np.zeros_like(fit_coeffs)
        if len(fit_coeffs) > 5: second_order_coeffs[3:6] = fit_coeffs[3:6]
        phase_error_roi = phase_roi - (A @ second_order_coeffs)
        pv_higher_order = np.ptp(phase_error_roi); rms_higher_order = np.std(phase_error_roi)
        prColor(f"✓ Higher-Order Error (P-V): {pv_higher_order:.4f} rad, (RMS): {rms_higher_order:.4f} rad", 'green')

        prColor("\n--- Calculating Curvature ---", 'cyan')
        roi_radius_um = radius * PIXEL_SIZE_UM
        roc_x, roc_y, roc_mean = calculate_roc_from_zernike(fit_coeffs, roi_radius_um, WAVELENGTH_UM)
        prColor(f"✓ Mean ROC: {roc_mean:,.3f} mm | Rx: {roc_x:,.3f} mm | Ry: {roc_y:,.3f} mm", 'green')
        
        # --- NEW: Create full-size maps first, then crop for display ---
        original_masked = np.full((h, w), np.nan); original_masked[mask] = phase_roi
        fitted_background_2d = np.full((h, w), np.nan); fitted_background_2d[mask] = A @ fit_coeffs
        residual_2d = np.full((h, w), np.nan); residual_2d[mask] = phase_roi - (A @ fit_coeffs)
        phase_error_2d = np.full((h, w), np.nan); phase_error_2d[mask] = phase_error_roi

        # --- NEW: Define optimized bounding box for centered display with padding ---
        padding = max(10, int(radius * 0.1))  # Add 10% padding or minimum 10 pixels
        x_min, x_max = int(center_x - radius - padding), int(center_x + radius + padding)
        y_min, y_max = int(center_y - radius - padding), int(center_y + radius + padding)
        
        # Ensure bounds are within image limits
        x_min, y_min = max(0, x_min), max(0, y_min)
        x_max, y_max = min(w, x_max), min(h, y_max)
        
        # Ensure the crop region is square for better visualization
        crop_width = x_max - x_min
        crop_height = y_max - y_min
        if crop_width != crop_height:
            # Make it square by expanding the smaller dimension
            target_size = max(crop_width, crop_height)
            
            # Adjust x bounds
            x_center = (x_min + x_max) // 2
            x_min = max(0, x_center - target_size // 2)
            x_max = min(w, x_min + target_size)
            if x_max - x_min < target_size:
                x_min = max(0, x_max - target_size)
            
            # Adjust y bounds
            y_center = (y_min + y_max) // 2
            y_min = max(0, y_center - target_size // 2)
            y_max = min(h, y_min + target_size)
            if y_max - y_min < target_size:
                y_min = max(0, y_max - target_size)

        # Crop all maps to the optimized bounding box for display
        original_crop = original_masked[y_min:y_max, x_min:x_max]
        fitted_crop = fitted_background_2d[y_min:y_max, x_min:x_max]
        residual_crop = residual_2d[y_min:y_max, x_min:x_max]
        error_crop = phase_error_2d[y_min:y_max, x_min:x_max]
        
        prColor(f"✓ Optimized crop region: ({x_min}, {y_min}) to ({x_max}, {y_max}), size: {x_max-x_min}×{y_max-y_min}", 'green')

        # --- Enhanced Visualization ---
        prColor("\n--- Generating Enhanced Visualization Report ---", 'cyan')
        COLORMAP_SEQ = 'RdYlGn'; COLORMAP_DIV = 'RdYlGn'  # Better color schemes
        fig = plt.figure(figsize=(22, 16)) # Increased figure size for more plots
        fig.suptitle("Advanced Zernike Analysis: Comprehensive Report", fontsize=22, y=0.98, weight='bold')
        gs = GridSpec(4, 3, figure=fig, height_ratios=[1, 1, 1, 1], width_ratios=[1, 1, 1.2], 
                     hspace=0.5, wspace=0.4)

        extent = [x_min, x_max, y_min, y_max]

        # Plot 1: Original Phase (Full View)
        ax0 = fig.add_subplot(gs[0, 0])
        ax0.set_title("1. Original Phase (Full)", fontsize=14, weight='bold')
        im0 = ax0.imshow(phase_data, cmap=COLORMAP_SEQ, origin='upper', aspect='auto')
        fig.colorbar(im0, ax=ax0, shrink=0.8).set_label('Phase (rad)', fontsize=10)
        ax0.set_xlabel('X (pixels)', fontsize=10)
        ax0.set_ylabel('Y (pixels)', fontsize=10)
        circle0 = Circle((center_x, center_y), radius, fill=False, color='red', linewidth=2, alpha=0.8)
        ax0.add_patch(circle0)

        # Plot 2: Original Phase (Cropped & Centered)
        ax1 = fig.add_subplot(gs[0, 1])
        ax1.set_title("2. Original Phase (ROI)", fontsize=14, weight='bold')
        im1 = ax1.imshow(original_crop, cmap=COLORMAP_SEQ, origin='upper', extent=extent, aspect='equal')
        fig.colorbar(im1, ax=ax1, shrink=0.8).set_label('Phase (rad)', fontsize=10)
        ax1.set_xlabel('X (pixels)', fontsize=10)
        ax1.set_ylabel('Y (pixels)', fontsize=10)
        circle1 = Circle((center_x, center_y), radius, fill=False, color='red', linewidth=2, alpha=0.8)
        ax1.add_patch(circle1)

        # Calculate 2nd order surface
        second_order_coeffs_only = np.zeros_like(fit_coeffs)
        if len(fit_coeffs) > 5: second_order_coeffs_only[3:6] = fit_coeffs[3:6]
        fitted_2nd_order_surface_1d = A @ second_order_coeffs_only
        fitted_2nd_order_surface_2d = np.full((h, w), np.nan)
        fitted_2nd_order_surface_2d[mask] = fitted_2nd_order_surface_1d
        fitted_2nd_order_crop = fitted_2nd_order_surface_2d[y_min:y_max, x_min:x_max]

        # Plot 3: Fitted 2nd Order Surface
        ax2 = fig.add_subplot(gs[0, 2])
        ax2.set_title("3. Fitted 2nd Order Surface", fontsize=14, weight='bold')
        im2 = ax2.imshow(fitted_2nd_order_crop, cmap=COLORMAP_SEQ, origin='upper', extent=extent, aspect='equal')
        fig.colorbar(im2, ax=ax2, shrink=0.8).set_label('Phase (rad)', fontsize=10)
        ax2.set_xlabel('X (pixels)', fontsize=10)
        ax2.set_ylabel('Y (pixels)', fontsize=10)
        circle2 = Circle((center_x, center_y), radius, fill=False, color='red', linewidth=2, alpha=0.8)
        ax2.add_patch(circle2)

        # Plot 4: Higher-Order Aberrations (Residual after removing 2nd order)
        ax3 = fig.add_subplot(gs[0, 3])
        ax3.set_title("4. Higher-Order Aberrations", fontsize=14, weight='bold')
        vmax_err = np.nanmax(np.abs(error_crop))
        im3 = ax3.imshow(error_crop, cmap=COLORMAP_DIV, origin='upper', extent=extent, 
                        vmin=-vmax_err, vmax=vmax_err, aspect='equal')
        fig.colorbar(im3, ax=ax3, shrink=0.8).set_label('Phase (rad)', fontsize=10)
        ax3.set_xlabel('X (pixels)', fontsize=10)
        ax3.set_ylabel('Y (pixels)', fontsize=10)
        circle3 = Circle((center_x, center_y), radius, fill=False, color='black', linewidth=2, alpha=0.8)
        ax3.add_patch(circle3)

        # Plot 5: Fitted Zernike Surface (All terms)
        ax4 = fig.add_subplot(gs[1, 0])
        ax4.set_title("5. Fitted Zernike Surface (All)", fontsize=14, weight='bold')
        im4 = ax4.imshow(fitted_crop, cmap=COLORMAP_SEQ, origin='upper', extent=extent, aspect='equal')
        fig.colorbar(im4, ax=ax4, shrink=0.8).set_label('Phase (rad)', fontsize=10)
        ax4.set_xlabel('X (pixels)', fontsize=10)
        ax4.set_ylabel('Y (pixels)', fontsize=10)
        circle4 = Circle((center_x, center_y), radius, fill=False, color='red', linewidth=2, alpha=0.8)
        ax4.add_patch(circle4)

        # Plot 6: Fitting Residual (Data - All terms fit)
        ax5 = fig.add_subplot(gs[1, 1])
        ax5.set_title("6. Fitting Residual", fontsize=14, weight='bold')
        vmax_res = np.nanmax(np.abs(residual_crop))
        im5 = ax5.imshow(residual_crop, cmap=COLORMAP_DIV, origin='upper', extent=extent, 
                        vmin=-vmax_res, vmax=vmax_res, aspect='equal')
        fig.colorbar(im5, ax=ax5, shrink=0.8).set_label('Phase (rad)', fontsize=10)
        ax5.set_xlabel('X (pixels)', fontsize=10)
        ax5.set_ylabel('Y (pixels)', fontsize=10)
        circle5 = Circle((center_x, center_y), radius, fill=False, color='black', linewidth=2, alpha=0.8)
        ax5.add_patch(circle5)

        # Plot 7: Zernike Coefficients
        ax6 = fig.add_subplot(gs[1, 0:2])
        ax6.set_title("Zernike Coefficients (Noll Indexing)", fontsize=14, weight='bold')
        j_indices = np.arange(1, ZERNIKE_TERMS_TO_FIT + 1)
        bars = ax6.bar(j_indices, fit_coeffs, alpha=0.7, edgecolor='black', linewidth=0.5)
        max_coeff = np.max(np.abs(fit_coeffs))
        for i, bar in enumerate(bars):
            normalized_height = abs(fit_coeffs[i]) / max_coeff if max_coeff > 0 else 0
            bar.set_color(plt.cm.plasma(normalized_height))
        ax6.grid(True, axis='y', linestyle='--', alpha=0.7)
        ax6.axhline(0, color='black', linewidth=1.0)
        ax6.set_xticks(j_indices)
        ax6.set_xlabel("Noll Index (j)", fontsize=12)
        ax6.set_ylabel("Coefficient Amplitude", fontsize=12)
        ax6.tick_params(axis='both', which='major', labelsize=10)

        # Plot 8: 3D view of Original Phase
        ax7 = fig.add_subplot(gs[2, 0], projection='3d')
        ax7.set_title("7. 3D View: Original Phase", fontsize=14, weight='bold')
        X, Y = np.meshgrid(np.arange(original_crop.shape[1]), np.arange(original_crop.shape[0]))
        ax7.plot_surface(X, Y, original_crop, cmap=COLORMAP_SEQ, edgecolor='none')
        ax7.set_xlabel('X', fontsize=10); ax7.set_ylabel('Y', fontsize=10); ax7.set_zlabel('Phase', fontsize=10)

        # Plot 9: 3D view of Higher-Order Aberrations
        ax8 = fig.add_subplot(gs[2, 1], projection='3d')
        ax8.set_title("8. 3D View: Higher-Order", fontsize=14, weight='bold')
        ax8.plot_surface(X, Y, error_crop, cmap=COLORMAP_DIV, vmin=-vmax_err, vmax=vmax_err, edgecolor='none')
        ax8.set_xlabel('X', fontsize=10); ax8.set_ylabel('Y', fontsize=10); ax8.set_zlabel('Phase', fontsize=10)

        # Plot 10: Enhanced Text Report Panel
        ax9 = fig.add_subplot(gs[0, 2])
        ax9.set_title("Quantitative Analysis", fontsize=14, weight='bold')
        ax9.axis('off')
        # Move text to a new subplot in the last row
        ax_text = fig.add_subplot(gs[3, :])
        ax_text.axis('off')
        ax9.set_title("Quantitative Analysis Summary", fontsize=14, weight='bold')
        ax9.axis('off')
        pv_fit_residual = np.ptp(residual_crop); rms_fit_residual = np.std(residual_crop)
        stats_text = (
            f"📊 CURVATURE ANALYSIS\n"
            f"  Mean ROC: {roc_mean:12,.2f} mm (Spherical Equivalent)\n"
            f"  Rx (Meridional): {roc_x:8,.2f} mm\n"
            f"  Ry (Sagittal):   {roc_y:8,.2f} mm\n\n"
            f"📈 OVERALL WAVEFRONT ERROR (ROI)\n"
            f"  Peak-to-Valley:   {pv_original:8.4f} rad\n"
            f"  RMS:              {rms_original:8.4f} rad\n\n"
            f"🔍 HIGHER-ORDER ABERRATIONS\n"
            f"  Peak-to-Valley:   {pv_higher_order:8.4f} rad\n"
            f"  RMS:              {rms_higher_order:8.4f} rad\n\n"
            f"📉 FITTING RESIDUAL (Data vs Zernike Fit)\n"
            f"  Peak-to-Valley:   {pv_fit_residual:8.4f} rad\n"
            f"  RMS:              {rms_fit_residual:8.4f} rad\n\n"
            f"⚙️ ANALYSIS PARAMETERS\n"
            f"  ROI Center: ({center_x:.1f}, {center_y:.1f})\n"
            f"  ROI Radius: {radius:.1f} pixels\n"
            f"  Zernike Terms: {ZERNIKE_TERMS_TO_FIT}\n"
            f"  Pixel Size: {PIXEL_SIZE_UM:.3f} μm"
        )
        ax_text.text(0.05, 0.95, stats_text, ha='left', va='top', fontsize=11, 
                fontfamily='monospace', transform=ax_text.transAxes,
                bbox=dict(boxstyle='round,pad=1', facecolor='lightblue', alpha=0.2, edgecolor='navy'))
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # --- Save Main Report Figure ---
        output_dir = "analysis_results_zernike_fit"  #输出路径
        os.makedirs(output_dir, exist_ok=True)
        base_filename = os.path.splitext(os.path.basename(PHASE_FILE_PATH))[0]
        png_file = os.path.join(output_dir, f"{base_filename}_zernike_detailed_report.png")
        plt.savefig(png_file, dpi=200)
        prColor(f"✓ Detailed analysis report saved to: {png_file}", 'green')
        plt.show()

        # --- NEW: Export Individual TIFFs ---
        prColor("\n--- Exporting Individual Maps as TIFF files ---", 'cyan')
        save_map_as_tiff(original_crop, COLORMAP_SEQ, "Original Phase (ROI)", os.path.join(output_dir, f"{base_filename}_1_original_phase.tiff"))
        save_map_as_tiff(fitted_crop, COLORMAP_SEQ, "Fitted Background", os.path.join(output_dir, f"{base_filename}_2_fitted_background.tiff"))
        save_map_as_tiff(residual_crop, COLORMAP_DIV, "Residual (Fit Error)", os.path.join(output_dir, f"{base_filename}_3_residual.tiff"), vmin=-vmax_res, vmax=vmax_res)
        save_map_as_tiff(error_crop, COLORMAP_DIV, "Higher-Order Error", os.path.join(output_dir, f"{base_filename}_4_higher_order_error.tiff"), vmin=-vmax_err, vmax=vmax_err)

    except Exception as e:
        prColor(f"\n✗ Program execution failed: {str(e)}", 'red')
        import traceback
        prColor(f"Detailed error information:\n{traceback.format_exc()}", 'red')

if __name__ == "__main__":
    main()