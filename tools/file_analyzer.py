import os
import hashlib
import pandas as pd
from typing import List, Tuple, Dict, Any
from docx import Document
from PyPDF2 import PdfReader

def _analyze_txt(path: str) -> Dict[str, Any]:
    meta = {}
    with open(path, "rb") as f:
        content = f.read()
    meta["SizeBytes"] = len(content)
    meta["MD5"] = hashlib.md5(content).hexdigest()
    meta["Lines"] = content.count(b"\n") + 1 if content else 0
    return meta

def _analyze_docx(path: str) -> Dict[str, Any]:
    meta = {}
    doc = Document(path)
    props = doc.core_properties
    meta["Title"] = props.title
    meta["Author"] = props.author
    meta["Created"] = props.created.isoformat() if props.created else None
    meta["LastModifiedBy"] = props.last_modified_by
    meta["Modified"] = props.modified.isoformat() if props.modified else None
    meta["Revision"] = str(props.revision) if props.revision is not None else None
    return meta

def _analyze_pdf(path: str) -> Dict[str, Any]:
    meta = {}
    reader = PdfReader(path)
    info = reader.metadata or {}
    meta["Author"] = info.get("/Author")
    meta["Creator"] = info.get("/Creator")
    meta["Producer"] = info.get("/Producer")
    meta["Title"] = info.get("/Title")
    meta["Created"] = info.get("/CreationDate")
    meta["Modified"] = info.get("/ModDate")
    return meta

def analyze_file(path: str) -> Dict[str, Any]:
    ext = os.path.splitext(path)[1].lower()
    row = {"File": path, "Type": ext}
    try:
        if ext == ".txt":
            row.update(_analyze_txt(path))
        elif ext == ".docx":
            row.update(_analyze_docx(path))
        elif ext == ".pdf":
            row.update(_analyze_pdf(path))
        else:
            row["Error"] = "Formato no soportado"
    except Exception as e:
        row["Error"] = str(e)
    return row

def analyze_multiple_files(files: List[str], export_csv: str = "docs_analysis.csv") -> Tuple[Dict[str, Any], str, list]:
    valid = [f for f in files if os.path.exists(f)]
    rows = [analyze_file(f) for f in valid]
    if not rows:
        return {}, export_csv, []

    df = pd.DataFrame(rows).fillna("")
    df.to_csv(export_csv, index=False, encoding="utf-8")

    # Campos comunes exactos (mismo valor en todos, no vacío)
    common = {}
    for col in df.columns:
        if col in ("File",):
            continue
        vals = df[col].unique()
        non_empty = [v for v in vals if str(v).strip() != ""]
        if len(non_empty) == 1 and len(vals) == 1:
            common[col] = non_empty[0]

    return common, export_csv, rows
