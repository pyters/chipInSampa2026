# Project: Chip in Sampa 2026

## 1. Small Signals Analysis (`2 scripts/1_small_signals.py`)

This script is responsible for processing raw S-parameter and stability criteria data extracted for three different operational modes (`01`, `10`, and `11`).

**Input Files**:

Requires `.vcsv` files (Comma Separated Values containing S-parameters and stability criteria data exported from Virtuoso/Spectre). The script expects one file per operational mode (`01`, `10`, `11`). It automatically parses S-parameter data and stability measures, converting internal frequency scales from `Hz` to `GHz` and masking out invalid `NaN` values.

- Directory: `1 raw results/1 s parameters/`

**Output Files**:

- `.png`: High-resolution figures/plots (2x2 grid, standalone variables, stability curve).
- `.csv`: Comma-separated summary tabular data of S-parameters, stability, and `-3dB` bounds at the Center Frequency.
- `.txt`: Formatted ASCII report featuring the summary table over various frequencies of interest (2 to 10 GHz).
- Directory: `3 outputs/1 s parameters/`

### Small Signals Features & Capabilities

- **Highly Configurable**: The script header includes variables to control the center frequency of analysis (default `6.7 GHz`), target frequency band margins (default `+/- 0.5 GHz`), list of frequencies for data interpolation, figure dimensions, and granular font size settings.
- **S-Parameters Grid & Standalone Plots**: Evaluates the transmission and reflection coefficients (`S11`, `S12`, `S21`, and `S22`). It generates an aggregated 2x2 grid showing the data for all modes, highlighting the target band in a shaded area. It also outputs high-quality standalone figures for each specific S-parameter.
- **Stability Criteria**: Produces an independent plot comparing the stability measure of the three modes against the target band and a strict reference limit line at `1.0`.
- **-3dB Bandwidth Calculation**: Automatically detects the maximum S21 peak and calculates the exact upper and lower bounds where the S21 magnitude drops by ~`3dB` to quantify the operational bandwidth for each mode.
- **Comprehensive Reporting**:
  - Outputs a concise `CSV` data table comparing the S-parameters, stability values, and `-3dB` bounds of all modes securely extracted at the defined center frequency.
  - Generates an in-depth ASCII formatted Text Report (`.txt`) featuring the high-level summary table at the top, followed by detailed mode-by-mode parameter interpolations at broader frequencies of interest (e.g., 2 to 10 GHz).
- **Centralized Outputs**: All generated assets (plots, grids, tables, and reports) are automatically routed to the `3 outputs/1 s parameters/` directory.

---

## 2. Large Signals Operation Point

This script (`2 scripts/2_large_signals_OP.py`) evaluates the power efficiency, output behavior, and linearity criteria within large signal operations. It cross-references data from performance, power-added efficiency (PAE), and DC power consumption curves simultaneously to extract critical operation metrics automatically.

**Input Files**:

Requires `.vcsv` files (exported from Virtuoso/Spectre). The script expects three files per operational mode (`01`, `10`, `11`):

- `comp_modeXX.vcsv`: Input Power (Pin) vs Output Power (Pout).
- `PAE_modeXX.vcsv`: Input Power (Pin) vs Power-Added Efficiency (PAE).
- `power_modeXX.vcsv`: Input Power (Pin) vs DC Power Consumption (in Watts).

- Directory: `1 raw results/2 large signals operation point/`

**Output Files**:

- `.png`: High-resolution figures/plots (`Pout_vs_Pin.png`, `PAE_vs_Pout.png`, `DualAxis_Pout_PAE_vs_Pin.png`).
- `.txt`: Formatted ASCII report (`Large_Signals_Report.txt`) containing the extracted metrics for each mode.

- Directory: `3 outputs/2 large signals operation point/`

### Metric Calculations

The output tabular report evaluates eight distinct parameters to summarize amplifier behavior. The calculations are resolved securely by analytical extrapolations over the provided data points:

