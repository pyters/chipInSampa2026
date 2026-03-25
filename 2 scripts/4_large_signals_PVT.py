import pandas as pd
import matplotlib.pyplot as plt
import os
import re

# File paths
input_file = '/home/pyter/Projects/phd/chip in sampa 2026/1 raw results/4 large signals PVT/PVT.csv'
output_dir = '/home/pyter/Projects/phd/chip in sampa 2026/3 outputs/4 large signals PVT'
os.makedirs(output_dir, exist_ok=True)

# Context information
modes_map = {
    'MMPA_V1_v15tb_01': '01',
    'MMPA_V1_v15tb_10': '10',
    'MMPA_V1_v15tb_11': '11'
}

metrics_of_interest = [
    'hb_ocp1dbm_value',
    'hb_peakPAE_value',
    'hb_gainAt-20dbm_value',
    'hb_PAEAtOcp1dbm'
]

temp_map = {
    '0': -40,
    '1': 27,
    '2': 125
}

# 1. PARSING THE CSV
data = []
current_vdd = None

with open(input_file, 'r') as f:
    lines = f.readlines()

for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # Detect VDD block
    vdd_match = re.search(r'Parameters: vdd=([\d\.]+)', line)
    if vdd_match:
        current_vdd = float(vdd_match.group(1))
        continue
    
    parts = line.split(',')
    if len(parts) < 21: # At least up to SS_2
        continue
    
    if not parts[0].isdigit():
        continue
    
    test_label = parts[1]
    metric_label = parts[2]
    
    if test_label in modes_map and metric_label in metrics_of_interest:
        mode = modes_map[test_label]
        
        # Nominal value (Ignore as requested for plots)
        # But we still parse it for the consolidated table
        nom_val = parts[3].strip()
        if nom_val and nom_val != '':
            try:
                data.append({
                    'Mode': mode,
                    'Process': 'Nominal',
                    'Voltage': current_vdd,
                    'Temperature': 27,
                    'Metric': metric_label,
                    'Value': float(nom_val)
                })
            except ValueError:
                pass
        
        process_indices = {
            'FF': [9, 10, 11],
            'FS': [12, 13, 14],
            'SF': [15, 16, 17],
            'SS': [18, 19, 20]
        }
        
        for proc, indices in process_indices.items():
            for i, idx in enumerate(indices):
                if idx < len(parts):
                    val = parts[idx].strip()
                    if val and val != '':
                        try:
                            data.append({
                                'Mode': mode,
                                'Process': proc,
                                'Voltage': current_vdd,
                                'Temperature': temp_map[str(i)],
                                'Metric': metric_label,
                                'Value': float(val)
                            })
                        except ValueError:
                            pass

df = pd.DataFrame(data)

# --- NEW: Calculate Delta Gain ---
# delta_gain = max(gain) - min(gain) for each corner across all modes
gain_df = df[df['Metric'] == 'hb_gainAt-20dbm_value']
if not gain_df.empty:
    delta_gain = gain_df.groupby(['Temperature', 'Voltage', 'Process'])['Value'].agg(lambda x: x.max() - x.min()).reset_index()
    delta_gain['Metric'] = 'delta_gain'
    delta_gain['Mode'] = 'delta'
    df = pd.concat([df, delta_gain], ignore_index=True)

# Save consolidated table
csv_output = os.path.join(output_dir, 'PVT_consolidated.csv')
df.to_csv(csv_output, index=False)
print(f"Consolidated table saved to {csv_output}")

# 2. REFINING FOR VARIABILITY CHARTS
# Update metrics of interest to include delta_gain
metrics_plot = metrics_of_interest + ['delta_gain']

# Filter: Remove 27°C, 2.5V, and Nominal/MC
df_plot = df[
    (df['Process'] != 'Nominal') & 
    (df['Temperature'] != 27) & 
    (df['Voltage'] != 2.5)
].copy()

# Sorting: Coarsest factor first (for nesting)
# Bottom up: Temperature -> Voltage -> Process
df_plot = df_plot.sort_values(['Temperature', 'Voltage', 'Process', 'Mode'])

