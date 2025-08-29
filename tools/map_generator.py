import os
import webbrowser
import subprocess
from typing import List, Union, Dict, Any, Tuple

import folium

from .metadata_utils import parse_metadata_to_dict, try_get_float_coords

def _coerce_items(metadata_items):
    norm = []
    for item in metadata_items:
        if isinstance(item, dict):
            filename = item.get("filename") or os.path.basename(item.get("path", "")) or "desconocido"
            path = item.get("path", "")
            metadata = item.get("metadata", "")
        else:
            filename, metadata = item
            path = ""  # sin path, solo podremos intentar parsear desde el texto
        norm.append({"filename": filename, "path": path, "metadata": metadata})
    return norm

def _safe_exiftool_numeric(path: str) -> Tuple[float, float]:
    """
    Intenta obtener GPS numérico con exiftool -n. Lanza excepción si falla.
    """
    result = subprocess.run(
        ["exiftool", "-n", "-GPSLatitude", "-GPSLongitude", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    lat = lon = None
    for line in result.stdout.splitlines():
        if "GPS Latitude" in line and ":" in line:
            lat = float(line.split(":", 1)[1].strip())
        if "GPS Longitude" in line and ":" in line:
            lon = float(line.split(":", 1)[1].strip())
    if lat is None or lon is None:
        raise ValueError("Sin coordenadas")
    return lat, lon

def generate_map(metadata_items, output_html="mapa_meta.html", open_after=True) -> str:
    items = _coerce_items(metadata_items)
    points = []

    # recolectar coordenadas
    for it in items:
        meta = parse_metadata_to_dict(it["metadata"])
        lat, lon = try_get_float_coords(meta)
        if lat is None or lon is None:
            # si tenemos path, intentamos re-consultar con -n
            if it["path"]:
                try:
                    lat, lon = _safe_exiftool_numeric(it["path"])
                except Exception:
                    pass
        if lat is not None and lon is not None:
            points.append((it["filename"], lat, lon))

    if not points:
        raise RuntimeError("No se encontraron coordenadas GPS en los archivos analizados.")

    # centro aproximado
    c_lat = sum(p[1] for p in points) / len(points)
    c_lon = sum(p[2] for p in points) / len(points)

    m = folium.Map(location=[c_lat, c_lon], zoom_start=13, tiles="CartoDB positron")
    for name, lat, lon in points:
        folium.Marker([lat, lon], popup=name).add_to(m)
    m.save(output_html)

    if open_after:
        webbrowser.open(f"file:///{os.path.abspath(output_html)}")

    return os.path.abspath(output_html)
