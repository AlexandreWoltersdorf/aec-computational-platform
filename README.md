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
The heart of the system. Once ingested, data becomes a **`WallBuildUp`**.
*   **Role:** Define the standard object (Structure + Layers) independent of the source software.

### 3. Solvers (Output)
Engines that consume the Core object to generate results.
*   **Physics Solvers:** Acoustics ($R_w$), Thermal ($U-value$), Carbon ($CO_2$).
*   **Fabrication Solvers:** Cutting lists (BOM), Assembly guides.

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
    ├── acoustics/        # ISO 10140 Simulation & Visualization
    ├── thermal/          # Heat transfer calculation
    └── fabrication/      # Cutting lists (BOM) & CNC data
</pre>
