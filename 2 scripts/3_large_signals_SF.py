import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re

# ==============================================================================
# ======================== USER CONFIGURATION SECTION ==========================
# ==============================================================================

# 1. DIRECTORY SETTINGS
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
INPUT_FILE = os.path.join(SCRIPT_DIR, '..', '1 raw results', '3 large signals freq sweep', 'data freq sweep all modes.csv')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, '..', '3 outputs', '3 large signal freq sweep')

# 2. MODES & STYLING COLORS
MODE_MAP = {
    'MMPA_V1_v15tb_11': '11',
    'MMPA_V1_v15tb_10': '10',
    'MMPA_V1_v15tb_01': '01'
}

COLORS = {
    '01': '#1f77b4', # Blue
    '10': '#ff7f0e', # Orange
    '11': '#2ca02c'  # Green
}

# 3. FIGURE SIZES AND FONTS
FIGSIZE = (10, 8)
FONT_SIZE_TITLE = 16
FONT_SIZE_AXIS = 12
FONT_SIZE_LEGEND = 10

# 4. METRICS TO PLOT
METRICS = {
    'hb_ocp1dbm_value': 'OCP1dBm (dBm)',
    'hb_peakPAE_value': 'Peak PAE (%)',
    'hb_gainAt-20dbm_value': 'Linear Gain at -20dBm (dB)',
    'hb_PAEAtOcp1dbm': 'PAE at OCP1dBm (%)'
}

# 5. VERTICAL LINE
FREQ_VLINE = 6.7

# ==============================================================================
# ====================== END OF CONFIGURATION SECTION ==========================
# ==============================================================================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def parse_data(filepath):
    """Parses the specific CSV format and extracts relevant data."""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return None
        
    data = []
    current_freq = None
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            # Check for frequency parameter
            if line.startswith('Parameters: input_port_f='):
                # Extract frequency value
                # e.g., "Parameters: input_port_f=6G,,,,,," -> "6G"
                match = re.search(r'input_port_f=([\d\.]+)(G|M|k)?', line)
                if match:
                    val = float(match.group(1))
                    unit = match.group(2)
                    if unit == 'G':
                        current_freq = val
                    elif unit == 'M':
                        current_freq = val / 1000.0
                    elif unit == 'k':
                        current_freq = val / 1e6
                    else:
                        current_freq = val / 1e9 # assume Hz if no unit, convert to GHz, or just val, adjust if necessary
                continue
                
            # Parse data lines
            parts = line.split(',')
            if len(parts) >= 4:
                # Point,Test,Output,Nominal
                point = parts[0]
                test = parts[1]
                output = parts[2]
                nominal_str = parts[3]
                
                # We only care about mapped modes and mapped metrics
                if test in MODE_MAP and output in METRICS:
                    try:
                        nominal = float(nominal_str)
                        data.append({
                            'Freq_GHz': current_freq,
                            'Mode': MODE_MAP[test],
                            'Metric': output,
                            'Value': nominal
                        })
                    except ValueError:
                        pass
                        
    return pd.DataFrame(data)

def main():
    ensure_dir(OUTPUT_DIR)
    
    print("Parsing data...")
    df = parse_data(INPUT_FILE)
    
    if df is None or df.empty:
        print("No valid data found or file missing.")
        return
        
    print(f"Successfully loaded {len(df)} data points.")
    
    # Get sorted list of modes and unique frequencies for axis limits
    modes_found = sorted(df['Mode'].unique())
    freqs = df['Freq_GHz'].unique()
    
    freq_min, freq_max = freqs.min() * 0.98, freqs.max() * 1.02
    
    # Helper to plot a single metric properly
    def plot_metric_on_ax(ax, metric_key, title_override=None, is_subplot=False):
        metric_data = df[df['Metric'] == metric_key]
        for mode in modes_found:
            mode_data = metric_data[metric_data['Mode'] == mode].sort_values('Freq_GHz')
            color = COLORS.get(mode, 'black')
            ax.plot(mode_data['Freq_GHz'], mode_data['Value'], label=f'Mode {mode}', color=color, linewidth=1.2, marker='o', markersize=4)
            
        ax.axvline(x=FREQ_VLINE, color='red', linestyle='--', linewidth=2, alpha=0.7, label=f'{FREQ_VLINE} GHz')
        
        ax.set_xlabel('Frequency (GHz)', fontsize=FONT_SIZE_AXIS if not is_subplot else 10)
        ylabel = METRICS[metric_key]
        ax.set_ylabel(ylabel, fontsize=FONT_SIZE_AXIS if not is_subplot else 10)
        ax.set_title(title_override if title_override else ylabel, fontsize=FONT_SIZE_TITLE if not is_subplot else 12)
        ax.grid(True, which='both', linestyle='--', alpha=0.6)
        
        # Avoid duplicate legend entries for vertical line and modes
        from matplotlib.lines import Line2D
        handles, labels = ax.get_legend_handles_labels()
        unique = [(h, l) for i, (h, l) in enumerate(zip(handles, labels)) if l not in labels[:i]]
        ax.legend([h for h,l in unique], [l for h,l in unique], fontsize=FONT_SIZE_LEGEND if not is_subplot else 8)

    # --- PLOT 1: 2x2 Grid of all metrics ---
    print("Generating 2x2 grid plot...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    metrics_list = list(METRICS.keys())
    for i, metric_key in enumerate(metrics_list):
        ax = axes[i]
        plot_metric_on_ax(ax, metric_key, is_subplot=True)
        
    plt.tight_layout()
    grid_path = os.path.join(OUTPUT_DIR, 'All_Metrics_2x2.png')
    plt.savefig(grid_path, dpi=300)
    print(f"Saved {grid_path}")
    
    # --- PLOT 2-5: Individual Metric Plots ---
    for metric_key in metrics_list:
        print(f"Generating individual plot for {metric_key}...")
        fig, ax = plt.subplots(figsize=FIGSIZE)
        plot_metric_on_ax(ax, metric_key)
        plt.tight_layout()
        
        # Clean up filename
        safe_name = metric_key.replace('-', '_').replace(' ', '_')
        ind_path = os.path.join(OUTPUT_DIR, f'{safe_name}.png')
        plt.savefig(ind_path, dpi=300)
        print(f"Saved {ind_path}")
        
    print("All plots generated successfully!")
    print("Opening plot windows...")
    
    # Show plots if executed directly
    plt.show()
    print("Done.")
    
if __name__ == "__main__":
    main()
