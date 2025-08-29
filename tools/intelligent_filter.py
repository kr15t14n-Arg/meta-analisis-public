import os
from collections import defaultdict
from typing import List, Tuple, Dict, Any, Union

from .metadata_utils import parse_metadata_to_dict, extract_core_fields, try_get_float_coords

# metadata_items: lista de dicts o tuplas
#   - NUEVO formato preferido: {"filename": str, "path": str, "metadata": str}
#   - Compatibilidad: lista de tuplas (filename, metadata_str)


def _coerce_items(metadata_items: List[Union[Tuple[str, str], Dict[str, Any]]]):
    """Normaliza a una lista de dicts con keys: filename, path (puede ser ""), metadata."""
    norm = []
    for item in metadata_items:
        if isinstance(item, dict):
            filename = item.get("filename") or os.path.basename(item.get("path", "")) or "desconocido"
            path = item.get("path", "")
            metadata = item.get("metadata", "")
        else:
            # tupla (filename, metadata)
            filename, metadata = item
            path = ""
        norm.append({"filename": filename, "path": path, "metadata": metadata})
    return norm


def group_by_same_day(items):
    groups = defaultdict(list)
    for it in items:
        meta = parse_metadata_to_dict(it["metadata"])
        core = extract_core_fields(meta)
        day = core.get("date")   # ✅ usamos "date" (no "date_day")
        if day:
            groups[day].append(it["filename"])
    return {k: v for k, v in groups.items() if len(v) >= 2}


def group_by_camera(items):
    groups = defaultdict(list)
    for it in items:
        meta = parse_metadata_to_dict(it["metadata"])
        core = extract_core_fields(meta)
        cam = core.get("camera")   # ✅ usamos "camera"
        if cam:
            groups[cam].append(it["filename"])
    return {k: v for k, v in groups.items() if len(v) >= 2}


def group_by_software(items):
    groups = defaultdict(list)
    for it in items:
        meta = parse_metadata_to_dict(it["metadata"])
        core = extract_core_fields(meta)
        sw = core.get("software")   # ✅ usamos "software"
        if sw:
            groups[sw].append(it["filename"])
    return {k: v for k, v in groups.items() if len(v) >= 2}


def cluster_by_geo_proximity(items, max_distance_m=250):
    """
    Agrupa por proximidad geográfica simple: pares a < max_distance_m.
    Implementación básica (no clustering jerárquico completo): forma 'bolsitas' por cercanía.
    """
    from math import radians, sin, cos, asin, sqrt

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        return 2 * R * asin(sqrt(a))

    coords = []
    for it in items:
        meta = parse_metadata_to_dict(it["metadata"])
        lat, lon = try_get_float_coords(meta)
        if lat is not None and lon is not None:
            coords.append((it["filename"], lat, lon))

    groups = []
    used = set()
    for i in range(len(coords)):
        if i in used:
            continue
        name_i, lat_i, lon_i = coords[i]
        group = [name_i]
        used.add(i)
        for j in range(i+1, len(coords)):
            if j in used:
                continue
            name_j, lat_j, lon_j = coords[j]
            d = haversine(lat_i, lon_i, lat_j, lon_j)
            if d <= max_distance_m:
                group.append(name_j)
                used.add(j)
        if len(group) >= 2:
            groups.append(group)
    return groups


def build_correlation_report(metadata_items) -> str:
    items = _coerce_items(metadata_items)
    by_day = group_by_same_day(items)
    by_cam = group_by_camera(items)
    by_sw = group_by_software(items)
    by_geo = cluster_by_geo_proximity(items, max_distance_m=250)

    lines = []
    lines.append("=== Coincidencias detectadas ===\n")

    if by_day:
        lines.append("[Por misma fecha (YYYY-MM-DD)]")
        for day, files in by_day.items():
            lines.append(f"  - {day}: {', '.join(files)}")
        lines.append("")
    if by_cam:
        lines.append("[Por misma cámara]")
        for cam, files in by_cam.items():
            lines.append(f"  - {cam}: {', '.join(files)}")
        lines.append("")
    if by_sw:
        lines.append("[Por mismo software]")
        for sw, files in by_sw.items():
            lines.append(f"  - {sw}: {', '.join(files)}")
        lines.append("")
    if by_geo:
        lines.append("[Por proximidad geográfica (~≤250m)]")
        for idx, group in enumerate(by_geo, 1):
            lines.append(f"  - Grupo {idx}: {', '.join(group)}")
        lines.append("")

    if len(lines) == 1:
        lines.append("No se encontraron coincidencias relevantes (con los criterios actuales).")

    return "\n".join(lines).strip()
