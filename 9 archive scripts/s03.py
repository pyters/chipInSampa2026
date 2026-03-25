import pandas as pd
import matplotlib.pyplot as plt
import numpy as np # Added for interpolation
import os

# ==============================================================================
# ======================== USER CONFIGURATION SECTION ==========================
# ==============================================================================
# 1. FILES CONFIGURATION
# Dictionary mapping Mode Name -> Filename
FILES_MAP = {
    '01': 'spParameters_mode01.vcsv',
    '10': 'spParameters_mode10.vcsv',
    '11': 'spParameters_mode11.vcsv'
}

# 2. COLOR CONFIGURATION
# Dictionary mapping Mode Name -> Color
COLORS = {
    '01': '#1f77b4', 
    '10': '#ff7f0e', 
    '11': '#2ca02c'
}

# 3. FREQUENCY SETTINGS (in GHz)
CENTER_FREQ_GHZ = 6.7
REGION_MARGIN_GHZ = 0.5

# 4. REPORT SETTINGS
# List of frequencies (in GHz) to extract for the text report
REPORT_FREQUENCIES_GHZ = [2.4, 5.0, 6.7, 8.0]

# 5. OUTPUT SETTINGS
OUTPUT_FILENAME_PREFIX = "Combined_Modes"

# ==============================================================================
# ====================== END OF CONFIGURATION SECTION ==========================
# ==============================================================================

