from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple
from shapely.geometry import GeometryCollection, Polygon, box
from shapely.ops import unary_union
from .openings import Opening

OPENING_CLEARANCE = 1.0

@dataclass
class LatticeElement:
    element_id: str
    element_type: str
    layer: int
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float
    orientation: str

    @property
    def length(self) -> float:
        return self.z_max - self.z_min

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def thickness(self) -> float:
        return self.y_max - self.y_min

    def as_dict(self) -> Dict[str, float]:
        return {
            "id": self.element_id,
            "element_type": self.element_type,
            "layer": self.layer,
            "orientation": self.orientation,
            "x_min": self.x_min,
            "x_max": self.x_max,
            "y_min": self.y_min,
            "y_max": self.y_max,
            "z_min": self.z_min,
            "z_max": self.z_max,
            "length": self.length,
            "width": self.width,
            "thickness": self.thickness,
        }


@dataclass
class LatticeLayout:
    elements: List[LatticeElement]
    post_positions: List[float]
    traverse_positions: List[float]
    layer_ranges: List[Tuple[float, float]]

    def elements_of_type(self, element_type: str) -> List[LatticeElement]:
        return [elem for elem in self.elements if elem.element_type == element_type]

    def as_dict(self) -> Dict[str, Iterable[Dict[str, float]]]:
        return {
            "elements": [elem.as_dict() for elem in self.elements],
            "post_positions": self.post_positions,
            "traverse_positions": self.traverse_positions,
            "layer_ranges": self.layer_ranges,
        }



# Multilayer wall

@dataclass
class LayerElement:
    element_id: str         # 
    element_type: str       # batten / insulation / OSB / air gap / cement board...
    layer: int         # -2 -1 (layer_index de la classe layer)
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float
    orientation: str # "vertical" / "horizontal"

    @property
    def length(self) -> float:
        # selon la nature de la coupe/pose de l’élément
        return self.z_max - self.z_min

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def thickness(self) -> float:
        return self.y_max - self.y_min

    def as_dict(self) -> Dict:
        return {
            "id": self.element_id,
            "element_type": self.element_type,
            "layer": self.layer,
            "orientation": self.orientation,
            "x_min": self.x_min,
            "x_max": self.x_max,
            "y_min": self.y_min,
            "y_max": self.y_max,
            "z_min": self.z_min,
            "z_max": self.z_max,
            "length": self.length,
            "width": self.width,
            "thickness": self.thickness,
        }
        
@dataclass
class Layer:
    layer_index: int # on prend -2 -1 [LEKO 1-5]  6 7 ...
    name: str
    layer_type: str  # "continuous" ou "battened"
    y_min: float
    y_max: float
    layer_pitch: float             # Découpage/principale subdivision de la couche
    layer_orientation: str         # "vertical", "horizontal"
    batten_width: float
    include_insulation: bool
    materials: Dict[str, str]  # Ex: {"surface": "OSB3"} ou {"batten": "Douglas", "fill": "Laine minérale"}
    elements: List[LayerElement]

    @property
    def thickness(self) -> float:
        return self.y_max - self.y_min

    def as_dict(self) -> Dict:
        return {
            "layer_index": self.layer_index,
            "name": self.name,
            "layer_type": self.layer_type,
            "thickness": self.thickness,
            "y_min": self.y_min,
            "y_max": self.y_max,
            "layer_pitch": self.layer_pitch,
            "layer_orientation": self.layer_orientation,
            "batten_width": self.batten_width,
            "include_insulation": self.include_insulation,
            "materials": self.materials,
            "elements": [e.as_dict() for e in self.elements]
        }


@dataclass
class WallBuildUp:
    panel_id: str
    panel_width: float               # Largeur du mur [mm]
    panel_height: float              # Hauteur du mur [mm]
    openings: Sequence[Opening]
    opening_voids: Sequence[Polygon]
    lattice: LatticeLayout     # Ossature principale (déjà existante)
    layers: List[Layer]        # Liste ordonnée (int -> ext)
    
    def total_thickness(self) -> float:
        # Sommation des épaisseurs de toutes les couches, y.c. la lattice principale
        t_lattice = self.lattice.layer_ranges[-1][1] if self.lattice.layer_ranges else 0
        t_layers = sum(layer.thickness for layer in self.layers)
        return t_lattice + t_layers

    def layers_of_type(self, name: str) -> List[Layer]:
        return [layer for layer in self.layers if layer.name == name]

    def as_dict(self) -> Dict:
        return {
            "panel_id": self.panel_id,
            "panel_width": self.panel_width,
            "panel_height": self.panel_height,
            "total_thickness": self.total_thickness(),
            "lattice": self.lattice.as_dict(),
            "layers": [layer.as_dict() for layer in self.layers],
        }



    

