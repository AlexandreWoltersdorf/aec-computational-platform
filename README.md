# AEC Computational Platform

**A personal R&D repository exploring the intersection of BIM data, Computational Geometry, and Engineering Physics.**

The goal of this project is to bridge the gap between standard design tools (Rhino, Speckle) and advanced engineering analysis (Python). Instead of treating walls as simple 3D geometry, this platform converts them into intelligent `WallBuildUp` objects to simulate their physical performance and generate fabrication data.

---

## 🔄 The Workflow

The architecture is strictly divided into 3 functional blocks:

### 1. Connectors (Input)
Bridges to external software. I don't model manually here; I pull data from **Speckle**, **Rhino**, or **IFC**.
*   **Role:** Normalize raw geometry into the Core format.

### 2. Core (Pivot)

The heart of the system. Once ingested, raw geometry acts as a seed to generate a semantic `WallBuildUp` object. 

This module acts as the **Single Source of Truth**, decoupling the input source (Rhino/Revit) from the analysis solvers. It enforces a strict physical architecture based on construction logic rather than just geometric layers:

*   **External Layers:** Weather protection & thermal envelope (defined relative to the structure's outer face).
*   **Structural Core:** The load-bearing reference (Lattice, CLT, or Concrete).
*   **Internal Layers:** Service cavities & finishes (defined relative to the structure's inner face).

<!-- GALERIE D'IMAGES - Remplace les liens src par tes noms de fichiers -->
<table border="0">
  <tr>
    <td width="50%" align="center">
      <img src="docs/buildup_3d_view.png" alt="3D View" width="100%">
      <br>
      <em>3D</em>
    </td>
    <td width="25%" align="center">
      <img src="docs/buildup_vertical_view.png" alt="Vertical" width="100%">
      <br>
      <em>Side view</em>
    </td>
    <td width="25%" align="center">
      <img src="docs/buildup_horizontal_view.png" alt="Horizontal" width="100%">
      <br>
      <em>Top view</em>
    </td>
  </tr>
</table>

## 3. Solvers (Output)

The platform features a dedicated Physics Engine that consumes the `Core` object to simulate multi-physical performance.
Results are benchmarked against standard construction methods (Concrete, CLT) to validate the system's viability.

### 🔊 Acoustics Solver
*   **Objective:** Predict the weighted Sound Reduction Index ($R_w$) for complex double-shell assemblies.
*   **Methodology:** Implements the **Sharp & Cremer Law** for Mass-Spring-Mass systems, accounting for critical frequency ($f_c$) and resonance ($f_0$).
*   **Key Insight:** The Lattice system achieves high acoustic performance despite its light weight by leveraging the mechanical decoupling of the double-shell structure.

### 🌡️ Thermal Solver
*   **Objective:** Optimize Winter Insulation ($U-value$) and Summer Comfort (Phase Shift).
*   **Methodology:**
    *   **Static:** ISO 6946 (Combined Method) for condensation risk and thickness optimization.
    *   **Dynamic:** **ISO 13786 (Matrix Transfer Method)** using `becalib` to simulate heat wave damping.
*   **Key Insight:** The system delivers a **15.3-hour Phase Shift** (vs. 7.9h for Concrete), proving that wood fibre density provides superior thermal inertia for summer comfort.

### 🌍 Carbon Solver (RE2020)
*   **Objective:** Assess the Carbon Weight ($kgCO_2eq/m^2$) under the RE2020 Dynamic LCA standard.
*   **Methodology:** Dynamic lifecycle assessment ($Ic_{component}$) using certified **INIES FDES** data, integrating production impacts (A1-A5), weighted end-of-life (C1-C4), and biogenic credits (Module D).
*   **Key Insight:** The Lattice system offers the best trade-off: it achieves a **Net Negative Carbon Footprint** by minimizing material usage (low production impact) while maximizing biogenic storage in the wood fibre insulation.

### 🏗️ Fabrication Solver
*   **Output:** Automated generation of Cutting Lists (BOM) and Assembly Guides directly from the `Core` geometry.

---

## 📂 Repository Structure
<pre>
aec-computational-platform/
├── connectors/           # [INPUT] Bridges to external software
│   ├── speckle.py
│   └── rhino.py
│
├── core/                 # [PIVOT] Standardized Python Objects
│   ├── elements.py       # WallBuildUp Class definition
│   └── materials.py      # Physical Material Database
│
└── solvers/              # [OUTPUT] Analysis & Fabrication Engines
    ├── physics/          # Design Analysis
    │   ├── acoustics/    # Sound (Rw) / ISO 10140 Simulation & Visualization
    │   └── thermal/      # Heat transfer calculation (U-value)
    └── production/       # Construction Analysis
        ├── fabrication/  # Cutting lists (BOM)
        └── logistics/    # Lifting weight & COG
</pre>