# Mode colors
mode_colors = {
    '01': '#1f77b4', # Blue
    '10': '#ff7f0e', # Orange
    '11': '#2ca02c', # Green
    'delta': '#333333' # Dark Gray for delta_gain
}

metric_info = {
    'hb_ocp1dbm_value': {'label': 'OCP1dBm (dBm)', 'title': 'OCP1dBm Variability'},
    'hb_peakPAE_value': {'label': 'Peak PAE (%)', 'title': 'Peak PAE Variability'},
    'hb_gainAt-20dbm_value': {'label': 'Linear Gain (dB)', 'title': 'Gain at -20dBm Variability'},
    'hb_PAEAtOcp1dbm': {'label': 'PAE at OCP1dBm (%)', 'title': 'PAE at Max Linearity Point'},
    'delta_gain': {'label': 'Delta Gain (dB)', 'title': 'Gain Spread Across Modes (Max-Min)'}
}

# Function to draw JMP-style nested labels
def draw_nested_labels(ax, df_pivot, combinations):
    # combinations is a unique list of (Temp, Voltage, Process)
    n = len(combinations)
    
    # Position of boxes/lines
    y_base = -0.15 # Starting y position below the X axis
    row_height = 0.08
    
    # 1. Process Names (Top level of labels)
    for i, (t, v, p) in enumerate(combinations):
        ax.text(i, y_base, p, ha='center', va='center', transform=ax.get_xaxis_transform(), fontsize=11, fontweight='bold')
    # Divider for Process
    ax.plot([0, 1], [y_base + 0.04, y_base + 0.04], color='lightgray', linewidth=0.5, transform=ax.get_xaxis_transform(), clip_on=False)
    # Label for Process row (on the left)
    ax.text(-0.8, y_base, "Process", ha='right', va='center', transform=ax.get_xaxis_transform(), fontsize=10)
    
    # 2. Voltage (Middle level)
    v_groups = []
    current_v = None
    current_t = None
    start_idx = 0
    for i, (t, v, p) in enumerate(combinations):
        if v != current_v or t != current_t:
            if current_v is not None:
                v_groups.append((current_v, start_idx, i - 1))
            current_v = v
            current_t = t
            start_idx = i
    v_groups.append((current_v, start_idx, n - 1))
    
    v_y = y_base - row_height
    for v_val, s, e in v_groups:
        center = (s + e) / 2
        ax.text(center, v_y, f"{v_val}V", ha='center', va='center', transform=ax.get_xaxis_transform(), fontweight='bold', fontsize=10)
        # Vertical divider line
        if e < n - 1:
            ax.axvline(x=e + 0.5, ymin=y_base - row_height*1.5, ymax=1, color='black', linewidth=0.5, clip_on=False)
        # Horizontal lines for the "box" effect
        ax.plot([s - 0.4, e + 0.4], [v_y + 0.04, v_y + 0.04], color='black', linewidth=0.8, transform=ax.get_xaxis_transform(), clip_on=False)
    
    # Label for Voltage row (on the left)
    ax.text(-0.8, v_y, "Voltage", ha='right', va='center', transform=ax.get_xaxis_transform(), fontsize=10)

    # 3. Temperature (Bottom level)
    t_groups = []
    current_t = None
    start_idx = 0
    for i, (t, v, p) in enumerate(combinations):
        if t != current_t:
            if current_t is not None:
                t_groups.append((current_t, start_idx, i - 1))
            current_t = t
            start_idx = i
    t_groups.append((current_t, start_idx, n - 1))
    
    t_y = y_base - 2 * row_height
    for t_val, s, e in t_groups:
        center = (s + e) / 2
        ax.text(center, t_y, f"{t_val}°C", ha='center', va='center', transform=ax.get_xaxis_transform(), fontweight='bold', fontsize=11)
        # Vertical divider line
        if e < n - 1:
            ax.axvline(x=e + 0.5, ymin=y_base - 2.5 * row_height, ymax=1, color='black', linewidth=1.2, clip_on=False)
        # Horizontal lines for the "box" effect
        ax.plot([s - 0.4, e + 0.4], [t_y + 0.04, t_y + 0.04], color='black', linewidth=1, transform=ax.get_xaxis_transform(), clip_on=False)

    # Label for Temperature row (on the left)
    ax.text(-0.8, t_y, "Temperature", ha='right', va='center', transform=ax.get_xaxis_transform(), fontsize=10)

