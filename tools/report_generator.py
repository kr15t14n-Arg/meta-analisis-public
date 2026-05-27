import os
import csv
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


# ==========================================================
# NORMALIZADOR DE CORRELACIONES
# ==========================================================
def _normalize_correlations(correlations: Any) -> Dict[str, List[Tuple[str, List[str]]]]:
    if not correlations:
        return {}

    if isinstance(correlations, dict):
        out = {}
        if correlations.get("by_day"):
            out["Por misma fecha (YYYY-MM-DD)"] = [
                (d, list(files)) for d, files in sorted(correlations["by_day"].items())
            ]
        if correlations.get("by_hour"):
            out["Por hora cercana (±60min)"] = [
                (f"Grupo {i+1}", list(g)) for i, g in enumerate(correlations["by_hour"])
            ]
        if correlations.get("by_cam"):
            out["Por misma cámara"] = [
                (c, list(files)) for c, files in sorted(correlations["by_cam"].items())
            ]
        if correlations.get("by_sw"):
            out["Por mismo software"] = [
                (s, list(files)) for s, files in sorted(correlations["by_sw"].items())
            ]
        if correlations.get("by_geo"):
            out["Por proximidad geográfica (~≤250m)"] = [
                (f"Grupo {i+1}", list(g)) for i, g in enumerate(correlations["by_geo"])
            ]
        return out

    if isinstance(correlations, str):
        lines = [l.strip() for l in correlations.splitlines() if l.strip()]
    elif isinstance(correlations, (list, tuple)):
        lines = []
        for x in correlations:
            if isinstance(x, (list, tuple)):
                lines.extend([str(s).strip() for s in x])
            else:
                lines.append(str(x).strip())
    else:
        return {}

    filtered = [
        l for l in lines
        if l.startswith("[") or l.startswith("-")
        or l.lower().startswith("por ") or l.lower().startswith("grupo ")
    ]

    out = {}
    current_cat = None

    for line in filtered:
        if line.startswith("[") and line.endswith("]"):
            current_cat = line.strip("[]")
            out[current_cat] = []
            continue
        if line.startswith("-") and ":" in line:
            key, val = line[1:].split(":", 1)
            key = key.strip()
            files = [f.strip() for f in val.split(",") if f.strip()]
            if not files:
                continue
            if current_cat is None:
                current_cat = "Coincidencias"
                out[current_cat] = []
            out[current_cat].append((key, files))

    return out


# ==========================================================
# EXPORTADORES TXT y CSV (sin cambios)
# ==========================================================
def export_to_txt(metadata_list, output_path="report.txt"):
    with open(output_path, "w", encoding="utf-8") as f:
        for filename, metadata in metadata_list:
            f.write(f"=== Metadatos de {filename} ===\n")
            f.write(metadata.strip() + "\n")
            f.write("-" * 40 + "\n\n")
    return os.path.abspath(output_path)


def export_to_csv(metadata_list, output_path="report.csv"):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Archivo", "Clave", "Valor"])
        for filename, metadata in metadata_list:
            for line in metadata.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    writer.writerow([filename, k.strip(), v.strip()])
    return os.path.abspath(output_path)


