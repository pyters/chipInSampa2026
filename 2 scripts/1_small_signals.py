import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# ==============================================================================
# ======================== USER CONFIGURATION SECTION ==========================
# ==============================================================================

# 1. FREQUENCY OF ANALYSES (Standard value: 6.7 GHz)
CENTER_FREQ_GHZ = 6.7

# 2. FREQUENCY BAND SETTINGS
# +freq and -freq margins where the band shall be defined 
# This will be plotted as a light gray area around the center frequency.
BAND_MARGIN_GHZ = 0.5  

# 3. LIST OF FREQUENCIES OF INTEREST (Standard values: 2 to 10 GHz)
REPORT_FREQUENCIES_GHZ = [2.0, 3.0, 4.0, 5.0, 6.0, CENTER_FREQ_GHZ, 7.0, 8.0, 9.0, 10.0]

# 4. DIRECTORY SETTINGS
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
INPUT_DIR = os.path.join(SCRIPT_DIR, '..', '1 raw results', '1 s parameters')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, '..', '3 outputs', '1 s parameters')

# 5. MODES & STYLING COLORS
FILES_MAP = {
    '01': 'spParameters_mode01.vcsv',
    '10': 'spParameters_mode10.vcsv',
    '11': 'spParameters_mode11.vcsv'
}
COLORS = {
    '01': '#1f77b4', # Blue
    '10': '#ff7f0e', # Orange
    '11': '#2ca02c'  # Green
}

# 6. FIGURE SIZES AND FONTS
FIGSIZE_2X2 = (12, 10)
FIGSIZE_SINGLE = (8, 6)
FONT_SIZE_TITLE = 16
FONT_SIZE_SUBTITLE = 12
FONT_SIZE_AXIS = 10
FONT_SIZE_LEGEND = 10

# ==============================================================================
# ====================== END OF CONFIGURATION SECTION ==========================
# ==============================================================================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_3db_drop_freqs(freq, s21):
    max_idx = np.argmax(s21)
    s21_max = s21[max_idx]
    target_val = s21_max - 3.0
    
    shifted = s21 - target_val
    crossings = []
    sign_changes = np.where(np.diff(np.sign(shifted)))[0]
    for c in sign_changes:
        x0, x1 = freq[c], freq[c+1]
        y0, y1 = shifted[c], shifted[c+1]
        if y1 != y0:
            cross_x = x0 - y0 * (x1 - x0) / (y1 - y0)
            crossings.append(cross_x)
            
    f_max = freq[max_idx]
    lower_cross = [cx for cx in crossings if cx < f_max]
    upper_cross = [cx for cx in crossings if cx > f_max]
    
    f_low = lower_cross[-1] if lower_cross else float('NaN')
    f_high = upper_cross[0] if upper_cross else float('NaN')
    
    return f_low, f_high, s21_max

