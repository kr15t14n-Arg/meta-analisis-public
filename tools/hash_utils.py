import hashlib

def compute_hash(file_path: str, algo: str = "sha256") -> str:
    """
    Calcula el hash de un archivo.
    :param file_path: Ruta del archivo
    :param algo: Algoritmo de hash ('md5', 'sha1', 'sha256')
    :return: Hash en formato hexadecimal
    """
    if algo not in {"md5", "sha1", "sha256"}:
        raise ValueError("Algoritmo no soportado. Usa: md5, sha1 o sha256")

    h = hashlib.new(algo)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)

    return h.hexdigest()


def compute_all_hashes(file_path: str) -> dict:
    """
    Calcula varios hashes comunes (MD5, SHA1, SHA256) para un archivo.
    Devuelve un dict con los resultados.
    """
    return {
        "md5": compute_hash(file_path, "md5"),
        "sha1": compute_hash(file_path, "sha1"),
        "sha256": compute_hash(file_path, "sha256"),
    }
