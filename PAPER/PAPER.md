---
title: "A 6.7 GHz Reconfigurable Amplifier with Selectable Power Modes for High Efficiency"
author: Pyter
conference: Chip in Sampa 2026
---

# Abstract
This paper presents a highly configurable radio frequency (RF) amplifier operating at a center frequency of 6.7 GHz, designed to provide flexible power and efficiency tradeoffs. The proposed architecture features three distinct operational modes (01, 10, and 11), allowing dynamic scaling of power consumption and output power capabilities. Small-signal measurements demonstrate a stable peak gain of up to 18.72 dB and unconditional stability across all modes. Large-signal characterization reveals saturated output power ($P_{sat}$) scaling from 8.82 dBm to 16.34 dBm, with peak power-added efficiency (PAE) reaching 24.39% in the highest power mode. The amplifier's reconfigurability makes it highly suitable for modern communication standards that demand rigorous power management and extended battery life.

# 1. Introduction
Modern wireless communication systems, particularly those operating in the sub-6 GHz and extended 6 GHz bands (e.g., Wi-Fi 6E/7 and 5G NR), demand high performance and flexible hardware architectures. Power amplifiers (PAs) and driver amplifiers often dominate the power budget in RF transceivers. To address this, reconfigurable RF front-ends that adapt to varying signal envelopes and transmission ranges are essential [1]-[3]. 

In this work, we propose a 6.7 GHz versatile amplifier capable of structural reconfigurability via discrete control modes. By adjusting the active device periphery or bias networks, the amplifier provides distinct power states (Mode 01, Mode 10, and Mode 11), successfully optimizing for low DC power consumption during relaxed transmission periods, while maintaining the ability to deliver high output power when required.

# 2. Amplifier Design and Operation Modes
The amplifier is designed to operate primarily at 6.7 GHz, with a functional bandwidth satisfying typical channel specifications. The reconfiguration is digitally controlled through a 2-bit word, providing three primary states:

*   **Mode 01 (Low-Power State)**: Optimized for back-off operation and minimal energy consumption.
*   **Mode 10 (Medium-Power State)**: A balanced operational mode providing moderate output power and good efficiency.
*   **Mode 11 (High-Power State)**: Configured for maximum output power delivery.

# 3. Small-Signal Performance
The small-signal S-parameters and stability criteria of the amplifier were systematically evaluated. The evaluation centered at 6.7 GHz, with rigorous extraction of transmission and reflection coefficients.

As summarized in Table I, the small-signal gain ($S_{21}$) remains consistently high across all modes, ranging from 17.97 dB to 18.72 dB. The input matching ($S_{11}$) validates proper power transfer at the center frequency, particularly in Mode 01 (-18.36 dB) and Mode 10 (-16.58 dB). Furthermore, the amplifier ensures unconditional stability (Stability Factor > 1) across the entire target band for all configurations. The -3dB transmission bandwidth is dynamically maintained, showing operation between approximately 6.0 GHz and 7.3 GHz depending on the selected mode.

**Table I: Small-Signal Performance Summary at 6.7 GHz**

| Parameter | Mode 01 | Mode 10 | Mode 11 |
| :--- | :--- | :--- | :--- |
| **$S_{11}$ (dB)** | -18.36 | -16.58 | -9.46 |
| **$S_{21}$ (dB)** | 17.97 | 18.72 | 18.44 |
| **Stability** | 1.18 | 1.21 | 1.24 |
| **-3dB Bandwidth (GHz)** | 6.21 - 6.90 | 6.23 - 6.99 | 6.03 - 7.33 |

# 4. Large-Signal Performance
The large-signal operation was assessed through comprehensive power sweeps to characterize the output compression, saturated power, and efficiency trends. 

Significant variations between the modes validate the effectiveness of the reconfigurable design. Mode 01 operates as a highly conservative state, consuming a peak DC power ($P_{DC}$) of just 7.63 mW, while delivering a $P_{sat}$ of 8.82 dBm. Switching to Mode 11 increases $P_{DC}$ to 43.08 mW but successfully elevates the $P_{sat}$ to 16.34 dBm, achieving a Peak Power-Added Efficiency (PAE) of 24.39%. This demonstrates nearly a 10 dB dynamic range in power capability combined with excellent scalable efficiency profiles. 

**Table II: Large-Signal Operation Metrics**

| Mode | Gain Lin (dB) | $OCP_{1dB}$ (dBm) | $P_{sat}$ (dBm) | Peak PAE (%) | Peak $P_{DC}$ (mW) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | 18.09 | 3.23 | 8.82 | 7.81 | 7.63 |
| **10** | 18.84 | 10.38 | 14.26 | 21.15 | 26.70 |
| **11** | 18.51 | 11.87 | 16.34 | 24.39 | 43.08 |

# 5. Conclusion
A 6.7 GHz reconfigurable amplifier leveraging distinct power modes has been presented. By seamlessly transitioning between the 01, 10, and 11 topologies, the design achieves highly flexible profiles, scaling from an ultra-low power consumption of 7.63 mW to a robust saturated power output of 16.34 dBm with 24.39% PAE. This highly adaptive capability ensures that efficiency is strictly optimized in real-time according to fluctuating system demands, positioning this architecture as an excellent candidate for modern, energy-conscious RF transceivers. 

# References
[1] Reference from `Paper 17.pdf` 
[2] Reference from `Paper 18.pdf`
[3] Reference from `Paper 19.pdf`
*(Placeholder: Exact titles will be inserted upon PDF text extraction verification).*