def main():
    ensure_dir(OUTPUT_DIR)
    
    # Setup Figures: 2x2 S-Parameters and Stability
    fig1, axs = plt.subplots(2, 2, figsize=FIGSIZE_2X2)
    fig1.suptitle('S-Parameters Analysis - All Modes', fontsize=FONT_SIZE_TITLE)

    fig2, ax2 = plt.subplots(figsize=FIGSIZE_SINGLE)
    ax2.set_title('Stability Criteria - All Modes', fontsize=FONT_SIZE_TITLE)

    # Setup Individual S-Parameter Figures (will not be shown interactively)
    fig_single = {
        'S11': plt.subplots(figsize=FIGSIZE_SINGLE),
        'S12': plt.subplots(figsize=FIGSIZE_SINGLE),
        'S21': plt.subplots(figsize=FIGSIZE_SINGLE),
        'S22': plt.subplots(figsize=FIGSIZE_SINGLE)
    }

    lower_bound_ghz = CENTER_FREQ_GHZ - BAND_MARGIN_GHZ
    upper_bound_ghz = CENTER_FREQ_GHZ + BAND_MARGIN_GHZ

    sp_subplots_config = [
        (0, 0, 0, 1, 'S11'),
        (0, 1, 2, 3, 'S12'),
        (1, 0, 4, 5, 'S21'),
        (1, 1, 6, 7, 'S22')
    ]

    header_lines = []
    header_lines.append("=" * 80)
    header_lines.append(" " * 25 + "SMALL SIGNALS ASCII REPORT")
    header_lines.append("=" * 80)
    header_lines.append(f"Analysis Center Frequency : {CENTER_FREQ_GHZ} GHz")
    header_lines.append(f"Target Band Margin        : +/- {BAND_MARGIN_GHZ} GHz")
    header_lines.append(f"Target Band Range         : {lower_bound_ghz} GHz to {upper_bound_ghz} GHz\n")

    # This will hold the detailed output for each mode
    mode_report_lines = []

    # Data structure for summary table
    summary_data = {mode: {} for mode in FILES_MAP.keys()}

    for mode, filename in FILES_MAP.items():
        filepath = os.path.join(INPUT_DIR, filename)
        if not os.path.exists(filepath):
            print(f"File not found, skipping mode {mode}: {filepath}")
            continue
            
        try:
            df = pd.read_csv(filepath, skiprows=6, header=None)
            df = df.apply(pd.to_numeric, errors='coerce')
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            continue

        def get_data(col_x, col_y):
            valid_mask = np.isfinite(df.iloc[:, col_x]) & np.isfinite(df.iloc[:, col_y])
            return df.iloc[:, col_x][valid_mask].to_numpy() / 1e9, df.iloc[:, col_y][valid_mask].to_numpy()

        color = COLORS.get(mode, 'black')
        
        mode_report_lines.append(f"--- MODE {mode} ---")
        mode_report_lines.append(f"{'Freq(GHz)':<12} | {'S11(dB)':<10} | {'S12(dB)':<10} | {'S21(dB)':<10} | {'S22(dB)':<10} | {'Stability':<10}")
        mode_report_lines.append("-" * 75)

        interp_dict = {f: {} for f in REPORT_FREQUENCIES_GHZ}
        
        freq_s21 = None
        s21_data = None
        
        # Plot S-Parameters (2x2 Grid + Individual)
        for r, c, x_idx, y_idx, param_name in sp_subplots_config:
            x, y = get_data(x_idx, y_idx)
            if len(x) == 0: continue
            
            # 2x2 Plot
            axs[r, c].plot(x, y, color=color, linewidth=1.5, label=f'Mode {mode}')
            axs[r, c].set_title(f'{param_name} (dB)', fontsize=FONT_SIZE_SUBTITLE, fontweight='bold')
            
            # Single Plot
            f_single, ax_single = fig_single[param_name]
            ax_single.plot(x, y, color=color, linewidth=1.5, label=f'Mode {mode}')
            
            if param_name == 'S21':
                freq_s21 = x
                s21_data = y
                
            interp_vals = np.interp(REPORT_FREQUENCIES_GHZ, x, y)
            for f, val in zip(REPORT_FREQUENCIES_GHZ, interp_vals):
                interp_dict[f][param_name] = val

            # Store in summary data
            summary_data[mode][param_name] = interp_dict[CENTER_FREQ_GHZ].get(param_name, float('nan'))

        # Plot Stability
        x_stab, y_stab = get_data(8, 9)
        if len(x_stab) > 0:
            ax2.plot(x_stab, y_stab, color=color, linewidth=2, label=f'Mode {mode}')
            
            stab_interp = np.interp(REPORT_FREQUENCIES_GHZ, x_stab, y_stab)
            for f, val in zip(REPORT_FREQUENCIES_GHZ, stab_interp):
                interp_dict[f]['Stability'] = val

            summary_data[mode]['Stability'] = interp_dict[CENTER_FREQ_GHZ].get('Stability', float('nan'))

            # Draw report rows for this mode
            for f in REPORT_FREQUENCIES_GHZ:
                vals = interp_dict[f]
                s11 = vals.get('S11', float('nan'))
                s12 = vals.get('S12', float('nan'))
                s21 = vals.get('S21', float('nan'))
                s22 = vals.get('S22', float('nan'))
                stab = vals.get('Stability', float('nan'))
                line = f"{f:<12.4f} | {s11:<10.2f} | {s12:<10.2f} | {s21:<10.2f} | {s22:<10.2f} | {stab:<10.4f}"
                mode_report_lines.append(line)

        # Append S21 3dB drop info
        if freq_s21 is not None and s21_data is not None:
            f_low, f_high, s21_max = get_3db_drop_freqs(freq_s21, s21_data)
            
            summary_data[mode]['S21_max'] = s21_max
            summary_data[mode]['f_low'] = f_low
            summary_data[mode]['f_high'] = f_high
            
            mode_report_lines.append("-" * 75)
            mode_report_lines.append(f" > S21 MAX         : {s21_max:.2f} dB (approx peak)")
            mode_report_lines.append(f" > S21 -3dB (LOW)  : {f_low:.4f} GHz" if not np.isnan(f_low) else " > S21 -3dB (LOW)  : N/A")
            mode_report_lines.append(f" > S21 -3dB (HIGH) : {f_high:.4f} GHz" if not np.isnan(f_high) else " > S21 -3dB (HIGH) : N/A")
            mode_report_lines.append(" \n")

    # --- Generate Summary Table ---
    summary_lines = []
    summary_lines.append("=" * 80)
    summary_lines.append(f" SUMMARY TABLE AT CENTER FREQUENCY ({CENTER_FREQ_GHZ} GHz)")
    summary_lines.append("=" * 80)
    
    modes_sorted = sorted(FILES_MAP.keys())
    header_row = f"{'Parameter':<20}" + "".join([f"| Mode {m:<8} " for m in modes_sorted])
    summary_lines.append(header_row)
    summary_lines.append("-" * len(header_row))
    
    params_to_print = [
        ('S11 (dB)', 'S11', '{:.2f}'),
        ('S12 (dB)', 'S12', '{:.2f}'),
        ('S21 (dB)', 'S21', '{:.2f}'),
        ('S22 (dB)', 'S22', '{:.2f}'),
        ('Stability', 'Stability', '{:.4f}'),
        ('S21 -3dB (LOW) GHz', 'f_low', '{:.4f}'),
        ('S21 -3dB (HIGH) GHz', 'f_high', '{:.4f}')
    ]
    
    # Store data for pd.DataFrame CSV export
    csv_data = {'Parameter': [label for label, _, _ in params_to_print]}
    for m in modes_sorted:
        csv_data[f"Mode_{m}"] = []
        
    for label, key, fmt in params_to_print:
        row_str = f"{label:<20}"
        for m in modes_sorted:
            val = summary_data[m].get(key, float('nan'))
            
            # Fill string table
            val_str = fmt.format(val) if not np.isnan(val) else "N/A"
            row_str += f"| {val_str:<12} "
            
            # Fill CSV data
            csv_data[f"Mode_{m}"].append(val)
            
        summary_lines.append(row_str)
    
    summary_lines.append("=" * 80 + "\n")
    
    # Combine Report Text
    final_report_lines = header_lines + summary_lines + mode_report_lines

    # --- Finalize 2x2 Plot ---
    for r in range(2):
        for c in range(2):
            ax = axs[r, c]
            ax.axvspan(lower_bound_ghz, upper_bound_ghz, color='lightgray', alpha=0.5)
            ax.axvline(CENTER_FREQ_GHZ, color='red', linestyle='--', linewidth=1.0)
            ax.set_xlabel('Frequency (GHz)', fontsize=FONT_SIZE_AXIS)
            ax.set_ylabel('Magnitude (dB)', fontsize=FONT_SIZE_AXIS)
            ax.tick_params(axis='both', which='major', labelsize=FONT_SIZE_AXIS)
            ax.grid(True, which='both', linestyle='--', alpha=0.6)
            ax.legend(fontsize=FONT_SIZE_LEGEND)
    fig1.tight_layout()

    # --- Finalize Stability Plot ---
    ax2.axvspan(lower_bound_ghz, upper_bound_ghz, color='lightgray', alpha=0.5, label='Target Band')
    ax2.axvline(CENTER_FREQ_GHZ, color='red', linestyle='--', linewidth=1.0)
    ax2.axhline(1.0, color='black', linestyle='-.', linewidth=2.0, label='Stability Limit = 1')
    ax2.set_xlabel('Frequency (GHz)', fontsize=FONT_SIZE_AXIS)
    ax2.set_ylabel('Stability Measure', fontsize=FONT_SIZE_AXIS)
    ax2.tick_params(axis='both', which='major', labelsize=FONT_SIZE_AXIS)
    ax2.grid(True, which='both', linestyle='--', alpha=0.6)
    ax2.legend(fontsize=FONT_SIZE_LEGEND)
    fig2.tight_layout()

    # Save Components
    save_prefix = os.path.join(OUTPUT_DIR, "Small_Signals")
    
    fig1_path = f"{save_prefix}_S_Parameters.png"
    fig1.savefig(fig1_path, dpi=300)
    print(f"Saved 2x2 S-Parameters plot to: {fig1_path}")

    fig2_path = f"{save_prefix}_Stability.png"
    fig2.savefig(fig2_path, dpi=300)
    print(f"Saved Stability plot to: {fig2_path}")

    # --- Finalize and Save Individual S-Parameter Plots ---
    for param_name in ['S11', 'S12', 'S21', 'S22']:
        f_single, ax_single = fig_single[param_name]
        
        ax_single.axvspan(lower_bound_ghz, upper_bound_ghz, color='lightgray', alpha=0.5)
        ax_single.axvline(CENTER_FREQ_GHZ, color='red', linestyle='--', linewidth=1.0)
        ax_single.set_title(f'{param_name} Analysis', fontsize=FONT_SIZE_TITLE, fontweight='bold')
        ax_single.set_xlabel('Frequency (GHz)', fontsize=FONT_SIZE_AXIS)
        ax_single.set_ylabel('Magnitude (dB)', fontsize=FONT_SIZE_AXIS)
        ax_single.tick_params(axis='both', which='major', labelsize=FONT_SIZE_AXIS)
        ax_single.grid(True, which='both', linestyle='--', alpha=0.6)
        ax_single.legend(fontsize=FONT_SIZE_LEGEND)
        f_single.tight_layout()
        
        single_path = f"{save_prefix}_{param_name}_Standalone.png"
        f_single.savefig(single_path, dpi=300)
        print(f"Saved Standalone {param_name} plot to: {single_path}")
        
        # Close to prevent them from showing interactively
        plt.close(f_single)

    # Save Text Report
    report_path = f"{save_prefix}_Report.txt"
    with open(report_path, 'w') as f:
        f.write('\n'.join(final_report_lines))
    print(f"Saved Report to: {report_path}")

    # Save CSV Report
    csv_path = f"{save_prefix}_Summary_Data.csv"
    df_csv = pd.DataFrame(csv_data)
    df_csv.to_csv(csv_path, index=False)
    print(f"Saved Summary CSV to: {csv_path}")

    # Show realtime (Only the 2x2 and Stability plots are left open)
    plt.show()

if __name__ == "__main__":
    main()
