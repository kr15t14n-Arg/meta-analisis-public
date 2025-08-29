import subprocess
import os
from typing import Dict

def get_metadata_text(input_path: str) -> str:
    """
    Retorna todos los metadatos de la imagen como string legible (formato exiftool por defecto).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No se encontró la imagen: {input_path}")

    result = subprocess.run(["exiftool", input_path], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout


def get_metadata_dict(input_path: str) -> Dict[str, str]:
    """
    Retorna metadatos en forma de diccionario {campo: valor} usando exiftool -s -s -s.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No se encontró la imagen: {input_path}")

    result = subprocess.run(["exiftool", "-s", "-s", "-s", input_path], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    meta = {}
    for line in result.stdout.splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            meta[k.strip()] = v.strip()
    return meta
