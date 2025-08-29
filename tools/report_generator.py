import csv
import os

def export_to_txt(metadata_list, output_path="report.txt"):
    """
    Exporta los metadatos a un archivo TXT legible.
    metadata_list = lista de tuplas (filename, metadatos_string)
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for filename, metadata in metadata_list:
            f.write(f"=== Metadatos de {filename} ===\n")
            f.write(metadata.strip() + "\n")
            f.write("-" * 40 + "\n\n")
    return os.path.abspath(output_path)


def export_to_csv(metadata_list, output_path="report.csv"):
    """
    Exporta los metadatos a CSV estructurado (Excel friendly).
    Metadata_list = lista de tuplas (filename, metadatos_string)
    """
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Archivo", "Clave", "Valor"])

        for filename, metadata in metadata_list:
            for line in metadata.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    writer.writerow([filename, key.strip(), value.strip()])

    return os.path.abspath(output_path)
