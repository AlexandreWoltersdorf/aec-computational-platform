from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple, Optional

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union


AXIS_MAP = {"x": 0, "y": 1, "z": 2}


@dataclass(frozen=True)
class Opening:
    center_x: float
    center_z: float
    width: float
    height: float

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        half_w = self.width / 2.0
        half_h = self.height / 2.0
        return (
            self.center_x - half_w,
            self.center_z - half_h,
            self.center_x + half_w,
            self.center_z + half_h,
        )

    def to_polygon(self):
        x_min, z_min, x_max, z_max = self.bounds
        return box(x_min, z_min, x_max, z_max)


@dataclass
class PanelMetrics:
    width: float
    height: float
    thickness: float
    gross_area: float
    openings_area: float
    net_area: float
    gross_volume: float
    net_volume: float
    openings: List[Opening]


def _polygons_from_projection(
    vertices: np.ndarray,
    faces: np.ndarray,
    axis_a: str,
    axis_b: str,
    area_tol: float = 1e-8,
) -> List[Polygon]:
    idx_a = AXIS_MAP[axis_a]
    idx_b = AXIS_MAP[axis_b]
    polys: List[Polygon] = []
    for tri in faces:
        coords = [
            (vertices[tri[idx], idx_a], vertices[tri[idx], idx_b]) for idx in range(3)
        ]
        poly = Polygon(coords)
        if poly.area > area_tol and poly.is_valid:
            polys.append(poly)
    return polys


def create_union_projections(
    vertices_local: Sequence[Sequence[float]],
    faces: Sequence[Sequence[int]],
    area_tol: float = 1e-8,
) -> Dict[str, Polygon]:
    """Union projected triangles on ZX, ZY and XY planes."""
    verts = np.asarray(vertices_local, dtype=float)
    face_array = np.asarray(faces, dtype=int)
    if face_array.shape[0] == 0:
        raise ValueError("At least one face is required to build projections.")

    polys_zx = _polygons_from_projection(verts, face_array, "x", "z", area_tol)
    polys_zy = _polygons_from_projection(verts, face_array, "y", "z", area_tol)
    polys_xy = _polygons_from_projection(verts, face_array, "x", "y", area_tol)

    return {
        "ZX": unary_union(polys_zx) if polys_zx else Polygon(),
        "ZY": unary_union(polys_zy) if polys_zy else Polygon(),
        "XY": unary_union(polys_xy) if polys_xy else Polygon(),
    }


def compute_opening_voids(
    union_zx: Polygon,
    panel_width: float,
    panel_height: float,
    heal_tol: float = 1e-6,
) -> List[Polygon]:
    """
    Return the actual void polygons inside the panel envelope.
    Includes closed holes and edge-open notches.
    """
    if union_zx.is_empty:
        return []

    geom = union_zx
    if heal_tol and heal_tol > 0:
        geom = geom.buffer(heal_tol).buffer(-heal_tol)

    envelope = box(0.0, 0.0, panel_width, panel_height)
    voids = envelope.difference(geom)
    if voids.is_empty:
        return []

    def _collect_polys(g) -> List[Polygon]:
        if g.is_empty:
            return []
        if isinstance(g, Polygon):
            return [g]
        if hasattr(g, "geoms"):
            out: List[Polygon] = []
            for sub in g.geoms:
                out.extend(_collect_polys(sub))
            return out
        return []

    return _collect_polys(voids)


def extract_openings_from_zx(
    union_zx: Polygon,
    panel_width: float,
    panel_height: float,
    min_width: float = 10.0,
    min_height: float = 10.0,
    min_area: float = 1e-4,
    heal_tol: float = 1e-6,
) -> List[Opening]:
    """
    Detect rectangular openings from the ZX projection, including edge-open cutouts.
    We compute voids = envelope - union_zx, then approximate each void by its AABB.
    """
    void_polys = compute_opening_voids(
        union_zx, panel_width=panel_width, panel_height=panel_height, heal_tol=heal_tol
    )

    openings: List[Opening] = []
    for poly in void_polys:
        if not poly.is_valid or poly.area < min_area:
            continue
        x_min, z_min, x_max, z_max = poly.bounds
        width = x_max - x_min
        height = z_max - z_min
        if width < min_width or height < min_height:
            continue
        openings.append(
            Opening(
                center_x=(x_min + x_max) / 2.0,
                center_z=(z_min + z_max) / 2.0,
                width=width,
                height=height,
            )
        )
    return openings


def compute_panel_metrics(
    vertices_local: Sequence[Sequence[float]],
    union_zx: Polygon,
    openings: Iterable[Opening],
) -> PanelMetrics:
    """Summarize panel dimensions and area/volume metrics."""
    verts = np.asarray(vertices_local, dtype=float)
    width = float(verts[:, 0].max() - verts[:, 0].min())
    thickness = float(verts[:, 1].max() - verts[:, 1].min())
    height = float(verts[:, 2].max() - verts[:, 2].min())

    gross_area = float(union_zx.area)
    openings_list = list(openings)
    openings_area = float(sum(op.width * op.height for op in openings_list))
    net_area = gross_area - openings_area
    gross_volume = gross_area * thickness
    net_volume = net_area * thickness

    return PanelMetrics(
        width=width,
        height=height,
        thickness=thickness,
        gross_area=gross_area,
        openings_area=openings_area,
        net_area=net_area,
        gross_volume=gross_volume,
        net_volume=net_volume,
        openings=openings_list,
    )


__all__ = [
    "Opening",
    "PanelMetrics",
    "create_union_projections",
    "extract_openings_from_zx",
    "compute_opening_voids",
    "compute_panel_metrics",
]