# Generate the plots
for metric in metrics_plot:
    subset = df_plot[df_plot['Metric'] == metric]
    if subset.empty:
        continue
    
    # Unique corners (Temp, Volt, Process)
    corners = subset[['Temperature', 'Voltage', 'Process']].drop_duplicates()
    corners = corners.sort_values(['Temperature', 'Voltage', 'Process'])
    combinations = list(corners.itertuples(index=False, name=None))
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # 1. Plot background boxes for each combination (showing variability over modes)
    for i, (t, v, p) in enumerate(combinations):
        corner_data = subset[(subset['Temperature'] == t) & (subset['Voltage'] == v) & (subset['Process'] == p)]
        if not corner_data.empty and len(corner_data['Mode'].unique()) > 1:
            y_min = corner_data['Value'].min()
            y_max = corner_data['Value'].max()
            # Draw a box spanning all modes in this condition
            rect = plt.Rectangle((i - 0.3, y_min), 0.6, y_max - y_min, color='lightgray', alpha=0.3, zorder=1)
            ax.add_patch(rect)
            # Add horizontal lines at top/bottom of box for better visibility
            ax.plot([i - 0.3, i + 0.3], [y_min, y_min], color='gray', linewidth=0.5, alpha=0.5, zorder=2)
            ax.plot([i - 0.3, i + 0.3], [y_max, y_max], color='gray', linewidth=0.5, alpha=0.5, zorder=2)
        
        # 2. Add dashed vertical lines between each column (Process level)
        if i < len(combinations) - 1:
            ax.axvline(x=i + 0.5, color='gray', linestyle='--', linewidth=0.5, alpha=0.3, zorder=1)

    # 3. Plot each mode with its color and connect with lines
    for mode, color in mode_colors.items():
        mode_data_all = subset[subset['Mode'] == mode]
        if not mode_data_all.empty:
            x_vals = []
            y_vals = []
            offset_map = {'01': -0.15, '10': 0, '11': 0.15, 'delta': 0}
            
            for j, (t, v, p) in enumerate(combinations):
                mode_corner_data = mode_data_all[(mode_data_all['Temperature'] == t) & 
                                                 (mode_data_all['Voltage'] == v) & 
                                                 (mode_data_all['Process'] == p)]
                if not mode_corner_data.empty:
                    x_vals.append(j + offset_map[mode])
                    y_vals.append(mode_corner_data['Value'].iloc[0])
            
            # Plot connecting line (thicker and more visible)
            if len(x_vals) > 1:
                ax.plot(x_vals, y_vals, color=color, linewidth=1.5, alpha=0.4, zorder=3)
            
            # Plot scatter points (larger size)
            ax.scatter(x_vals, y_vals, label=f'Mode {mode}', color=color, s=160, edgecolors='k', linewidth=0.5, zorder=4)
    
    # Axis styling
    ax.set_title(metric_info.get(metric, {}).get('title', metric), fontsize=18, fontweight='bold', pad=20)
    ax.set_ylabel(metric_info.get(metric, {}).get('label', 'Value'), fontsize=14)
    
    # Remove default X axis labels
    ax.set_xticks(range(len(combinations)))
    ax.set_xticklabels([])
    ax.set_xlabel('')
    
    # Add nested JMP-style labels
    draw_nested_labels(ax, subset, combinations)
    
    # Grid lines
    ax.grid(True, axis='y', linestyle='--', alpha=0.5)
    
    # Legend (deduplicate)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), title='Operating Mode', loc='upper right', frameon=True, shadow=True)
    
    # Adjust layout to make room for bottom labels
    plt.subplots_adjust(bottom=0.25)
    
    plot_file = os.path.join(output_dir, f'variability_{metric}.png')
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Plot saved to {plot_file}")

