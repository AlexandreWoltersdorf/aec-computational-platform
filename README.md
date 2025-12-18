# AEC Computational Platform

**A personal R&D repository exploring the intersection of BIM data, Computational Geometry, and Engineering Physics.**

The goal of this project is to bridge the gap between standard design tools (Rhino, Speckle) and advanced engineering analysis (Python). Instead of treating walls as simple 3D geometry, this platform converts them into intelligent `WallBuildUp` objects to simulate their physical performance (Acoustics, Thermal, Carbon) and generate fabrication data.

---

## 🔄 The Workflow

The architecture follows a simple 3-step logic (Input → Pivot → Output):

### 1. Input (Connectors)
I don't manually model walls in this repo. I pull geometry from existing BIM workflows.
*   **Interop:** Bridges to **Speckle** and **Rhino/Grasshopper**.
*   **Normalization:** Converting raw external geometry into a clean internal format.

### 2. Core (The Pivot)
The heart of the repo. Once ingested, data becomes a **`WallBuildUp`**.
*   **Object-Oriented:** A wall is defined by its structural system (e.g., Timber Lattice, CLT) and its material layers.
*   **Agnostic:** The physics engines don't care if the geometry came from Revit or Blender; they just read the Core Object.

### 3. Output (Solvers)
I plug various "Solvers" into the Core object to generate insights.
*   **Physics:** Simulating $R_w$ (Sound), $U-values$, or $CO_2$ impact.
*   **Fabrication:** Generating cutting lists and assembly guides.

---

## 📂 Repository Structure