def load_and_plot():
    # 1. Setup Figures
    # Fig 1: S-Parameters (2x2 Grid)
    fig1, axs = plt.subplots(2, 2, figsize=(12, 10))
    fig1.suptitle(f'S-Parameters Analysis - All Modes', fontsize=16)

    # Fig 2: Stability
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.set_title(f'Stability Criteria (K-Factor / Mu) - All Modes', fontsize=14)

    # Calculate bounds
    lower_bound_ghz = CENTER_FREQ_GHZ - REGION_MARGIN_GHZ
    upper_bound_ghz = CENTER_FREQ_GHZ + REGION_MARGIN_GHZ

    # Define S-Param Subplot Mapping: (Row, Col, DataColX, DataColY, Title)
    sp_subplots_config = [
        (0, 0, 0, 1, 'S11 (dB)'),
        (0, 1, 2, 3, 'S12 (dB)'),
        (1, 0, 4, 5, 'S21 (dB)'),
        (1, 1, 6, 7, 'S22 (dB)')
    ]

    # Initialize Report Data
    report_lines = []
    report_lines.append(f"S-PARAMETERS & STABILITY REPORT")
    report_lines.append(f"==================================================")
    
    # 2. Loop through each mode and plot
    for mode, filename in FILES_MAP.items():
        print(f"Processing Mode: {mode} | File: {filename}")
        
        if not os.path.exists(filename):
            print(f"  Warning: File '{filename}' not found. Skipping.")
            continue

        try:
            # Load Data (Skip 6 header lines)
            df = pd.read_csv(filename, skiprows=6, header=None)
            df = df.apply(pd.to_numeric, errors='coerce')
        except Exception as e:
            print(f"  Error reading {filename}: {e}")
            continue

        # Helper to extract X(GHz) and Y
        def get_data(col_x, col_y):
            return df.iloc[:, col_x] / 1e9, df.iloc[:, col_y]

        current_color = COLORS.get(mode, 'black')
        
        # --- Report Header for this Mode ---
        report_lines.append(f"\nMODE: {mode} (File: {filename})")
        header = f"{'Freq(GHz)':<12} | {'S11(dB)':<10} | {'S12(dB)':<10} | {'S21(dB)':<10} | {'S22(dB)':<10} | {'Stability':<10}"
        report_lines.append(header)
        report_lines.append("-" * len(header))

        # Dictionary to store interpolated values for the report
        current_mode_values = {freq: {} for freq in REPORT_FREQUENCIES_GHZ}

        # Plot S-Parameters on Fig 1 and collect data for report
        s_param_indices = [(0, 1, 'S11'), (2, 3, 'S12'), (4, 5, 'S21'), (6, 7, 'S22')]
        
        for r, c, x_idx, y_idx, title in sp_subplots_config:
            x, y = get_data(x_idx, y_idx)
            ax = axs[r, c]
            ax.plot(x, y, color=current_color, linewidth=1.5, label=f'Mode {mode}')
            ax.set_title(title, fontsize=12, fontweight='bold')
            
            # Interpolate for report
            # Find the param name based on indices to store correctly
            param_name = next(p[2] for p in s_param_indices if p[0] == x_idx)
            interp_vals = np.interp(REPORT_FREQUENCIES_GHZ, x, y)
            for f, val in zip(REPORT_FREQUENCIES_GHZ, interp_vals):
                current_mode_values[f][param_name] = val

        # Plot Stability on Fig 2
        x_stab, y_stab = get_data(8, 9)
        
        # CLEAN DATA: Remove NaNs to ensure fill_between and plotting work perfectly
        # Create a mask where both X and Y are finite
        valid_mask = np.isfinite(x_stab) & np.isfinite(y_stab)
        x_stab_np = x_stab[valid_mask].to_numpy()
        y_stab_np = y_stab[valid_mask].to_numpy()
        
        if len(x_stab_np) > 0:
            # 1. Plot the main curve
            ax2.plot(x_stab_np, y_stab_np, color=current_color, linewidth=2, label=f'Mode {mode}', zorder=10)
            
            # 2. Highlight Unstable Region (Stability < 1)
            # Use 'gray' instead of 'darkgrey' for better visibility
            # interpolate=True ensures the fill goes exactly to the intersection point
            ax2.fill_between(x_stab_np, 1.0, y_stab_np, 
                            where=(y_stab_np < 1.0), 
                            color='gray', 
                            alpha=0.6, 
                            interpolate=True,
                            zorder=5) # zorder 5 puts it above grid (0.5) but below lines (10)
            
            # 3. EXTRA SAFETY: Plot markers for points < 1
            # If a single point dips below 1, fill_between might have 0 width. 
            # This ensures it is visible.
            unstable_indices = y_stab_np < 1.0
            if np.any(unstable_indices):
                ax2.scatter(x_stab_np[unstable_indices], y_stab_np[unstable_indices], 
                           color='red', s=20, marker='o', zorder=15, label='_nolegend_')

        # Interpolate Stability for report (using original data for interp is fine, or cleaned)
        stab_interp = np.interp(REPORT_FREQUENCIES_GHZ, x_stab, y_stab)
        for f, val in zip(REPORT_FREQUENCIES_GHZ, stab_interp):
            current_mode_values[f]['Stability'] = val

        # Write lines to report buffer
        for freq in REPORT_FREQUENCIES_GHZ:
            vals = current_mode_values[freq]
            line = f"{freq:<12.4f} | {vals['S11']:<10.2f} | {vals['S12']:<10.2f} | {vals['S21']:<10.2f} | {vals['S22']:<10.2f} | {vals['Stability']:<10.4f}"
            report_lines.append(line)

    # 3. Apply Styling, Regions, and Legends to All Plots
    
    # --- Process S-Parameter Subplots ---
    for r in range(2):
        for c in range(2):
            ax = axs[r, c]
            ax.axvspan(lower_bound_ghz, upper_bound_ghz, color='grey', alpha=0.3)
            ax.axvline(CENTER_FREQ_GHZ, color='red', linestyle='--', linewidth=1.5, alpha=0.8)
            ax.set_xlabel('Frequency (GHz)')
            ax.set_ylabel('Magnitude (dB)')
            ax.grid(True, which='both', linestyle='--', alpha=0.7)
            ax.legend()

    fig1.tight_layout()

    # --- Process Stability Plot ---
    ax2.axvspan(lower_bound_ghz, upper_bound_ghz, color='grey', alpha=0.3, label=f'Target Band')
    ax2.axvline(CENTER_FREQ_GHZ, color='red', linestyle='--', linewidth=1.5, alpha=0.8)
    
    # Add a dummy artist for the legend to explain the dark grey area/red dots
    ax2.fill_between([], [], color='gray', alpha=0.6, label='Unstable (< 1)')
    
    ax2.set_xlabel('Frequency (GHz)', fontsize=12)
    ax2.set_ylabel('Stability Measure', fontsize=12)
    # Set Grid zorder low so fills cover it
    ax2.grid(True, which='both', linestyle='--', alpha=0.7, zorder=0)
    ax2.legend()

    # 4. Save Files
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    # Save Images
    save_path1 = os.path.join(script_dir, f"{OUTPUT_FILENAME_PREFIX}_S_Parameters.png")
    fig1.savefig(save_path1, dpi=300)
    print(f"Saved S-Parameters plot to: {save_path1}")

    save_path2 = os.path.join(script_dir, f"{OUTPUT_FILENAME_PREFIX}_Stability.png")
    fig2.savefig(save_path2, dpi=300)
    print(f"Saved Stability plot to: {save_path2}")

    # Save Text Report
    report_path = os.path.join(script_dir, f"{OUTPUT_FILENAME_PREFIX}_Report.txt")
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    print(f"Saved Report to: {report_path}")

    plt.show()

if __name__ == "__main__":
    load_and_plot()