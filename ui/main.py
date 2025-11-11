import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os

from tools.cleaner import clean_with_exiftool, clean_batch
from tools.metadata_viewer import get_metadata_text
from tools.metadata_analyzer import analyze_common_metadata as analyze_images
from tools.file_analyzer import analyze_multiple_files as analyze_docs
from tools.report_generator import export_to_pdf  # 🆕 reemplaza generate_forensic_report


class MetaAnalisisUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Meta Análisis 🕵️‍♀️")
        self.root.geometry("800x600")

        # --- Barra de botones ---
        frame = tk.Frame(root)
        frame.pack(pady=10)

        tk.Button(frame, text="Seleccionar Imagen", command=self.select_image).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(frame, text="Ver Metadatos (Imagen)", command=self.show_metadata).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(frame, text="Limpiar Imagen", command=self.clean_image).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(frame, text="Limpieza en Lote (Imágenes)", command=self.clean_images_batch).grid(row=0, column=3, padx=5, pady=5)

        tk.Button(frame, text="Analizar Imágenes", command=self.analyze_images_ui).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(frame, text="Analizar Documentos", command=self.analyze_docs_ui).grid(row=1, column=1, padx=5, pady=5)

        # Archivo actual
        self.lbl_file = tk.Label(root, text="Ningún archivo seleccionado")
        self.lbl_file.pack()

        # Área de salida
        self.txt_out = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=28)
        self.txt_out.pack(padx=10, pady=10)

        self.image_path = None

    # --------- Imagen individual ----------
    def select_image(self):
        path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imágenes", "*.jpg;*.jpeg;*.png;*.heic;*.webp;*.tiff"), ("Todos", "*.*")]
        )
        if path:
            self.image_path = path
            self.lbl_file.config(text=f"Imagen: {os.path.basename(path)}")
            self.txt_out.delete("1.0", tk.END)

    def show_metadata(self):
        if not self.image_path:
            messagebox.showwarning("Atención", "Primero seleccioná una imagen.")
            return
        try:
            meta_txt = get_metadata_text(self.image_path)
            self.txt_out.delete("1.0", tk.END)
            self.txt_out.insert(tk.END, meta_txt)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clean_image(self):
        if not self.image_path:
            messagebox.showwarning("Atención", "Primero seleccioná una imagen.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Guardar imagen limpia como...",
            defaultextension=os.path.splitext(self.image_path)[1],
            initialfile=f"{os.path.splitext(os.path.basename(self.image_path))[0]}_clean{os.path.splitext(self.image_path)[1]}"
        )
        if not save_path:
            return

        ok, msg = clean_with_exiftool(self.image_path, save_path)
        if ok:
            messagebox.showinfo("Éxito", f"Imagen limpia guardada en:\n{save_path}")
        else:
            messagebox.showerror("Error", msg)

    # --------- Lote imágenes ----------
    def clean_images_batch(self):
        paths = filedialog.askopenfilenames(
            title="Seleccionar imágenes",
            filetypes=[("Imágenes", "*.jpg;*.jpeg;*.png;*.heic;*.webp;*.tiff"), ("Todos", "*.*")]
        )
        if not paths:
            return

        output_dir = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if not output_dir:
            output_dir = "clean"

        results = clean_batch(paths, output_dir)
        self.txt_out.delete("1.0", tk.END)
        for f, ok, msg, outp in results:
            self.txt_out.insert(tk.END, f"{'✅' if ok else '❌'} {os.path.basename(f)} → {outp or msg}\n")

        messagebox.showinfo("Batch finalizado", f"Limpieza realizada. Salida: {output_dir}")

    # --------- Análisis imágenes ----------
    def analyze_images_ui(self):
        paths = filedialog.askopenfilenames(
            title="Seleccionar imágenes para análisis",
            filetypes=[("Imágenes", "*.jpg;*.jpeg;*.png;*.heic;*.webp;*.tiff"), ("Todos", "*.*")]
        )
        if not paths:
            return

        common, csv_path, rows = analyze_images(paths)
        self.txt_out.delete("1.0", tk.END)
        self.txt_out.insert(tk.END, f"📊 Coincidencias (Imágenes):\n{common}\n\nCSV: {csv_path}\n")

        if rows:
            save_report = messagebox.askyesno("Informe", "¿Generar informe PDF para imágenes?")
            if save_report:
                pdf_path = filedialog.asksaveasfilename(
                    title="Guardar informe PDF",
                    defaultextension=".pdf",
                    initialfile="images_forensic_report.pdf"
                )
                if pdf_path:
                    correlations = [(k, "-", v) for k, v in common.items()]
                    export_to_pdf(
                        metadata_list=[(row["File"], "\n".join([f"{k}: {v}" for k, v in row.items()])) for row in rows],
                        correlations=correlations,
                        output_path=pdf_path
                    )
                    messagebox.showinfo("Informe generado", f"Informe guardado en:\n{pdf_path}")

    # --------- Análisis documentos ----------
    def analyze_docs_ui(self):
        paths = filedialog.askopenfilenames(
            title="Seleccionar documentos (TXT/DOCX/PDF)",
            filetypes=[("Docs", "*.txt;*.docx;*.pdf"), ("Todos", "*.*")]
        )
        if not paths:
            return

        common, csv_path, rows = analyze_docs(paths)
        self.txt_out.delete("1.0", tk.END)
        self.txt_out.insert(tk.END, f"📊 Coincidencias (Documentos):\n{common}\n\nCSV: {csv_path}\n")

        if rows:
            save_report = messagebox.askyesno("Informe", "¿Generar informe PDF para documentos?")
            if save_report:
                pdf_path = filedialog.asksaveasfilename(
                    title="Guardar informe PDF",
                    defaultextension=".pdf",
                    initialfile="docs_forensic_report.pdf"
                )
                if pdf_path:
                    correlations = [(k, "-", v) for k, v in common.items()]
                    export_to_pdf(
                        metadata_list=[(row["File"], "\n".join([f"{k}: {v}" for k, v in row.items()])) for row in rows],
                        correlations=correlations,
                        output_path=pdf_path
                    )
                    messagebox.showinfo("Informe generado", f"Informe guardado en:\n{pdf_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MetaAnalisisUI(root)
    root.mainloop()