- **Gain Lin(dB)**: The average small-signal (linear) gain derived from `Pout - Pin` computed over the first 5 low-power data points.
- **OCP1dBm(dBm)**: Output Power at 1dB Compression Point. The script computes an ideal linear response curve (`Pout_ideal = Pin + Gain_Lin`) and extracts the precise Input Power (`IP1dB`) where the compression difference (`Pout_ideal - Pout`) strictly equals `1.0 dB`. `OCP1dB` evaluates `Pout` exactly at this `IP1dB` coordinate.
- **Psat(dBm)**: Saturated Output Power. The absolute maximum output power extracted identically directly from the data.
- **Psat(mW)**: Saturated Output Power translated algebraically to milliwatts (`10^(Psat/10)`).
- **Peak PAE(%)**: The absolute maximum Power-Added Efficiency (PAE) achieved linearly through the dataset.
- **PAE@OCP1dB(%)**: Power-Added Efficiency evaluated explicitly at the 1dB compression coordinate (`IP1dB`).
- **Peak PDC(mW)**: The highest detected DC Power Consumption recorded strictly via the `power_modeXX` file. The extracted data originally given in Watts is mathematically rescaled to milliwatts (`W * 1000`).
- **Pdc@OCP1dbm(mW)**: The matching DC Power Consumption evaluated securely at the 1dB compression coordinate (`IP1dB`), also returned in milliwatts.

---

## 3. Large Signals Frequency Sweep (`2 scripts/3_large_signals_SF.py`)

This script evaluates how key large-signal performance metrics evolve across a broad frequency range. It parses a single consolidated frequency sweep dataset and generates comparative visualizations for the three operational modes (`01`, `10`, and `11`).

**Input Files**:

Requires a consolidated `.csv` file containing the frequency sweep results for all modes:

- `data freq sweep all modes.csv`: Contains tabular data for multiple frequencies, categorized by mode and metric.

- Directory: `1 raw results/3 large signals freq sweep/`

**Output Files**:

- `.png`: High-resolution figures showing metrics vs. Frequency.
  - `All_Metrics_2x2.png`: A consolidated grid overlapping all modes for all metrics.
  - Individual metric plots: `hb_ocp1dbm_value.png`, `hb_peakPAE_value.png`, `hb_gainAt_20dbm_value.png`, and `hb_PAEAtOcp1dbm.png`.

- Directory: `3 outputs/3 large signal freq sweep/`

### Frequency Sweep Features & Capabilities

- **Multi-Mode Overlap**: Automatically filters and maps data for modes `01`, `10`, and `11`, plotting them on the same axes to visualize performance trade-offs across the frequency band.
- **Metric Tracking**: Monitors four critical performance indicators:
  - **OCP1dBm (dBm)**: Output power at 1dB compression.
  - **Peak PAE (%)**: Maximum Power-Added Efficiency.
  - **Linear Gain (dB)**: Small-signal gain measured at a low input power (e.g., -20 dBm).
  - **PAE @ OCP1dB (%)**: Efficiency at the maximum linearity point.
- **Visual References**: Includes a customizable vertical reference line at the design center frequency (default `6.7 GHz`) and uses 4px circle markers to highlight discrete data points.
- **2x2 Grid Visualization**: Provides a "one-glance" overview of the entire large-signal frequency response of the chip, maintaining styling consistency (colors, fonts, and dimensions) with other project scripts.
- **Customized Plotting**: Includes high-quality standalone plots for each of the four indicators mentioned above.

---

## 4. PVT Simulation Analysis (`2 scripts/4_large_signals_PVT.py`)

This script performs a comprehensive analysis of circuit performance across process, voltage, and temperature variations (PVT). It processes a wide-format corner simulation dataset and generates both high-quality variability charts and multi-mode sensitivity plots.

**Input Files**:

- `PVT.csv`: Wide-format corner simulation results (FF, FS, SF, SS, Nominal) across multiple voltages (2.25V, 2.5V, 2.75V) and temperatures (-40, 27, 125ºC).
- Directory: `1 raw results/4 large signals PVT/`

**Output Files**:

- `variability_*.png`: JMP-style variability charts with nested X-axis labels (Temp -> Voltage -> Process).
- `tornado_*.png`: Grouped sensitivity analysis charts (Tornado Plots) comparing P/V/T impact across all modes.
- `PVT_consolidated.csv`: Tidy-format data table including all corner data and a new "Delta Gain" metric.
- `PVT_report.txt`: Professional ASCII formatted summary report with detailed process and extreme variations.
- Directory: `3 outputs/4 large signals PVT/`

### PVT Analysis Features & Capabilities

- **Variability Charts**: Features a manual, JMP-style nested X-axis grouping temperature, voltage, and process levels linearly. Includes light grey background boxes to visualize mode spread at each corner, dashed vertical dividers for readability, and thick mode-colored connecting lines to highlight performance trends across corners.
- **Tornado Sensitivity Plots**: Provides a high-impact visualization of technical robustness. It groups three horizontal bars per factor (Process, Voltage, Temperature), each bar representing one operational mode. It features a thick central line for the baseline (Nominal Process, 2.5V, 27ºC) and explicit terminal markers at performance limits.
- **Delta Gain Metric**: Introduces a new calculated metric, `max(gain) - min(gain)`, representing the absolute gain spread between operational modes for every single PVT corner. This is plotted identically to other metrics for comparative analysis.
- **Advanced ASCII Reporting**:
  - `Section 1`: Captures process variations (SS, FS, SF, FF) specifically under nominal conditions (27ºC, 2.5V) for modes `01`, `10`, and `11`.
  - `Section 2`: Identifies the absolute minimum, maximum, and total range for each metric across all 16 PVT corners, providing separate columns for the specific condition (**T**, **V**, and **P**) where each extreme was detected.

---

## 5. Monte Carlo Analysis (`2 scripts/5_large_signals_MC.py`)

This script performs a statistical evaluation of the Power Amplifier performance across 500 Monte Carlo iterations for three operational modes (`01`, `10`, and `11`). It generates probability density distributions and calculates detailed statistical metrics.

**Input Files**:

Requires `.csv` files containing Monte Carlo simulation results (exported from Virtuoso/Spectre). The script expects one file per operational mode.

- Directory: `1 raw results/5 large signals MC/`

**Output Files**:

- `.png`: High-resolution histograms and PDF (KDE) curves.
  - `Monte_Carlo_Metrics_Histogram.png`: A consolidated 2x2 grid for all metrics.
  - Individual metric plots: `Monte_Carlo_Linear_Gain_dB.png`, `Monte_Carlo_OCP1dBm_dBm.png`, `Monte_Carlo_Peak_PAE_pct.png`, and `Monte_Carlo_PAE_at_OCP1dBm_pct.png`.
- `.txt`: Formatted ASCII report (`Monte_Carlo_Statistics_Report.txt`) containing the statistical summary (Min, Max, Avg, Median, Std Dev) for each mode and metric.

- Directory: `3 outputs/5 large signals MC/`

### Monte Carlo Features & Capabilities

- **Statistical Distribution Analysis**: Uses Gaussian Kernel Density Estimation (KDE) to overlay smooth probability density curves on top of histograms, providing a clearer view of the performance distribution.
- **Multi-Metric Evaluation**: Tracks four critical indicators:
  - **Linear Gain (dB)**
  - **OCP1dBm (dBm)**
  - **Peak PAE (%)**
  - **PAE @ OCP1dBm (%)**
- **Comparative Mode Analysis**: Overlaps distributions for all three modes using consistent color coding, allowing direct visual comparison of statistical stability and performance trade-offs.
- **Comprehensive Reporting**: Generates a detailed statistical summary table, highlighting the robustness of the design against manufacturing process variations and mismatch.