# ==========================================================
# EXPORTAR A PDF — VERSIÓN CORREGIDA CON WORD WRAP
# ==========================================================
def export_to_pdf(metadata_list, correlations=None, output_path="report.pdf"):
    pdf = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50
    )
    elements = []
    styles = getSampleStyleSheet()

    # ----------------------------------------------------------
    # Estilos personalizados
    # ----------------------------------------------------------
    # Estilo para celdas de tabla — soporta word wrap
    cell_style = ParagraphStyle(
        name="CellStyle",
        fontSize=7,
        leading=10,
        wordWrap='CJK',        # wrap agresivo, corta en cualquier carácter si es necesario
        splitLongWords=True,
    )
    cell_bold = ParagraphStyle(
        name="CellBold",
        fontSize=7,
        leading=10,
        fontName="Helvetica-Bold",
        wordWrap='CJK',
        splitLongWords=True,
    )
    styles.add(ParagraphStyle(
        name="Category",
        fontSize=11,
        leading=14,
        textColor=colors.darkblue,
        spaceBefore=10,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name="Value",
        fontSize=9,
        leading=12,
        leftIndent=10
    ))
    styles.add(ParagraphStyle(
        name="BulletList",
        fontSize=8,
        leading=11,
        leftIndent=20
    ))
    styles.add(ParagraphStyle(
        name="Separator",
        fontSize=6,
        spaceBefore=8,
        spaceAfter=4,
        textColor=colors.grey
    ))

    # Ancho útil de la página
    PAGE_WIDTH = A4[0] - 80   # 80 = leftMargin + rightMargin
    COL_KEY   = 160
    COL_VALUE = PAGE_WIDTH - COL_KEY

    def add_watermark(canvas_obj, doc):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica-Bold", 100)
        canvas_obj.setFillGray(0.9, 0.3)
        canvas_obj.rotate(60)
        canvas_obj.drawCentredString(550, -50, "Meta-Analisis")
        canvas_obj.restoreState()

    # ----------------------------------------------------------
    # ENCABEZADO
    # ----------------------------------------------------------
    elements.append(Paragraph("<b>Informe de Análisis preliminar de Metadatos</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 20))

    # ----------------------------------------------------------
    # SECCIÓN 1 — METADATOS POR ARCHIVO
    # ----------------------------------------------------------
    elements.append(Paragraph("1) Detalles de archivos escaneados", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    # Campos a omitir en el PDF (datos binarios o muy voluminosos que no aportan)
    SKIP_KEYS = {"thumbnail image", "xmp meta", "xmp toolkit"}

    for filename, metadata in metadata_list:
        short_name = os.path.basename(filename)
        elements.append(Paragraph(f"<b>Archivo:</b> {short_name}", styles["Normal"]))
        elements.append(Spacer(1, 4))

        # Cabecera de tabla
        table_data = [
            [
                Paragraph("<b>Clave</b>", cell_bold),
                Paragraph("<b>Valor</b>", cell_bold),
            ]
        ]

        for line in metadata.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key   = key.strip()
            value = value.strip()

            # Omitir campos binarios / muy largos que no son legibles
            if key.lower() in SKIP_KEYS:
                continue

            # Escapar caracteres especiales de XML/HTML para ReportLab
            def safe(text):
                return (text
                        .replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;"))

            table_data.append([
                Paragraph(safe(key),   cell_style),
                Paragraph(safe(value), cell_style),
            ])

        table = Table(table_data, colWidths=[COL_KEY, COL_VALUE])
        table.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0),  colors.HexColor("#d9e1f2")),
            ('GRID',        (0, 0), (-1, -1), 0.25, colors.grey),
            ('VALIGN',      (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ('LEFTPADDING',  (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING',   (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 16))

    # ----------------------------------------------------------
    # SECCIÓN 2 — CORRELACIONES
    # ----------------------------------------------------------
    elements.append(PageBreak())
    elements.append(Paragraph("2) Correlaciones Detectadas", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    normalized = _normalize_correlations(correlations)
    if not normalized:
        elements.append(Paragraph(
            "No se encontraron correlaciones detectadas.",
            styles["Normal"]
        ))
    else:
        for category, matches in normalized.items():
            if not matches:
                continue
            elements.append(Paragraph(
                "───────────────────────────────────────────────",
                styles["Separator"]
            ))
            elements.append(Paragraph(f"<b>{category}</b>", styles["Category"]))
            elements.append(Spacer(1, 6))

            for value, files in matches:
                if not files:
                    continue
                elements.append(Paragraph(f"<b>Valor:</b> {value}", styles["Value"]))
                for f in files:
                    elements.append(Paragraph(
                        f"• {os.path.basename(f)}",
                        styles["BulletList"]
                    ))
                elements.append(Spacer(1, 8))

    pdf.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark)
    return os.path.abspath(output_path)