def get_layer_thickness(panel_type: str) -> List[float]:
    mapping = {
        "3L90": [30, 30, 30],
        "3L110": [40, 30, 40],
        "5L150": [30, 30, 30, 30, 30],
        "5L180": [40, 30, 40, 30, 40],
        "5L210": [40, 40, 40, 40, 40],
    }
    if panel_type not in mapping:
        raise ValueError(f"Unknown panel type '{panel_type}'.")
    return mapping[panel_type]


def get_range_thickness(layer_thickness: Sequence[float]) -> List[Tuple[float, float]]:
    ranges: List[Tuple[float, float]] = []
    offset = 0.0
    for thickness in layer_thickness:
        ranges.append((offset, offset + thickness))
        offset += thickness
    return ranges


def _fill_positions(
    base_positions: Iterable[float],
    pitch: float,
    slat_width: float,
    limit: float,
) -> List[float]:
    if pitch <= 0:
        clipped = [max(0.0, min(pos, limit)) for pos in base_positions]
        return sorted(set(clipped))

    positions = sorted(set(base_positions))
    changed = True
    while changed:
        changed = False
        new_positions: List[float] = []
        for left, right in zip(positions[:-1], positions[1:]):
            gap = right - left
            if gap <= pitch:
                continue
            steps = int(gap // pitch)
            for step in range(1, steps + 1):
                candidate = left + step * pitch
                if step == steps and candidate + slat_width > right:
                    candidate = max(right - slat_width, left)
                if left < candidate < right:
                    candidate = max(0.0, min(candidate, limit))
                    if candidate not in positions and candidate not in new_positions:
                        new_positions.append(candidate)
            if new_positions:
                changed = True
        if changed:
            positions = sorted(set(positions + new_positions))

    clipped = [max(0.0, min(pos, limit)) for pos in positions]
    return sorted(set(clipped))


def compute_post_positions(
    panel_width: float,
    horizontal_pitch: float,
    slat_width: float,
    openings: Iterable[Opening],
) -> List[float]:
    limit = max(panel_width - slat_width, 0.0) # pourquoi 0 ? (+ robuste? on ne vas pas faire des panneaux de moins de 120mm c'est inutile : vérifier plutot l'input)
    base = [0.0, limit]  
    for opening in openings:
        x_min, _, x_max, _ = opening.bounds
        base.extend([x_min - slat_width, x_max])
    return _fill_positions(base, horizontal_pitch, slat_width, limit)


def compute_traverse_positions(
    panel_height: float,
    vertical_pitch: float,
    slat_width: float,
    openings: Iterable[Opening],
) -> List[float]:
    limit = max(panel_height - slat_width, 0.0)
    base = [0.0, limit]
    for opening in openings:
        _, z_min, _, z_max = opening.bounds
        base.extend([z_min - slat_width, z_max])
    return _fill_positions(base, vertical_pitch, slat_width, limit)


def _collect_polygons(geometry) -> List[Polygon]:
    if geometry.is_empty:
        return []
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, GeometryCollection):
        polygons: List[Polygon] = []
        for geom in geometry.geoms:
            polygons.extend(_collect_polygons(geom))
        return polygons
    if hasattr(geometry, "geoms"):
        polygons = []
        for geom in geometry.geoms:
            polygons.extend(_collect_polygons(geom))
        return polygons
    return []


def _heal(g, tol=1e-6):
    """Close hairline gaps and remove slivers from boolean ops."""
    if g.is_empty:
        return g
    return g.buffer(tol).buffer(-tol)


