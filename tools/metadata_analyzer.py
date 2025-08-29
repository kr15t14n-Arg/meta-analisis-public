import os
import pandas as pd
from typing import List, Tuple, Dict, Any
from tools.metadata_viewer import get_metadata_dict

def analyze_common_metadata(files: List[str], export_csv: str = "image_analysis.csv") -> Tuple[Dict[str, Any], str, list]:
    """
    Analiza metadatos de múltiples imágenes y detecta campos comunes/interesantes.
    - Exporta una tabla CSV con todos los metadatos.
    - Devuelve (common_fields, export_csv, all_rows_as_dicts).
    """
    valid = [f for f in files if os.path.exists(f)]
    rows = []
    for f in valid:
        meta = get_metadata_dict(f)
        meta_row = {"File": f, **meta}
        rows.append(meta_row)

    if not rows:
        return {}, export_csv, []

    df = pd.DataFrame(rows).fillna("")
    df.to_csv(export_csv, index=False, encoding="utf-8")

    # Campos con el MISMO valor en todos los archivos (y no vacío)
    common = {}
    for col in df.columns:
        if col == "File":
            continue
        vals = df[col].unique()
        non_empty = [v for v in vals if str(v).strip() != ""]
        if len(non_empty) == 1 and len(vals) == 1:
            common[col] = non_empty[0]

    return common, export_csv, rows
