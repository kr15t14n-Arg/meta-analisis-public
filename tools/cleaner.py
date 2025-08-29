import subprocess
import os
from typing import List, Tuple, Optional

def clean_with_exiftool(input_path: str, output_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Limpia metadatos de una imagen usando ExifTool.
    - Si output_path es None, sobrescribe el archivo original.
    - Devuelve (success, mensaje_exiftool).
    """
    if not os.path.exists(input_path):
        return False, f"No existe el archivo: {input_path}"

    if output_path:
        cmd = ["exiftool", "-all=", "-o", output_path, input_path]
    else:
        cmd = ["exiftool", "-all=", "-overwrite_original", input_path]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return (result.returncode == 0), (result.stdout or result.stderr)


def clean_batch(input_files: List[str], output_dir: str = "clean") -> list:
    """
    Limpia múltiples imágenes y las guarda en `output_dir`.
    Devuelve lista de tuplas: [(file, success, msg, out_path | None), ...]
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for f in input_files:
        base = os.path.basename(f)
        name, ext = os.path.splitext(base)
        out_path = os.path.join(output_dir, f"{name}_clean{ext}")
        ok, msg = clean_with_exiftool(f, out_path)
        results.append((f, ok, msg, out_path if ok else None))

    return results