def generate_lattice_layout(
    panel_id: str,
    panel_width: float,
    panel_height: float,
    vertical_pitch: float,
    horizontal_pitch: float,
    slat_width: float,
    panel_type: str,
    openings: Sequence[Opening],
    include_insulation: bool = True,
    opening_voids: Sequence[Polygon] = (),   # precise boolean geoms (optional)
) -> LatticeLayout:
    openings_list = list(openings)

    # Prefer true void shapes if provided; otherwise fall back to rectangular AABBs
    if opening_voids:
        opening_polys = list(opening_voids)
    else:
        opening_polys = [opening.to_polygon() for opening in openings_list]

    # Build a buffered opening union so slats/insulation never encroach,
    # even with floating-point fuzz along shared edges.
    if opening_polys:
        openings_raw_union = unary_union(opening_polys)
        openings_union = openings_raw_union.buffer(OPENING_CLEARANCE)
    else:
        openings_union = None

    layer_thickness = get_layer_thickness(panel_type)
    layer_ranges = get_range_thickness(layer_thickness)

    post_positions = compute_post_positions(
        panel_width, horizontal_pitch, slat_width, openings_list
    )
    traverse_positions = compute_traverse_positions(
        panel_height, vertical_pitch, slat_width, openings_list
    )

    elements: List[LatticeElement] = []

    # --------------------------------
    # 1) BUILD ALL SLATS PER LAYER
    # --------------------------------
    for layer_index, (y_min, y_max) in enumerate(layer_ranges, start=1):
        layer_polys: List[Polygon] = []

        if layer_index % 2 == 1:
            # Vertical slats (posts)
            segment_counter = 0
            for idx, x_pos in enumerate(post_positions):
                x_min = max(0.0, min(x_pos, panel_width - slat_width))
                x_max = min(panel_width, x_min + slat_width)
                base_geom = box(x_min, 0.0, x_max, panel_height)

                geom = base_geom
                if openings_union:
                    geom = geom.difference(openings_union)
                geom = _heal(geom, tol=1e-6)

                for piece in _collect_polygons(geom):
                    x0, z0, x1, z1 = piece.bounds
                    if (x1 - x0) <= 1e-6 or (z1 - z0) <= 1e-6:
                        continue
                    segment_counter += 1
                    element_id = f"{panel_id}-L{layer_index}-P{idx}-{segment_counter}"
                    elements.append(
                        LatticeElement(
                            element_id=element_id,
                            element_type="slat",
                            layer=layer_index,
                            orientation="vertical",
                            x_min=x0,
                            x_max=x1,
                            y_min=y_min,
                            y_max=y_max,
                            z_min=z0,
                            z_max=z1,
                        )
                    )
                    layer_polys.append(piece)

        else:
            # Horizontal slats (traverses)
            segment_counter = 0
            for idx, z_pos in enumerate(traverse_positions):
                z_min = max(0.0, min(z_pos, panel_height - slat_width))
                z_max = min(panel_height, z_min + slat_width)
                base_geom = box(0.0, z_min, panel_width, z_max)

                geom = base_geom
                if openings_union:
                    geom = geom.difference(openings_union)
                geom = _heal(geom, tol=1e-6)

                for piece in _collect_polygons(geom):
                    x0, z0, x1, z1 = piece.bounds
                    if (x1 - x0) <= 1e-6 or (z1 - z0) <= 1e-6:
                        continue
                    segment_counter += 1
                    element_id = f"{panel_id}-L{layer_index}-T{idx}-{segment_counter}"
                    elements.append(
                        LatticeElement(
                            element_id=element_id,
                            element_type="slat",
                            layer=layer_index,
                            orientation="horizontal",
                            x_min=x0,
                            x_max=x1,
                            y_min=y_min,
                            y_max=y_max,
                            z_min=z0,
                            z_max=z1,
                        )
                    )
                    layer_polys.append(piece)

        # --------------------------------
        # 2) INSULATION PER LAYER
        # --------------------------------
        if include_insulation:
            envelope = box(0.0, 0.0, panel_width, panel_height)

            if layer_index % 2 == 1:
                # VERTICAL LAYER:
                # insulation between vertical slats of THIS layer,
                # also avoiding openings.
                occupied = layer_polys.copy()
                if openings_union:
                    occupied.append(openings_union)
                if occupied:
                    occupied_union = unary_union(occupied)
                    insulation_geom = envelope.difference(occupied_union)
                else:
                    insulation_geom = envelope
                insulation_geom = _heal(insulation_geom, tol=1e-6)

                for idx, piece in enumerate(_collect_polygons(insulation_geom), start=1):
                    x0, z0, x1, z1 = piece.bounds
                    if (x1 - x0) <= 1e-6 or (z1 - z0) <= 1e-6:
                        continue
                    element_id = f"{panel_id}-L{layer_index}-I{idx}"
                    elements.append(
                        LatticeElement(
                            element_id=element_id,
                            element_type="insulation",
                            layer=layer_index,
                            orientation="surface",
                            x_min=x0,
                            x_max=x1,
                            y_min=y_min,
                            y_max=y_max,
                            z_min=z0,
                            z_max=z1,
                        )
                    )
            else:
                # HORIZONTAL LAYER:
                # insulation between horizontal slats of THIS layer (bands along Z),
                # also avoiding openings (buffered).
                # 1D intervals of slats along Z
                slat_intervals: List[Tuple[float, float]] = []
                for z_pos in traverse_positions:
                    z_min = max(0.0, min(z_pos, panel_height - slat_width))
                    z_max = min(panel_height, z_min + slat_width)
                    slat_intervals.append((z_min, z_max))

                # Merge overlapping intervals
                slat_intervals.sort(key=lambda ab: ab[0])
                merged: List[Tuple[float, float]] = []
                eps = 1e-9
                for a, b in slat_intervals:
                    if not merged:
                        merged.append([a, b])
                    else:
                        la, lb = merged[-1]
                        if a <= lb + eps:
                            merged[-1][1] = max(lb, b)
                        else:
                            merged.append([a, b])
                merged_intervals = [(a, b) for a, b in merged]

                # Gaps between slat bands along Z
                gaps: List[Tuple[float, float]] = []
                prev = 0.0
                for a, b in merged_intervals:
                    if a > prev + eps:
                        gaps.append((prev, a))
                    prev = max(prev, b)
                if prev < panel_height - eps:
                    gaps.append((prev, panel_height))

                # For each gap: full-width band, then subtract buffered openings
                for gap_idx, (gz0, gz1) in enumerate(gaps, start=1):
                    base_gap = box(0.0, gz0, panel_width, gz1)
                    geom_gap = base_gap
                    if openings_union:
                        geom_gap = geom_gap.difference(openings_union)
                    geom_gap = _heal(geom_gap, tol=1e-6)

                    for piece in _collect_polygons(geom_gap):
                        x0, z0, x1, z1 = piece.bounds
                        if (x1 - x0) <= 1e-6 or (z1 - z0) <= 1e-6:
                            continue
                        element_id = f"{panel_id}-L{layer_index}-I{gap_idx}"
                        elements.append(
                            LatticeElement(
                                element_id=element_id,
                                element_type="insulation",
                                layer=layer_index,
                                orientation="surface",
                                x_min=x0,
                                x_max=x1,
                                y_min=y_min,
                                y_max=y_max,
                                z_min=z0,
                                z_max=z1,
                            )
                        )

    return LatticeLayout(
        elements=elements,
        post_positions=post_positions,
        traverse_positions=traverse_positions,
        layer_ranges=layer_ranges,
    )



