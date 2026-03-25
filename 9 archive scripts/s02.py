import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from io import StringIO
import os
import math
from matplotlib.lines import Line2D

# =============================================================================
# ÁREA DE CONFIGURAÇÃO - AJUSTE OS NOMES DOS ARQUIVOS AQUI
# =============================================================================
# Define os nomes raiz para os seus arquivos. 
# O script espera encontrar: {ROOT}{MODE}.vcsv
COMP_ROOT = 'comp_mode'  # Nome raiz para arquivos de compressão
PAE_ROOT  = 'pae_mode'   # Nome raiz para arquivos de PAE
MODES     = ['01', '10', '11'] # Lista de sufixos de modo para processar

# TAMANHOS DE FONTE
TITLE_FONT = 18
LABEL_FONT = 16
TICK_FONT  = 14
LEGEND_FONT = 12

# ESTILO DE ANOTAÇÃO
# Fundo cinza com 50% de opacidade
BBOX_STYLE = dict(boxstyle="round,pad=0.2", facecolor='grey', alpha=0.5, edgecolor='none')
# =============================================================================

def read_vcsv(filename):
    """Lê arquivos VCSV pulando linhas de metadados que começam com ';'."""
    if not os.path.exists(filename):
        print(f"Aviso: Arquivo {filename} não encontrado.")
        return None
    with open(filename, 'r') as f:
        lines = f.readlines()
    data_lines = [l for l in lines if not l.startswith(';')]
    df = pd.read_csv(StringIO("".join(data_lines)), names=['Pin', 'Value'])
    return df

