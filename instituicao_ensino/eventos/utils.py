from PIL import Image
import os

def resize_image(path, max_size=(400, 400), quality=70):
    """
    Redimensiona uma imagem mantendo proporção, sobrescrevendo o arquivo.
    Compatível com Pillow >= 10 (usa Resampling.LANCZOS)
    """
    if not path or not os.path.exists(path):
        return

    with Image.open(path) as img:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img.save(path, quality=quality)