def generate_layer(
        panel_id: str,
        panel_width: float,
        panel_height: float,
        openings: Sequence[Opening],
        y_min: float,
        y_max: float,
        layer_index: str,
        name: str,
        layer_type: str,
        layer_pitch: float,
        layer_orientation: str,
        batten_width: float,
        include_insulation: bool = True,
        materials: Dict[str, str] = None, # {"batten": "Douglas", "insulation": "Mineral wool"}
        opening_voids: Sequence[Polygon] = (),   # precise boolean geoms (optional)
    ) -> Layer:
    
    openings_list = list(openings)

    # Prefer true void shapes if provided; otherwise fall back to rectangular AABBs
    if opening_voids:
        opening_polys = list(opening_voids)
    else:
        opening_polys = [opening.to_polygon() for opening in openings_list]

    # Build a buffered opening union so slats/insulation never encroach,
    # even with floating-point fuzz along shared edges.
    if opening_polys:
        openings_raw_union = unary_union(opening_polys)
        openings_union = openings_raw_union.buffer(OPENING_CLEARANCE)
    else:
        openings_union = None

    elements: List[LayerElement] = []
    layer_polys: List[Polygon] = []
    # continuous layer
    #if layer_type == 'continuous':
        
    #    if layer_orientation == 'vertical':
    #        cut_positions = compute_post_positions(
    #            panel_width, layer_pitch, 0, openings_list
    #        )
        
    #    if layer_orientation == 'horizontal':
    #        cut_positions = compute_traverse_positions(
    #            panel_height, layer_pitch, 0, openings_list
    #        )
    

    # battened layer
    if layer_type == 'battened':
        fill_material = [key for key in materials.keys() if key != "batten"][0]
        
        if layer_orientation == 'vertical':

            # batten 
            post_positions = compute_post_positions(
                panel_width, layer_pitch, batten_width, openings_list
            )

            # Vertical slats (posts)
            segment_counter = 0
            for idx, x_pos in enumerate(post_positions):
                x_min = max(0.0, min(x_pos, panel_width - batten_width))
                x_max = min(panel_width, x_min + batten_width)
                base_geom = box(x_min, 0.0, x_max, panel_height)

                geom = base_geom
                if openings_union:
                    geom = geom.difference(openings_union)
                geom = _heal(geom, tol=1e-6)

                for piece in _collect_polygons(geom):
                    x0, z0, x1, z1 = piece.bounds
                    if (x1 - x0) <= 1e-6 or (z1 - z0) <= 1e-6:
                        continue
                    segment_counter += 1
                    element_id = f"{panel_id}-L{layer_index}-P{idx}-{segment_counter}"
                    elements.append(
                        LatticeElement(
                            element_id=element_id,
                            element_type="batten",
                            layer=layer_index,
                            orientation="vertical",
                            x_min=x0,
                            x_max=x1,
                            y_min=y_min,
                            y_max=y_max,
                            z_min=z0,
                            z_max=z1,
                        )
                    )
                    layer_polys.append(piece)

            if include_insulation:
                envelope = box(0.0, 0.0, panel_width, panel_height)


                # VERTICAL LAYER:
                # insulation between vertical slats of THIS layer,
                # also avoiding openings.
                occupied = layer_polys.copy()
                if openings_union:
                    occupied.append(openings_union)
                if occupied:
                    occupied_union = unary_union(occupied)
                    insulation_geom = envelope.difference(occupied_union)
                else:
                    insulation_geom = envelope
                insulation_geom = _heal(insulation_geom, tol=1e-6)

                for idx, piece in enumerate(_collect_polygons(insulation_geom), start=1):
                    x0, z0, x1, z1 = piece.bounds
                    if (x1 - x0) <= 1e-6 or (z1 - z0) <= 1e-6:
                        continue
                    element_id = f"{panel_id}-L{layer_index}-I{idx}"
                    elements.append(
                        LatticeElement(
                            element_id=element_id,
                            element_type=fill_material,
                            layer=layer_index,
                            orientation="surface",
                            x_min=x0,
                            x_max=x1,
                            y_min=y_min,
                            y_max=y_max,
                            z_min=z0,
                            z_max=z1,
                        )
                    )

        if layer_orientation == 'horizontal':

            traverse_positions = compute_traverse_positions(
                panel_height, layer_pitch, batten_width, openings_list
            )
            # Horizontal slats (traverses)
            segment_counter = 0
            for idx, z_pos in enumerate(traverse_positions):
                z_min = max(0.0, min(z_pos, panel_height - batten_width))
                z_max = min(panel_height, z_min + batten_width)
                base_geom = box(0.0, z_min, panel_width, z_max)

                geom = base_geom
                if openings_union:
                    geom = geom.difference(openings_union)
                geom = _heal(geom, tol=1e-6)

                for piece in _collect_polygons(geom):
                    x0, z0, x1, z1 = piece.bounds
                    if (x1 - x0) <= 1e-6 or (z1 - z0) <= 1e-6:
                        continue
                    segment_counter += 1
                    element_id = f"{panel_id}-L{layer_index}-T{idx}-{segment_counter}"
                    elements.append(
                        LatticeElement(
                            element_id=element_id,
                            element_type="batten",
                            layer=layer_index,
                            orientation="horizontal",
                            x_min=x0,
                            x_max=x1,
                            y_min=y_min,
                            y_max=y_max,
                            z_min=z0,
                            z_max=z1,
                        )
                    )
                    layer_polys.append(piece)

            if include_insulation:
                envelope = box(0.0, 0.0, panel_width, panel_height)

                # HORIZONTAL LAYER:
                # insulation between horizontal slats of THIS layer (bands along Z),
                # also avoiding openings (buffered).
                # 1D intervals of slats along Z
                slat_intervals: List[Tuple[float, float]] = []
                for z_pos in traverse_positions:
                    z_min = max(0.0, min(z_pos, panel_height - batten_width))
                    z_max = min(panel_height, z_min + batten_width)
                    slat_intervals.append((z_min, z_max))

                # Merge overlapping intervals
                slat_intervals.sort(key=lambda ab: ab[0])
                merged: List[Tuple[float, float]] = []
                eps = 1e-9
                for a, b in slat_intervals:
                    if not merged:
                        merged.append([a, b])
                    else:
                        la, lb = merged[-1]
                        if a <= lb + eps:
                            merged[-1][1] = max(lb, b)
                        else:
                            merged.append([a, b])
                merged_intervals = [(a, b) for a, b in merged]

                # Gaps between slat bands along Z
                gaps: List[Tuple[float, float]] = []
                prev = 0.0
                for a, b in merged_intervals:
                    if a > prev + eps:
                        gaps.append((prev, a))
                    prev = max(prev, b)
                if prev < panel_height - eps:
                    gaps.append((prev, panel_height))

                # For each gap: full-width band, then subtract buffered openings
                for gap_idx, (gz0, gz1) in enumerate(gaps, start=1):
                    base_gap = box(0.0, gz0, panel_width, gz1)
                    geom_gap = base_gap
                    if openings_union:
                        geom_gap = geom_gap.difference(openings_union)
                    geom_gap = _heal(geom_gap, tol=1e-6)

                    for piece in _collect_polygons(geom_gap):
                        x0, z0, x1, z1 = piece.bounds
                        if (x1 - x0) <= 1e-6 or (z1 - z0) <= 1e-6:
                            continue
                        element_id = f"{panel_id}-L{layer_index}-I{gap_idx}"
                        elements.append(
                            LatticeElement(
                                element_id=element_id,
                                element_type=fill_material,
                                layer=layer_index,
                                orientation="surface",
                                x_min=x0,
                                x_max=x1,
                                y_min=y_min,
                                y_max=y_max,
                                z_min=z0,
                                z_max=z1,
                            )
                        )

    return Layer(
        layer_index=layer_index,
        name=name,
        layer_type=layer_type,
        y_min=y_min,
        y_max=y_max,
        layer_pitch=layer_pitch,
        layer_orientation=layer_orientation,
        batten_width=batten_width,
        include_insulation=include_insulation,
        materials=materials,
        elements=elements,
    )

