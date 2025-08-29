import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess, os, webbrowser

import folium
from tools.metadata_utils import parse_metadata_to_dict, extract_core_fields
from tools.intelligent_filter import build_correlation_report

# almacenamiento temporal de resultados
metadata_results = []


def analyze_files(file_paths, output_text):
    global metadata_results
    metadata_results.clear()

    for path in file_paths:
        try:
            result = subprocess.run(
                ["exiftool", path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            meta_text = result.stdout
            meta = parse_metadata_to_dict(meta_text)
            core = extract_core_fields(meta, file_path=path)

            metadata_results.append({
                "filename": os.path.basename(path),
                "path": path,
                "metadata": meta_text,
                "core": core
            })

            output_text.insert(tk.END, f"=== Metadatos de {os.path.basename(path)} ===\n")
            output_text.insert(tk.END, meta_text + "\n")

            # Mostrar campos clave + hashes
            output_text.insert(tk.END, "--- Campos clave normalizados ---\n")
            for k, v in core.items():
                output_text.insert(tk.END, f"{k}: {v}\n")

            output_text.insert(tk.END, "----------------------------------------\n\n")
            output_text.see(tk.END)

        except FileNotFoundError:
            messagebox.showerror("Error", "❌ ExifTool no está instalado o no está en el PATH.")
            break


def select_files(output_text):
    file_paths = filedialog.askopenfilenames(
        title="Selecciona archivos para analizar",
        filetypes=[("Todos los archivos", "*.*")]
    )
    if file_paths:
        analyze_files(file_paths, output_text)


def run_correlations(output_text):
    if not metadata_results:
        messagebox.showwarning("Atención", "Primero analiza archivos antes de buscar coincidencias.")
        return

    report = build_correlation_report(metadata_results)
    output_text.insert(tk.END, "\n=== Reporte de Coincidencias Inteligentes ===\n")
    output_text.insert(tk.END, report + "\n")
    output_text.insert(tk.END, "----------------------------------------\n\n")
    output_text.see(tk.END)


def export_results(output_text):
    if not metadata_results:
        messagebox.showwarning("Atención", "No hay resultados para exportar.")
        return

    save_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Archivo de texto", "*.txt")]
    )
    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            for item in metadata_results:
                f.write(f"=== {item['filename']} ===\n")
                f.write(item["metadata"] + "\n")
                f.write("--- Campos clave ---\n")
                for k, v in item["core"].items():
                    f.write(f"{k}: {v}\n")
                f.write("\n")
        messagebox.showinfo("Éxito", f"Resultados exportados a {save_path}")


def show_on_map():
    """Muestra todos los puntos GPS encontrados en un mapa (folium)."""
    if not metadata_results:
        messagebox.showwarning("Atención", "No hay archivos analizados.")
        return

    gps_points = []
    for item in metadata_results:
        gps = item["core"].get("gps")
        if gps:
            gps_points.append((gps[0], gps[1], item["filename"]))

    if not gps_points:
        messagebox.showinfo("Info", "Ningún archivo tiene coordenadas GPS.")
        return

    # Crear mapa centrado en el primer punto
    m = folium.Map(location=[gps_points[0][0], gps_points[0][1]], zoom_start=12)

    for lat, lon, name in gps_points:
        folium.Marker([lat, lon], popup=name).add_to(m)

    map_path = "mapa_resultados.html"
    m.save(map_path)
    webbrowser.open("file://" + os.path.abspath(map_path))


def main():
    root = tk.Tk()
    root.title("Meta-Analisis 🕵️‍♀️")

    frame = tk.Frame(root)
    frame.pack(pady=10)

    # Botones principales
    tk.Button(frame, text="Seleccionar archivos", command=lambda: select_files(output_text)).grid(row=0, column=0, padx=5)
    tk.Button(frame, text="Coincidencias inteligentes", command=lambda: run_correlations(output_text)).grid(row=0, column=1, padx=5)
    tk.Button(frame, text="Mostrar en mapa", command=show_on_map).grid(row=0, column=2, padx=5)
    tk.Button(frame, text="Exportar resultados", command=lambda: export_results(output_text)).grid(row=0, column=3, padx=5)

    output_text = scrolledtext.ScrolledText(root, width=100, height=40)
    output_text.pack(padx=10, pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