# 3. GENERATE ASCII TEXT REPORT
def generate_ascii_report(df, output_path):
    with open(output_path, 'w') as f:
        f.write("================================================================================\n")
        f.write("                         PVT SIMULATION ANALYSIS REPORT                         \n")
        f.write("================================================================================\n\n")

        metrics = [
            'hb_ocp1dbm_value',
            'hb_peakPAE_value',
            'hb_gainAt-20dbm_value',
            'hb_PAEAtOcp1dbm'
        ]
        
        # 1. Nominal Conditions (27C, 2.5V)
        f.write("1. PROCESS VARIATION UNDER NOMINAL CONDITIONS (27°C, 2.5V)\n")
        f.write("--------------------------------------------------------------------------------\n")
        
        processes = ['Nominal', 'SS', 'SF', 'FS', 'FF']
        modes = ['01', '10', '11']
        
        for mode in modes:
            f.write(f"\nMODE {mode}:\n")
            header = f"| {'Metric':<25} | {'Nom':>8} | {'SS':>8} | {'SF':>8} | {'FS':>8} | {'FF':>8} |"
            f.write(header + "\n")
            f.write("-" * len(header) + "\n")
            
            for m in metrics:
                row = f"| {m:<25} |"
                for p in processes:
                    val = df[(df['Mode'] == mode) & (df['Process'] == p) & (df['Temperature'] == 27) & (df['Voltage'] == 2.5) & (df['Metric'] == m)]['Value']
                    if not val.empty:
                        row += f" {val.iloc[0]:>8.3f} |"
                    else:
                        row += f" {'-':>8} |"
                f.write(row + "\n")
            f.write("-" * len(header) + "\n")

        # 2. Extreme Variations (All corners excluding Nominal/MC)
        f.write("\n\n2. EXTREME VARIATIONS ACROSS ALL PVT CORNERS\n")
        f.write("--------------------------------------------------------------------------------------------------------------------------------------\n")
        f.write("(Excluding Nominal and Monte Carlo variations)\n")
        
        header = f"| {'Mode':<5} | {'Metric':<22} | {'Min':>8} | {'T':>4} | {'V':>6} | {'P':>4} | {'Max':>8} | {'T':>4} | {'V':>6} | {'P':>4} | {'Range':>8} |"
        f.write("\n" + header + "\n")
        f.write("-" * len(header) + "\n")
        
        # Filter for PVT corners (SS, SF, FS, FF) at any Temp/Volt
        df_pvt = df[(df['Process'] != 'Nominal') & (df['Mode'] != 'delta')]
        
        for mode in modes:
            for m in metrics:
                subset = df_pvt[(df_pvt['Mode'] == mode) & (df_pvt['Metric'] == m)]
                if not subset.empty:
                    # Find min
                    min_idx = subset['Value'].idxmin()
                    v_min = subset.loc[min_idx, 'Value']
                    t_min = f"{subset.loc[min_idx, 'Temperature']}C"
                    vol_min = f"{subset.loc[min_idx, 'Voltage']}V"
                    p_min = subset.loc[min_idx, 'Process']
                    
                    # Find max
                    max_idx = subset['Value'].idxmax()
                    v_max = subset.loc[max_idx, 'Value']
                    t_max = f"{subset.loc[max_idx, 'Temperature']}C"
                    vol_max = f"{subset.loc[max_idx, 'Voltage']}V"
                    p_max = subset.loc[max_idx, 'Process']
                    
                    v_range = v_max - v_min
                    
                    row = f"| {mode:<5} | {m:<22} | {v_min:>8.3f} | {t_min:>4} | {vol_min:>6} | {p_min:>4} | {v_max:>8.3f} | {t_max:>4} | {vol_max:>6} | {p_max:>4} | {v_range:>8.3f} |"
                    f.write(row + "\n")
            f.write("-" * len(header) + "\n")

