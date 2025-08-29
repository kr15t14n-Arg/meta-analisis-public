import subprocess
import os

def test_exiftool(image_path: str):
    """
    Prueba si ExifTool está instalado y funcionando.
    Intenta leer los metadatos de la imagen indicada.
    """
    if not os.path.exists(image_path):
        print(f"❌ No se encontró la imagen: {image_path}")
        return

    try:
        result = subprocess.run(
            ["exiftool", image_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ ExifTool funciona correctamente")
            print("=== Metadatos detectados ===")
            print(result.stdout[:500])  # muestra los primeros 500 caracteres
        else:
            print("❌ Error ejecutando ExifTool")
            print(result.stderr)
    except FileNotFoundError:
        print("❌ ExifTool no está instalado o no está en el PATH")

if __name__ == "__main__":
    # 👉 Cambia la ruta por una imagen real que tengas
    test_exiftool(test_exiftool("C:\\Users\\Cristian\\OneDrive\\Imágenes\\Leonardo-DiCaprio-Meme.png")
)
