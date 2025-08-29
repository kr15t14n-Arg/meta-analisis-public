import re
from datetime import datetime
from .hash_utils import compute_all_hashes

def parse_metadata_to_dict(metadata_text: str) -> dict:
    """
    Convierte un bloque de texto de ExifTool en un diccionario clave: valor.
    """
    meta = {}
    for line in metadata_text.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip()
    return meta


def normalize_date_to_day(date_str: str) -> str:
    """
    Intenta normalizar distintas fechas a YYYY-MM-DD.
    """
    if not date_str:
        return ""
    # Formatos típicos de fechas en EXIF/PDF/DOCX
    candidates = [
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y:%m:%d",
        "%Y-%m-%d",
    ]
    for fmt in candidates:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return date_str  # fallback: no se pudo parsear


def parse_decimal_from_exif_gps(coord_str: str) -> float:
    """
    Convierte coordenadas GPS tipo "32 deg 54' 10.48\" S" en decimal.
    Maneja hemisferios N/S/E/W.
    """
    if not coord_str:
        return None

    match = re.match(r"(\d+)\s+deg\s+(\d+)'\s+([\d.]+)\"\s+([NSEW])", coord_str)
    if not match:
        return None

    deg, minutes, seconds, hemi = match.groups()
    decimal = float(deg) + float(minutes) / 60 + float(seconds) / 3600

    if hemi in ["S", "W"]:
        decimal *= -1

    return decimal


def try_get_float_coords(meta: dict):
    lat = parse_decimal_from_exif_gps(meta.get("GPS Latitude", ""))
    lon = parse_decimal_from_exif_gps(meta.get("GPS Longitude", ""))
    return lat, lon


def extract_core_fields(meta: dict, file_path: str = None) -> dict:
    """
    Devuelve campos clave estandarizados + hashes.
    """
    fields = {
        "date": normalize_date_to_day(meta.get("File Modification Date/Time", "")
                                      or meta.get("Create Date", "")
                                      or meta.get("Modify Date", "")),
        "camera": (meta.get("Make", "") + " " + meta.get("Model", "")).strip(),
        "software": meta.get("Software", "")
                     or meta.get("Creator", "")
                     or meta.get("Producer", ""),
        "author": meta.get("Author", "")
                   or meta.get("Creator", "")
                   or meta.get("Last Modified By", ""),
    }

    # Coordenadas GPS si existen
    lat, lon = try_get_float_coords(meta)
    if lat is not None and lon is not None:
        fields["gps"] = (lat, lon)

    # Hashes si hay path disponible
    if file_path:
        try:
            hashes = compute_all_hashes(file_path)
            fields.update({
                "hash_md5": hashes["md5"],
                "hash_sha256": hashes["sha256"],
            })
        except Exception as e:
            fields["hash_error"] = str(e)

    return fields