# 4. GENERATE TORNADO SENSITIVITY PLOTS
def generate_tornado_plots(df, output_dir):
    import numpy as np
    metrics = ['hb_ocp1dbm_value', 'hb_peakPAE_value', 'hb_gainAt-20dbm_value', 'hb_PAEAtOcp1dbm']
    modes = ['01', '10', '11']
    mode_colors = {'01': '#1f77b4', '10': '#ff7f0e', '11': '#2ca02c'}
    factors = ['Temperature', 'Voltage', 'Process']
    
    for metric in metrics:
        fig, ax = plt.subplots(figsize=(12, 8))
        y_positions = np.arange(len(factors))
        bar_height = 0.25
        
        found_data = False
        for i, mode in enumerate(modes):
            # Baseline: (Nominal, 2.5V, 27C)
            base_df = df[(df['Mode'] == mode) & (df['Process'] == 'Nominal') & (df['Voltage'] == 2.5) & (df['Temperature'] == 27) & (df['Metric'] == metric)]
            if base_df.empty: continue
            baseline = base_df['Value'].iloc[0]
            found_data = True
            
            # Sensitivity Calculation
            # 1. Temperature: Average of all processes at each T (at 2.5V)
            t_sub = df[(df['Mode'] == mode) & (df['Voltage'] == 2.5) & (df['Metric'] == metric)].groupby('Temperature')['Value'].mean()
            t_range = (t_sub.min(), t_sub.max())
            
            # 2. Voltage: All Nominal process at 27C (across VDDs)
            v_sub = df[(df['Mode'] == mode) & (df['Process'] == 'Nominal') & (df['Temperature'] == 27) & (df['Metric'] == metric)]
            v_range = (v_sub['Value'].min(), v_sub['Value'].max())
            
            # 3. Process: All processes at (2.5V, 27C)
            p_sub = df[(df['Mode'] == mode) & (df['Voltage'] == 2.5) & (df['Temperature'] == 27) & (df['Process'] != 'Nominal') & (df['Metric'] == metric)]
            p_range = (p_sub['Value'].min(), p_sub['Value'].max())
            
            ranges = [t_range, v_range, p_range]
            offsets = [0.25, 0, -0.25] # Shift modes vertically
            y_pos = y_positions + offsets[i]
            
            for j, (mi, ma) in enumerate(ranges):
                # Bar from min to max, color-coded by mode
                ax.barh(y_pos[j], ma - mi, left=mi, height=bar_height, color=mode_colors[mode], alpha=0.7, label=f'Mode {mode}' if j == 0 else "")
                
                # Limit markers (Vertical lines at edges)
                ax.plot([mi, mi], [y_pos[j] - bar_height/2, y_pos[j] + bar_height/2], color='black', linewidth=1, alpha=0.8)
                ax.plot([ma, ma], [y_pos[j] - bar_height/2, y_pos[j] + bar_height/2], color='black', linewidth=1, alpha=0.8)
                
                # Central baseline marker (thicker)
                ax.plot([baseline, baseline], [y_pos[j] - bar_height/2, y_pos[j] + bar_height/2], color='black', linewidth=2.5, alpha=1.0)

        if not found_data:
            plt.close()
            continue
            
        ax.set_yticks(y_positions)
        ax.set_yticklabels(factors, fontsize=12, fontweight='bold')
        ax.set_xlabel(metric_info.get(metric, {}).get('label', 'Value'), fontsize=12)
        ax.set_title(f"Tornado Plot: {metric_info.get(metric, {}).get('title', metric)} Sensitivity", fontsize=16, fontweight='bold', pad=20)
        ax.grid(True, axis='x', linestyle='--', alpha=0.4)
        
        # Legend (de-duplicate)
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), title='Operating Mode', loc='upper right')
        
        plt.tight_layout()
        plot_file = os.path.join(output_dir, f'tornado_{metric}.png')
        plt.savefig(plot_file, dpi=300)
        plt.close()
        print(f"Tornado plot saved to {plot_file}")

report_path = os.path.join(output_dir, 'PVT_report.txt')
generate_ascii_report(df, report_path)
print(f"ASCII report saved to {report_path}")

generate_tornado_plots(df, output_dir)

print("Refined analysis complete.")
