import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import os

# ==============================================================================
# ======================== USER CONFIGURATION SECTION ==========================
# ==============================================================================

# 1. DIRECTORY SETTINGS
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
INPUT_DIR = os.path.join(SCRIPT_DIR, '..', '1 raw results', '2 large signals operation point')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, '..', '3 outputs', '2 large signals operation point')

# 2. MODES & STYLING COLORS
MODES = ['01', '10', '11']
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

# 4. TOGGLE FLAGS FOR PLOTS
SHOW_LINEAR_REGION = True
SHOW_OCP1DBM = True
SHOW_PAE_PEAK = True

# ==============================================================================
# ====================== END OF CONFIGURATION SECTION ==========================
# ==============================================================================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def read_vcsv(filename):
    """Reads VCSV files avoiding lines starting with ';'"""
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return None
        
    with open(filename, 'r') as f:
        lines = f.readlines()
        
    data_lines = [l for l in lines if not l.startswith(';')]
    from io import StringIO
    df = pd.read_csv(StringIO("".join(data_lines)), names=['Pin', 'Value'])
    return df

def main():
    ensure_dir(OUTPUT_DIR)
    
    results = {}
    
    print("Processing modes and calculating metrics...")
    
    for mode in MODES:
        comp_file = os.path.join(INPUT_DIR, f'comp_mode{mode}.vcsv')
        pae_file = os.path.join(INPUT_DIR, f'PAE_mode{mode}.vcsv')
        power_file = os.path.join(INPUT_DIR, f'power_mode{mode}.vcsv')
        
        df_comp = read_vcsv(comp_file)
        df_pae = read_vcsv(pae_file)
        df_power = read_vcsv(power_file)
        
        if df_comp is None or df_pae is None or df_power is None:
            print(f"Skipping Mode {mode} due to missing files.")
            continue
            
        # Interpolate PAE and Power to Pin from comp
        f_pae_interp = interp1d(df_pae['Pin'], df_pae['Value'], bounds_error=False, fill_value="extrapolate")
        f_power_interp = interp1d(df_power['Pin'], df_power['Value'], bounds_error=False, fill_value="extrapolate")
        
        df = pd.DataFrame({
            'Pin': df_comp['Pin'],
            'Pout': df_comp['Value'],
            'PAE': f_pae_interp(df_comp['Pin']),
            'Pdc_W': f_power_interp(df_comp['Pin'])
        })
        
        df['Pdc_mW'] = df['Pdc_W'] * 1000.0
        
        # Linear Gain Calculation (at lower power, e.g., using first 5 points or near -20dBm)
        df['Gain'] = df['Pout'] - df['Pin']
        
        # Mean of first 5 points like s02.py
        gain_linear = df.sort_values('Pin')['Gain'].iloc[:5].mean()
        
        df['Pout_ideal'] = df['Pin'] + gain_linear
        df['Compression'] = df['Pout_ideal'] - df['Pout']
        
        try:
            f_find_ip1db = interp1d(df['Compression'], df['Pin'], bounds_error=False, fill_value="extrapolate")
            ip1db = float(f_find_ip1db(1.0))
            f_pout = interp1d(df['Pin'], df['Pout'], bounds_error=False, fill_value="extrapolate")
            ocp1db = float(f_pout(ip1db))
            f_pae = interp1d(df['Pin'], df['PAE'], bounds_error=False, fill_value="extrapolate")
            pae_at_p1db = float(f_pae(ip1db))
            
            f_pdc = interp1d(df['Pin'], df['Pdc_mW'], bounds_error=False, fill_value="extrapolate")
            pdc_at_p1db = float(f_pdc(ip1db))
        except:
            ip1db, ocp1db, pae_at_p1db, pdc_at_p1db = np.nan, np.nan, np.nan, np.nan
            
        p_sat = df['Pout'].max()
        p_sat_mw = 10**(p_sat/10)
        
        peak_pae = df['PAE'].max()
        peak_pae_idx = df['PAE'].idxmax()
        pout_at_peak_pae = df.loc[peak_pae_idx, 'Pout']
        pin_at_peak_pae = df.loc[peak_pae_idx, 'Pin']
        
        peak_pdc = df['Pdc_mW'].max()
        
        results[mode] = {
            'df': df,
            'ip1db': ip1db, 
            'ocp1db': ocp1db, 
            'pae_at_p1db': pae_at_p1db,
            'p_sat': p_sat, 
            'p_sat_mw': p_sat_mw, 
            'peak_pae': peak_pae,
            'peak_pdc': peak_pdc, 
            'pdc_at_p1db': pdc_at_p1db,
            'pout_at_peak_pae': pout_at_peak_pae, 
            'pin_at_peak_pae': pin_at_peak_pae,
            'gain_linear': gain_linear
        }

    # BBox style for annotations
    bbox_style = dict(boxstyle="round,pad=0.2", facecolor='grey', alpha=0.5, edgecolor='none')
    
    # helper functions
    import math
    def round_down_5(val): return math.floor(val / 5) * 5
    def round_up_5(val): return math.ceil(val / 5) * 5
    
    # Axis limits
    all_pin_min = min([results[m]['df']['Pin'].min() for m in results])
    all_pin_max = max([results[m]['df']['Pin'].max() for m in results])
    all_pout_min = min([results[m]['df']['Pout'].min() for m in results])
    all_pout_max = max([results[m]['df']['Pout'].max() for m in results])
    all_pae_max = max([results[m]['df']['PAE'].max() for m in results])
    
    x_lim_low = round_down_5(all_pin_min)
    x_lim_high = round_up_5(all_pin_max)
    y_pout_low = round_down_5(all_pout_min)
    y_pout_high = round_up_5(all_pout_max)
    y_pae_high = round_up_5(all_pae_max) + 5
    
    # --- PLOT 1: Pout vs Pin ---
    plt.figure(figsize=FIGSIZE)
    for mode in MODES:
        if mode not in results: continue
        res = results[mode]
        df = res['df']
        color = COLORS.get(mode, 'black')
        
        plt.plot(df['Pin'], df['Pout'], label=f'Mode {mode}', color=color, linewidth=2.5)
        
        if SHOW_LINEAR_REGION:
            plt.plot(df['Pin'], df['Pout_ideal'], linestyle=':', color='lightgray', alpha=0.8, linewidth=2)
        if SHOW_OCP1DBM and not np.isnan(res['ocp1db']):
            plt.scatter(res['ip1db'], res['ocp1db'], color=color, marker='s', s=100, edgecolors='black', zorder=5)
            plt.text(res['ip1db'], res['ocp1db']+0.5, f"{res['ocp1db']:.1f}", 
                     color='white', fontweight='bold', ha='center', fontsize=10, bbox=bbox_style)
                         
    plt.xlabel('Input Power (dBm)', fontsize=FONT_SIZE_AXIS)
    plt.ylabel('Output Power (dBm)', fontsize=FONT_SIZE_AXIS)
    plt.title('Pout vs Pin', fontsize=FONT_SIZE_TITLE)
    plt.xlim(x_lim_low, x_lim_high)
    plt.ylim(y_pout_low, y_pout_high)
    plt.grid(True, which='both', linestyle='--', alpha=0.6)
    
    # Construct legend
    from matplotlib.lines import Line2D
    handles, labels = plt.gca().get_legend_handles_labels()
    # Filter repeated tracking line
    unique = [(h, l) for i, (h, l) in enumerate(zip(handles, labels)) if l not in labels[:i]]
    if SHOW_LINEAR_REGION:
        unique.append((Line2D([0],[0], color='lightgray', linestyle=':', lw=2), 'Linear Region'))
    if SHOW_OCP1DBM:
        unique.append((Line2D([0],[0], marker='s', color='w', markerfacecolor='gray', markeredgecolor='black', markersize=10), 'OCP1dB'))
        
    plt.legend([h for h, l in unique], [l for h, l in unique], fontsize=FONT_SIZE_LEGEND, loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'Pout_vs_Pin.png'), dpi=300)
    
    # --- PLOT 2: PAE vs Pout ---
    plt.figure(figsize=FIGSIZE)
    for mode in MODES:
        if mode not in results: continue
        res = results[mode]
        df = res['df']
        color = COLORS.get(mode, 'black')
        
        plt.plot(df['Pout'], df['PAE'], label=f'Mode {mode}', color=color, linewidth=2.5)
        
        if SHOW_PAE_PEAK and not np.isnan(res['peak_pae']):
            plt.scatter(res['pout_at_peak_pae'], res['peak_pae'], color=color, marker='o', s=100, edgecolors='black', zorder=5)
            plt.text(res['pout_at_peak_pae'], res['peak_pae']+1.0, f"{res['peak_pae']:.1f}%", 
                     color='white', fontweight='bold', ha='center', fontsize=10, bbox=bbox_style)
                     
    plt.xlabel('Output Power (dBm)', fontsize=FONT_SIZE_AXIS)
    plt.ylabel('PAE (%)', fontsize=FONT_SIZE_AXIS)
    plt.title('PAE vs Pout', fontsize=FONT_SIZE_TITLE)
    plt.ylim(0, y_pae_high)
    plt.grid(True, which='both', linestyle='--', alpha=0.6)
    
    handles, labels = plt.gca().get_legend_handles_labels()
    if SHOW_PAE_PEAK:
        handles.append(Line2D([0],[0], marker='o', color='w', markerfacecolor='gray', markeredgecolor='black', markersize=10))
        labels.append('Peak PAE')
    plt.legend(handles, labels, fontsize=FONT_SIZE_LEGEND, loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'PAE_vs_Pout.png'), dpi=300)
    
    # --- PLOT 3: Pout and PAE vs Pin (Dual Axis) ---
    fig, ax1 = plt.subplots(figsize=FIGSIZE)
    ax2 = ax1.twinx()
    
    for mode in MODES:
        if mode not in results: continue
        res = results[mode]
        df = res['df']
        color = COLORS.get(mode, 'black')
        
        ax1.plot(df['Pin'], df['Pout'], color=color, linewidth=2.5, label=f'Mode {mode} (Pout)')
        ax2.plot(df['Pin'], df['PAE'], color=color, linewidth=2.5, linestyle='--', alpha=0.8, label=f'Mode {mode} (PAE)')
        
    ax1.set_xlabel('Input Power (dBm)', fontsize=FONT_SIZE_AXIS)
    ax1.set_ylabel('Output Power (dBm)', fontsize=FONT_SIZE_AXIS)
    ax2.set_ylabel('PAE (%)', fontsize=FONT_SIZE_AXIS)
    plt.title('Pout and PAE vs Pin', fontsize=FONT_SIZE_TITLE)
    
    ax1.set_xlim(x_lim_low, x_lim_high)
    ax1.set_ylim(y_pout_low, y_pout_high)
    ax2.set_ylim(0, y_pae_high)
    
    ax1.grid(True, which='both', linestyle='--', alpha=0.6)
    
    # Legend combining both axes
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    custom_lines = []
    custom_labels = []
    for mode in MODES:
        if mode in results:
            custom_lines.append(Line2D([0], [0], color=COLORS[mode], lw=2.5))
            custom_labels.append(f'Mode {mode}')
    custom_lines.append(Line2D([0], [0], color='gray', lw=2.5))
    custom_labels.append('Solid: Pout')
    custom_lines.append(Line2D([0], [0], color='gray', lw=2.5, linestyle='--'))
    custom_labels.append('Dashed: PAE')
            
    ax1.legend(custom_lines, custom_labels, fontsize=FONT_SIZE_LEGEND, loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'DualAxis_Pout_PAE_vs_Pin.png'), dpi=300)
    
    # --- TXT REPORT GENERATION ---
    report_lines = []
    report_lines.append("=" * 140)
    report_lines.append(f"{'Mode':<6} | {'Gain Lin(dB)':<14} | {'OCP1dBm(dBm)':<14} | {'Psat(dBm)':<10} | {'Psat(mW)':<10} | {'Peak PAE(%)':<12} | {'PAE@OCP1dB(%)':<14} | {'Peak PDC(mW)':<14} | {'Pdc@OCP1dbm(mW)':<14}")
    report_lines.append("-" * 140)
    
    for mode in MODES:
        if mode not in results: continue
        r = results[mode]
        # format line
        line = (f"{mode:<6} | {r['gain_linear']:<14.2f} | {r['ocp1db']:<14.2f} | {r['p_sat']:<10.2f} | {r['p_sat_mw']:<10.2f} | "
                f"{r['peak_pae']:<12.2f} | {r['pae_at_p1db']:<14.2f} | {r['peak_pdc']:<14.2f} | {r['pdc_at_p1db']:<14.2f}")
        report_lines.append(line)
        
    report_lines.append("=" * 140)
    
    report_path = os.path.join(OUTPUT_DIR, 'Large_Signals_Report.txt')
    with open(report_path, 'w') as f:
        f.write("\n".join(report_lines) + "\n")
        
    print(f"Report saved to {report_path}")
    
    # Show plots if executed directly
    plt.show()

if __name__ == "__main__":
    main()
