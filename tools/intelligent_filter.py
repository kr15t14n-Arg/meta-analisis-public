import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Union
from math import radians, sin, cos, asin, sqrt

from .metadata_utils import parse_metadata_to_dict, extract_core_fields, try_get_float_coords


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


def _parse_datetime_from_meta(meta: Dict[str, Any], file_path: str = "") -> Union[datetime, None]:
    """
    Intenta extraer un datetime válido de metadatos EXIF o fallback al file mtime.
    Devuelve un objeto datetime (sin tzinfo preferiblemente).
    """
    date_keys = [
        "EXIF:DateTimeOriginal",
        "EXIF:CreateDate",
        "DateTimeOriginal",
        "CreateDate",
        "Create Date",
        "Date/Time Original",
        "File Modification Date/Time",
        "ModifyDate",
        "Modify Date"
    ]

    date_str = None
    for key in date_keys:
        if key in meta and meta[key]:
            date_str = str(meta[key])
            break

    # fallback: file mtime (solo si hay path)
    if not date_str and file_path:
        try:
            ts = os.path.getmtime(file_path)
            date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            date_str = None

    if not date_str:
        return None

    # Normalizar separadores comunes
    ds = date_str.strip()
    ds = ds.replace("/", ":").replace("-", ":")

    # Eliminar zona horaria final tipo +03:00 o Z si existe (conservar HH:MM:SS)
    if "+" in ds:
        ds = ds.split("+", 1)[0].strip()
    if "Z" in ds:
        ds = ds.replace("Z", "").strip()

    # Probar varios formatos
    fmts = [
        "%Y:%m:%d %H:%M:%S.%f",
        "%Y:%m:%d %H:%M:%S",
        "%Y:%m:%d",
        "%Y:%m:%d:%H:%M:%S"  # a veces exiftool devuelve con ':'
    ]

    for fmt in fmts:
        try:
            return datetime.strptime(ds, fmt)
        except Exception:
            continue

    # último intento: tomar los primeros 3 campos como date
    parts = ds.split()
    if parts:
        date_part = parts[0]
        date_part = date_part.replace(":", "-")
        try:
            return datetime.strptime(date_part, "%Y-%m-%d")
        except Exception:
            return None
    return None