def generate_wall_buildup(
    panel_id: str,
    panel_width: float,
    panel_height: float,
    openings: Sequence[Opening],
    lattice_config: Dict,             # Dict avec SEULEMENT les paramètres d'ossature
    layer_configs: Sequence[Dict],    # Liste de dicts avec SEULEMENT les paramètres de couche
    opening_voids: Sequence[Polygon] = (),  # Optionnel, défaut: tuple vide
) -> WallBuildUp:
    """
    Generate a WallBuildUp object from global info and specific configs for each layer and the lattice.
    """
    # Generate the main framework (lattice)
    lattice = generate_lattice_layout(
        panel_id=panel_id,
        panel_width=panel_width,
        panel_height=panel_height,
        openings=openings,
        opening_voids=opening_voids,
        **lattice_config
    )

    # Generate the wall layers
    layers = []
    for layer_cfg in layer_configs:
        layer = generate_layer(
            panel_id=panel_id,
            panel_width=panel_width,
            panel_height=panel_height,
            openings=openings,
            opening_voids=opening_voids,
            **layer_cfg
        )
        layers.append(layer)

    # Return the complete composition
    buildup = WallBuildUp(
        panel_id=panel_id,
        panel_width=panel_width,
        panel_height=panel_height,
        openings=openings,
        opening_voids=opening_voids,
        lattice=lattice,
        layers=layers
    )
    return buildup






__all__ = [
    "LatticeElement",
    "LatticeLayout",
    "compute_post_positions",
    "compute_traverse_positions",
    "generate_lattice_layout",
    "generate_layer",
    "generate_wall_buildup",
    "get_layer_thickness",
    "get_range_thickness",
]
