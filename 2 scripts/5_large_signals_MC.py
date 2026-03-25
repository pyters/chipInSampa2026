import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from scipy.stats import gaussian_kde

# ==============================================================================
# ======================== USER CONFIGURATION SECTION ==========================
# ==============================================================================

# 1. DIRECTORY SETTINGS
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
# The user specified directories relative to the root or current script location
INPUT_DIR = os.path.join(SCRIPT_DIR, '..', '1 raw results', '5 large signals MC')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, '..', '3 outputs', '5 large signals MC')

# 2. MODES & STYLING COLORS
# Filenames in the input folder
FILES_MAP = {
    '01': 'MonteCarlo.5.MMPA_V1_v15tb_01.MC.csv',
    '10': 'MonteCarlo.5.MMPA_V1_v15tb_10.MC.csv',
    '11': 'MonteCarlo.5.MMPA_V1_v15tb_11.MC.csv'
}

COLORS = {
    '01': '#1f77b4', # Blue
    '10': '#ff7f0e', # Orange
    '11': '#2ca02c'  # Green
}

# 3. METRICS OF INTEREST
METRICS = {
    'hb_gainAt-20dbm_value': 'Linear Gain (dB)',
    'hb_ocp1dbm_value': 'OCP1dBm (dBm)',
    'hb_peakPAE_value': 'Peak PAE (%)',
    'hb_PAEAtOcp1dbm': 'PAE @ OCP1dBm (%)'
}

# 4. PLOT SETTINGS
BINS = 20
FIGSIZE_2X2 = (14, 11)
FONT_SIZE_TITLE = 18
FONT_SIZE_SUBTITLE = 14
FONT_SIZE_AXIS = 12
FONT_SIZE_LEGEND = 12

# ==============================================================================
# ====================== END OF CONFIGURATION SECTION ==========================
# ==============================================================================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def calculate_stats(data):
    return {
        'Min': np.min(data),
        'Max': np.max(data),
        'Avg': np.mean(data),
        'Median': np.median(data),
        'Std': np.std(data)
    }

def main():
    ensure_dir(OUTPUT_DIR)
    
    # Data storage
    all_data = {mode: None for mode in FILES_MAP.keys()}
    
    # Load data
    print("Loading data...")
    for mode, filename in FILES_MAP.items():
        filepath = os.path.join(INPUT_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Warning: File not found for Mode {mode}: {filepath}")
            continue
        
        try:
            df = pd.read_csv(filepath)
            all_data[mode] = df
            print(f" > Loaded Mode {mode} ({len(df)} points)")
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            continue

    # Plotting setup
    fig, axs = plt.subplots(2, 2, figsize=FIGSIZE_2X2)
    fig.suptitle('Monte Carlo Analysis - Power Amplifier Operation Modes', fontsize=FONT_SIZE_TITLE, fontweight='bold')
    
    # Statistics storage
    stats_results = {}

    # Iterate over metrics and plot
    print("Generating plots and calculating statistics...")
    for i, (metric_key, metric_label) in enumerate(METRICS.items()):
        # 1. 2x2 Grid Plot (Subplot)
        ax = axs[i // 2, i % 2]
        ax.set_title(metric_label, fontsize=FONT_SIZE_SUBTITLE, fontweight='bold')
        
        # 2. Standalone Plot for this metric
        fig_ind, ax_ind = plt.subplots(figsize=(10, 7))
        ax_ind.set_title(f'Monte Carlo Analysis - {metric_label}', fontsize=FONT_SIZE_SUBTITLE, fontweight='bold')
        
        metric_stats = {}
        
        for mode in sorted(FILES_MAP.keys()):
            df = all_data[mode]
            if df is None or metric_key not in df.columns:
                continue
            
            data = df[metric_key].dropna().values
            color = COLORS.get(mode, 'black')
            
            # Plot Histograms
            ax.hist(data, bins=BINS, density=True, alpha=0.3, color=color, label=f'Mode {mode}')
            ax_ind.hist(data, bins=BINS, density=True, alpha=0.3, color=color, label=f'Mode {mode}')
            
            # PDF (KDE) lines
            try:
                kde = gaussian_kde(data)
                x_range = np.linspace(np.min(data), np.max(data), 200)
                
                # KDE on Grid
                ax.plot(x_range, kde(x_range), color=color, linewidth=2.5)
                
                # KDE on Independent Figure
                ax_ind.plot(x_range, kde(x_range), color=color, linewidth=2.5)
            except Exception as e:
                print(f"KDE failed for {metric_key} in Mode {mode}: {e}")
            
            # Calculate Statistics
            metric_stats[mode] = calculate_stats(data)
            
        # Finalize Grid Subplot
        ax.set_xlabel('Value', fontsize=FONT_SIZE_AXIS)
        ax.set_ylabel('Probability Density', fontsize=FONT_SIZE_AXIS)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(fontsize=FONT_SIZE_LEGEND)
        
        # Finalize and Save Independent Plot
        ax_ind.set_xlabel('Value', fontsize=FONT_SIZE_AXIS)
        ax_ind.set_ylabel('Probability Density', fontsize=FONT_SIZE_AXIS)
        ax_ind.grid(True, linestyle='--', alpha=0.4)
        ax_ind.legend(fontsize=FONT_SIZE_LEGEND)
        fig_ind.tight_layout()
        
        # Fix filename for standalone plot
        safe_name = metric_label.replace(' ', '_').replace('(', '').replace(')', '').replace('@', 'at').replace('%', 'pct')
        ind_plot_path = os.path.join(OUTPUT_DIR, f'Monte_Carlo_{safe_name}.png')
        fig_ind.savefig(ind_plot_path, dpi=300)
        plt.close(fig_ind) # Close standalone fig to save memory
        print(f" > Saved Standalone plot: {ind_plot_path}")
        
        stats_results[metric_label] = metric_stats

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save Figure
    plot_path = os.path.join(OUTPUT_DIR, 'Monte_Carlo_Metrics_Histogram.png')
    plt.savefig(plot_path, dpi=300)
    print(f"Saved Monte Carlo plot to: {plot_path}")

    # Generate ASCII Report
    report_lines = []
    report_lines.append("=" * 115)
    report_lines.append(f"{'MONTE CARLO STATISTICAL SUMMARY':^115}")
    report_lines.append("=" * 115)
    report_lines.append("\n")

    for metric_label, modes_stats in stats_results.items():
        report_lines.append(f"Metric: {metric_label}")
        header = f"{'Mode':<10} | {'Minimum':<15} | {'Maximum':<15} | {'Average':<15} | {'Median':<15} | {'Std Dev':<15}"
        report_lines.append(header)
        report_lines.append("-" * len(header))
        
        for mode in sorted(modes_stats.keys()):
            s = modes_stats[mode]
            line = f"{mode:<10} | {s['Min']:<15.4f} | {s['Max']:<15.4f} | {s['Avg']:<15.4f} | {s['Median']:<15.4f} | {s['Std']:<15.4f}"
            report_lines.append(line)
        report_lines.append("\n")

    report_lines.append("=" * 115)
    
    # Save Report
    report_path = os.path.join(OUTPUT_DIR, 'Monte_Carlo_Statistics_Report.txt')
    with open(report_path, 'w') as f:
        f.write("\n".join(report_lines))
    print(f"Saved Monte Carlo report to: {report_path}")

    # Show results
    plt.show()

if __name__ == "__main__":
    main()