def group_by_same_day(items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Agrupa por fecha de captura (YYYY-MM-DD)."""
    groups = defaultdict(list)
    for it in items:
        meta = parse_metadata_to_dict(it["metadata"])
        dt = _parse_datetime_from_meta(meta, it.get("path", ""))
        if not dt:
            continue
        key = dt.strftime("%Y-%m-%d")
        groups[key].append(it["filename"])
    # limpiar duplicados y ordenar
    out = {}
    for k, v in groups.items():
        unique = sorted(set(v))
        if len(unique) >= 2:
            out[k] = unique
    return out


def group_by_close_hour(items: List[Dict[str, Any]], tolerance_minutes: int = 60) -> List[List[str]]:
    """
    Agrupa archivos cuya diferencia temporal entre pares es <= tolerance_minutes.
    Devuelve lista de grupos (listas de filenames).
    """
    datetimes = []
    for it in items:
        meta = parse_metadata_to_dict(it["metadata"])
        dt = _parse_datetime_from_meta(meta, it.get("path", ""))
        if dt:
            datetimes.append((it["filename"], dt))

    datetimes.sort(key=lambda x: x[1])
    used = set()
    groups = []

    for i in range(len(datetimes)):
        if i in used:
            continue
        name_i, dt_i = datetimes[i]
        group = [name_i]
        used.add(i)
        for j in range(i + 1, len(datetimes)):
            if j in used:
                continue
            name_j, dt_j = datetimes[j]
            diff_min = abs((dt_j - dt_i).total_seconds()) / 60.0
            if diff_min <= tolerance_minutes:
                group.append(name_j)
                used.add(j)
        if len(group) >= 2:
            groups.append(sorted(set(group)))
    return groups


def group_by_camera(items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    groups = defaultdict(list)
    for it in items:
        meta = parse_metadata_to_dict(it["metadata"])
        core = extract_core_fields(meta)
        cam = core.get("camera") or core.get("make") or core.get("camera_model")
        if cam:
            groups[str(cam)].append(it["filename"])
    out = {}
    for k, v in groups.items():
        unique = sorted(set(v))
        if len(unique) >= 2:
            out[k] = unique
    return out


def group_by_software(items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    groups = defaultdict(list)
    for it in items:
        meta = parse_metadata_to_dict(it["metadata"])
        core = extract_core_fields(meta)
        sw = core.get("software") or core.get("creator") or core.get("app")
        if sw:
            groups[str(sw)].append(it["filename"])
    out = {}
    for k, v in groups.items():
        unique = sorted(set(v))
        if len(unique) >= 2:
            out[k] = unique
    return out


def cluster_by_geo_proximity(items: List[Dict[str, Any]], max_distance_m: float = 250.0) -> List[List[str]]:
    """Agrupa por proximidad geográfica simple: bolsas de archivos dentro de max_distance_m."""
    coords = []
    for it in items:
        meta = parse_metadata_to_dict(it["metadata"])
        lat, lon = try_get_float_coords(meta)
        if lat is not None and lon is not None:
            coords.append((it["filename"], float(lat), float(lon)))

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
        return 2 * R * asin(sqrt(a))

    groups = []
    used = set()
    for i in range(len(coords)):
        if i in used:
            continue
        name_i, lat_i, lon_i = coords[i]
        group = [name_i]
        used.add(i)
        for j in range(i + 1, len(coords)):
            if j in used:
                continue
            name_j, lat_j, lon_j = coords[j]
            d = haversine(lat_i, lon_i, lat_j, lon_j)
            if d <= max_distance_m:
                group.append(name_j)
                used.add(j)
        if len(group) >= 2:
            groups.append(sorted(set(group)))
    return groups


def build_correlation_report(metadata_items: List[Union[Tuple[str, str], Dict[str, Any]]],
                             tolerance_minutes: int = 60) -> Tuple[str, Dict[str, Any]]:
    """
    Construye:
      - texto (string) para mostrar en UI (compatibilidad con versiones anteriores)
      - dict estructurado con keys: by_day, by_hour, by_cam, by_sw, by_geo
    Devuelve (texto, estructura)
    """
    items = _coerce_items(metadata_items)
    by_day = group_by_same_day(items)
    by_hour = group_by_close_hour(items, tolerance_minutes=tolerance_minutes)
    by_cam = group_by_camera(items)
    by_sw = group_by_software(items)
    by_geo = cluster_by_geo_proximity(items, max_distance_m=250.0)

    structure = {
        "by_day": by_day,
        "by_hour": by_hour,
        "by_cam": by_cam,
        "by_sw": by_sw,
        "by_geo": by_geo
    }

    lines = []
    lines.append("=== Coincidencias detectadas ===\n")

    if by_day:
        lines.append("[Por misma fecha (YYYY-MM-DD)]")
        for day, files in sorted(by_day.items()):
            lines.append(f"  - {day}: {', '.join(files)}")
        lines.append("")

    if by_hour:
        lines.append("[Por hora cercana (±{}min)]".format(tolerance_minutes))
        for idx, group in enumerate(by_hour, 1):
            lines.append(f"  - Grupo {idx}: {', '.join(group)}")
        lines.append("")

    if by_cam:
        lines.append("[Por misma cámara]")
        for cam, files in sorted(by_cam.items()):
            lines.append(f"  - {cam}: {', '.join(files)}")
        lines.append("")

    if by_sw:
        lines.append("[Por mismo software]")
        for sw, files in sorted(by_sw.items()):
            lines.append(f"  - {sw}: {', '.join(files)}")
        lines.append("")

    if by_geo:
        lines.append("[Por proximidad geográfica (~≤{}m)]".format(250))
        for idx, group in enumerate(by_geo, 1):
            lines.append(f"  - Grupo {idx}: {', '.join(group)}")
        lines.append("")

    if len(lines) == 1:
        lines.append("No se encontraron coincidencias relevantes (con los criterios actuales).")

    text = "\n".join(lines).strip()
    return text, structure