def run_analysis():
    colors = {'01': '#1f77b4', '10': '#ff7f0e', '11': '#2ca02c'} # Azul, Laranja, Verde
    results = {}

    print("Processando modos e calculando métricas...")

    all_pout_min = []
    all_pout_max = []
    all_pin_min = []
    all_pin_max = []
    all_pae_max = []

    for mode in MODES:
        comp_file = f'{COMP_ROOT}{mode}.vcsv'
        pae_file = f'{PAE_ROOT}{mode}.vcsv'
        
        df_comp = read_vcsv(comp_file)
        df_pae = read_vcsv(pae_file)
        
        if df_comp is None or df_pae is None:
            continue
            
        f_pae_interp = interp1d(df_pae['Pin'], df_pae['Value'], bounds_error=False, fill_value="extrapolate")
        
        df = pd.DataFrame({
            'Pin': df_comp['Pin'],
            'Pout': df_comp['Value'],
            'PAE': f_pae_interp(df_comp['Pin'])
        })
        
        all_pout_min.append(df['Pout'].min())
        all_pout_max.append(df['Pout'].max())
        all_pin_min.append(df['Pin'].min())
        all_pin_max.append(df['Pin'].max())
        all_pae_max.append(df['PAE'].max())

        # Cálculo do Ganho Linear
        df['Gain'] = df['Pout'] - df['Pin']
        
        # Usa os 5 primeiros pontos (menor potência de entrada) para calcular a média do ganho linear
        # Isso cria uma métrica mais robusta que um corte fixo em -25dBm
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
        except:
            ip1db, ocp1db, pae_at_p1db = np.nan, np.nan, np.nan
            
        p_sat = df['Pout'].max()
        p_sat_mw = 10**(p_sat/10)
        peak_pae = df['PAE'].max()
        peak_pae_idx = df['PAE'].idxmax()
        pout_at_peak_pae = df.loc[peak_pae_idx, 'Pout']
        pin_at_peak_pae = df.loc[peak_pae_idx, 'Pin']
        
        pout_mw = 10**(df['Pout']/10)
        pin_mw = 10**(df['Pin']/10)
        df['Pdc_mw'] = (pout_mw - pin_mw) / (df['PAE'].replace(0, np.nan) / 100)
        
        peak_pdc = df['Pdc_mw'].max()
        f_pdc = interp1d(df['Pin'], df['Pdc_mw'].fillna(0), bounds_error=False, fill_value="extrapolate")
        pdc_at_p1db = float(f_pdc(ip1db))
        
        results[mode] = {
            'df': df, 'ip1db': ip1db, 'ocp1db': ocp1db, 'pae_at_p1db': pae_at_p1db,
            'p_sat': p_sat, 'p_sat_mw': p_sat_mw, 'peak_pae': peak_pae,
            'peak_pdc': peak_pdc, 'pdc_at_p1db': pdc_at_p1db,
            'pout_at_peak_pae': pout_at_peak_pae, 'pin_at_peak_pae': pin_at_peak_pae,
            'gain_linear': gain_linear # Armazenando o ganho linear
        }

    # Helper para arredondamento de eixos
    def round_down_5(val): return math.floor(val / 5) * 5
    def round_up_5(val): return math.ceil(val / 5) * 5

    x_lim_low = round_down_5(min(all_pin_min)) if all_pin_min else -30
    x_lim_high = round_up_5(max(all_pin_max)) if all_pin_max else 0
    y_pout_low = round_down_5(min(all_pout_min)) if all_pout_min else -30
    y_pout_high = round_up_5(max(all_pout_max)) if all_pout_max else 20
    y_pae_high = round_up_5(max(all_pae_max)) if all_pae_max else 40

    # --- PLOT 1: Pin vs Pout ---
    plt.figure(figsize=(10, 8))
    for mode in MODES:
        if mode not in results: continue
        res = results[mode]
        df = res['df']
        color = colors.get(mode, '#333333')
        plt.plot(df['Pin'], df['Pout'], label=f'Mode {mode}', color=color, linewidth=2.5)
        plt.plot(df['Pin'], df['Pout_ideal'], linestyle='--', color=color, alpha=0.3)
        if not np.isnan(res['ocp1db']):
            plt.scatter(res['ip1db'], res['ocp1db'], color=color, marker='s', s=100, edgecolors='black', zorder=5)
            plt.text(res['ip1db'], res['ocp1db']+0.5, f"{res['ocp1db']:.1f}", 
                     color='white', fontweight='bold', ha='center', fontsize=TICK_FONT-2, bbox=BBOX_STYLE)
            plt.plot([res['ip1db'], res['ip1db']], [y_pout_low, res['ocp1db']], color=color, linestyle='--', alpha=0.5, linewidth=1)
            plt.plot([x_lim_low, res['ip1db']], [res['ocp1db'], res['ocp1db']], color=color, linestyle='--', alpha=0.5, linewidth=1)
    plt.xlabel('Input Power (dBm)', fontsize=LABEL_FONT); plt.ylabel('Output Power (dBm)', fontsize=LABEL_FONT)
    plt.title('Pout vs Pin with OCP1dB Markers', fontsize=TITLE_FONT)
    plt.xticks(fontsize=TICK_FONT); plt.yticks(fontsize=TICK_FONT)
    plt.xlim(x_lim_low, x_lim_high); plt.ylim(y_pout_low, y_pout_high)
    plt.legend(fontsize=LEGEND_FONT); plt.grid(True, which='major', linestyle='-', alpha=0.6)
    plt.minorticks_on(); plt.grid(True, which='minor', linestyle=':', alpha=0.3)
    plt.tight_layout(); plt.savefig('plot1_pout_vs_pin.png', dpi=300)

    # --- PLOT 2: Pin vs PAE ---
    plt.figure(figsize=(10, 8))
    legend_elements = [Line2D([0], [0], marker='o', color='w', label='Peak PAE', markerfacecolor='gray', markersize=10, markeredgecolor='black'),
                       Line2D([0], [0], marker='s', color='w', label='@OCP1dB', markerfacecolor='gray', markersize=10, markeredgecolor='black')]
    for mode in MODES:
        if mode not in results: continue
        res = results[mode]; df = res['df']; color = colors.get(mode, '#333333')
        plt.plot(df['Pin'], df['PAE'], label=f'Mode {mode}', color=color, linewidth=2.5)
        legend_elements.append(Line2D([0], [0], color=color, lw=2.5, label=f'Mode {mode}'))
        plt.scatter(res['pin_at_peak_pae'], res['peak_pae'], color=color, marker='o', s=100, edgecolors='black', zorder=5)
        plt.text(res['pin_at_peak_pae'], res['peak_pae']+0.8, f"{res['peak_pae']:.1f}%", color='white', fontweight='bold', ha='center', fontsize=TICK_FONT-2, bbox=BBOX_STYLE)
        if not np.isnan(res['pae_at_p1db']):
            plt.scatter(res['ip1db'], res['pae_at_p1db'], color=color, marker='s', s=100, edgecolors='black', zorder=5)
            plt.text(res['ip1db'], res['pae_at_p1db']+0.8, f"{res['pae_at_p1db']:.1f}%", color='white', fontweight='bold', ha='center', fontsize=TICK_FONT-2, bbox=BBOX_STYLE)
    plt.xlabel('Input Power (dBm)', fontsize=LABEL_FONT); plt.ylabel('PAE (%)', fontsize=LABEL_FONT)
    plt.title('PAE vs Pin Performance', fontsize=TITLE_FONT)
    plt.xticks(fontsize=TICK_FONT); plt.yticks(fontsize=TICK_FONT)
    plt.xlim(x_lim_low, x_lim_high); plt.ylim(0, y_pae_high)
    plt.legend(handles=legend_elements, fontsize=LEGEND_FONT); plt.grid(True, which='major', linestyle='-', alpha=0.6)
    plt.minorticks_on(); plt.grid(True, which='minor', linestyle=':', alpha=0.3)
    plt.tight_layout(); plt.savefig('plot2_pae_vs_pin.png', dpi=300)

    # --- PLOT 3: PAE vs Pout ---
    plt.figure(figsize=(10, 8))
    for mode in MODES:
        if mode not in results: continue
        res = results[mode]; df = res['df']; color = colors.get(mode, '#333333')
        plt.plot(df['Pout'], df['PAE'], label=f'Mode {mode}', color=color, linewidth=2.5)
        plt.scatter(res['pout_at_peak_pae'], res['peak_pae'], color=color, marker='o', s=80, edgecolors='black', alpha=0.7)
        plt.text(res['pout_at_peak_pae'], res['peak_pae']+0.8, f"{res['peak_pae']:.1f}%", color='white', fontweight='bold', ha='center', fontsize=TICK_FONT-2, bbox=BBOX_STYLE)
        if not np.isnan(res['ocp1db']):
            plt.scatter(res['ocp1db'], res['pae_at_p1db'], color=color, marker='s', s=100, edgecolors='black', zorder=5)
            plt.text(res['ocp1db'], res['pae_at_p1db']+0.8, f"{res['pae_at_p1db']:.1f}%", color='white', fontweight='bold', ha='center', fontsize=TICK_FONT-2, bbox=BBOX_STYLE)
    plt.xlabel('Output Power (dBm)', fontsize=LABEL_FONT); plt.ylabel('PAE (%)', fontsize=LABEL_FONT)
    plt.title('PAE vs Pout Characteristic', fontsize=TITLE_FONT)
    plt.xticks(fontsize=TICK_FONT); plt.yticks(fontsize=TICK_FONT)
    plt.ylim(0, y_pae_high); plt.legend(fontsize=LEGEND_FONT); plt.grid(True, which='major', linestyle='-', alpha=0.6)
    plt.minorticks_on(); plt.grid(True, which='minor', linestyle=':', alpha=0.3)
    plt.tight_layout(); plt.savefig('plot3_pae_vs_pout.png', dpi=300)

    # --- PLOT 4: Dual Axis (Pout & PAE vs Pin) ---
    fig4, ax1 = plt.subplots(figsize=(10, 8)); ax2 = ax1.twinx()
    for mode in MODES:
        if mode not in results: continue
        res = results[mode]; df = res['df']; color = colors.get(mode, '#333333')
        ax1.plot(df['Pin'], df['Pout'], color=color, linewidth=2.5, label=f'Mode {mode} (Pout)')
        ax2.plot(df['Pin'], df['PAE'], color=color, linewidth=2.5, linestyle='--', label=f'Mode {mode} (PAE)')
        if not np.isnan(res['ocp1db']):
            ax1.scatter(res['ip1db'], res['ocp1db'], color=color, marker='s', s=100, edgecolors='black', zorder=5)
            ax1.plot([x_lim_low, res['ip1db']], [res['ocp1db'], res['ocp1db']], color=color, linestyle=':', alpha=0.4, linewidth=1.5)
            ax1.plot([res['ip1db'], x_lim_high], [res['ocp1db'], res['ocp1db']], color=color, linestyle=':', alpha=0.4, linewidth=1.5)
            ax1.plot([res['ip1db'], res['ip1db']], [y_pout_low, res['ocp1db']], color=color, linestyle=':', alpha=0.4, linewidth=1.5)
    ax1.set_xlabel('Input Power (dBm)', fontsize=LABEL_FONT); ax1.set_ylabel('Output Power (dBm)', fontsize=LABEL_FONT); ax2.set_ylabel('PAE (%)', fontsize=LABEL_FONT)
    plt.title('Pout and PAE vs Pin', fontsize=TITLE_FONT)
    ax1.tick_params(axis='both', which='major', labelsize=TICK_FONT); ax2.tick_params(axis='y', which='major', labelsize=TICK_FONT)
    ax1.set_xlim(x_lim_low, x_lim_high); ax1.set_ylim(y_pout_low, y_pout_high); ax2.set_ylim(0, y_pae_high)
    ax1.grid(True, which='major', linestyle='-', alpha=0.6); ax1.minorticks_on(); ax1.grid(True, which='minor', linestyle=':', alpha=0.3)
    legend_handles = [Line2D([0], [0], color=colors[m], lw=2.5, label=f'Mode {m}') for m in MODES if m in results]
    legend_handles.append(Line2D([0], [0], marker='s', color='w', label='Square = OCP1dB', markerfacecolor='gray', markersize=10, markeredgecolor='black'))
    ax1.legend(handles=legend_handles, fontsize=LEGEND_FONT, title="Solid: Pout, Dashed: PAE")
    plt.tight_layout(); plt.savefig('plot4_dual_axis.png', dpi=300)

    # --- PLOT 5: Tracking Linear Region (Envelope) ---
    fig5, ax5_1 = plt.subplots(figsize=(10, 8)); ax5_2 = ax5_1.twinx()
    
    # Construção das Curvas de Rastreamento (Envelope)
    all_pins = sorted(list(set(np.concatenate([results[m]['df']['Pin'].values for m in MODES if m in results]))))
    tracking_pout = []; tracking_pae = []
    
    # Definindo pontos de transição baseados em IP1dB
    switch_01_10 = results['01']['ip1db']
    switch_10_11 = results['10']['ip1db']

    for p in all_pins:
        if p <= switch_01_10: mode_to_use = '01'
        elif p <= switch_10_11: mode_to_use = '10'
        else: mode_to_use = '11'
        
        f_p = interp1d(results[mode_to_use]['df']['Pin'], results[mode_to_use]['df']['Pout'], fill_value="extrapolate")
        f_e = interp1d(results[mode_to_use]['df']['Pin'], results[mode_to_use]['df']['PAE'], fill_value="extrapolate")
        tracking_pout.append(f_p(p))
        tracking_pae.append(f_e(p))

    # Desenha curvas originais ao fundo (transparentes)
    for mode in MODES:
        if mode not in results: continue
        res = results[mode]; df = res['df']; color = colors.get(mode, '#333333')
        ax5_1.plot(df['Pin'], df['Pout'], color=color, linewidth=2.0, alpha=0.5)
        ax5_2.plot(df['Pin'], df['PAE'], color=color, linewidth=2.0, linestyle='--', alpha=0.5)
    
    # Plot da Envoltória de Rastreamento (Vermelho Claro PONTILHADA)
    envelope_color = "#fa1515"
    # Pout Envoltória
    ax5_1.plot(all_pins, tracking_pout, color=envelope_color, linestyle=':', linewidth=3, label='Tracking Envelope (Pout)')
    # PAE Envoltória
    ax5_2.plot(all_pins, tracking_pae, color=envelope_color, linestyle=':', linewidth=3, label='Tracking Envelope (PAE)')

    # Adicionando Linhas Verticais Pretas e Pontilhadas nos pontos de transição
    transition_points = [switch_01_10, switch_10_11]
    for tp in transition_points:
        if not np.isnan(tp):
            ax5_1.axvline(x=tp, color='black', linestyle='-', linewidth=1.2, alpha=0.6, zorder=1)

    ax5_1.set_xlabel('Input Power (dBm)', fontsize=LABEL_FONT); ax5_1.set_ylabel('Output Power (dBm)', fontsize=LABEL_FONT); ax5_2.set_ylabel('PAE (%)', fontsize=LABEL_FONT)
    plt.title('Plot 5: Mode Tracking Envelope (Linear Region)', fontsize=TITLE_FONT)
    ax5_1.tick_params(axis='both', which='major', labelsize=TICK_FONT); ax5_2.tick_params(axis='y', which='major', labelsize=TICK_FONT)
    ax5_1.set_xlim(x_lim_low, x_lim_high); ax5_1.set_ylim(y_pout_low, y_pout_high); ax5_2.set_ylim(0, y_pae_high)
    ax5_1.grid(True, which='major', linestyle='-', alpha=0.6); ax5_1.minorticks_on(); ax5_1.grid(True, which='minor', linestyle=':', alpha=0.3)
    
    # Legenda customizada para o Plot 5
    env_handle = Line2D([0], [0], color=envelope_color, lw=3, ls=':', label='Envoltória Pontilhada')
    trans_handle = Line2D([0], [0], color='black', lw=1.2, ls=':', alpha=0.6, label='Troca de Modo')
    mode_handles = [Line2D([0], [0], color=colors[m], lw=2, alpha=0.3, label=f'Modo {m}') for m in MODES if m in results]
    ax5_1.legend(handles=[env_handle, trans_handle] + mode_handles, fontsize=LEGEND_FONT, loc='upper left')
    
    plt.tight_layout(); plt.savefig('plot5_tracking.png', dpi=300)

    # --- GERAÇÃO DE RELATÓRIO ---
    # Adicionada a coluna 'gain_lin(dB)'
    report_header = "mode | gain_lin(dB) | ocp1dbm | p_sat(dbm) | p_sat(mw) | peak PAE | PAE @ ocp1db | peak pdc (mw) | pdc @ ocp1db (mw)"
    report_lines = [report_header, "-" * len(report_header)]
    for mode in MODES:
        if mode not in results: continue
        r = results[mode]
        # Adicionado r['gain_linear'] na formatação
        line = (f"{mode:4} | {r['gain_linear']:12.2f} | {r['ocp1db']:7.2f} | {r['p_sat']:10.2f} | {r['p_sat_mw']:9.2f} | "
                f"{r['peak_pae']:8.2f} | {r['pae_at_p1db']:12.2f} | "
                f"{r['peak_pdc']:13.2f} | {r['pdc_at_p1db']:17.2f}")
        report_lines.append(line)
    with open('report.txt', 'w') as f: f.write("\n".join(report_lines))
    print("\n--- Summary Report ---\n" + "\n".join(report_lines) + "\n\nArquivos salvos com sucesso.")

if __name__ == "__main__":
    run_analysis()