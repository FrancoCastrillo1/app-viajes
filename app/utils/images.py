"""
Procesamiento de imágenes de perfil (avatares).
"""
import base64
import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_SIZE_BYTES     = 2 * 1024 * 1024   # 2 MB
AVATAR_DIMENSIONS  = (200, 200)
JPEG_QUALITY       = 75


def process_avatar(file_bytes: bytes, ext: str) -> tuple[str | None, str | None]:
    """
    Valida, redimensiona y comprime una imagen de avatar.

    Returns:
        (data_url, None)   si todo salió bien.
        (None, error_msg)  si hubo un error de validación o procesamiento.
    """
    if len(file_bytes) > MAX_SIZE_BYTES:
        return None, "La imagen no puede superar los 2MB."
    if ext.lower() not in ALLOWED_EXTENSIONS:
        return None, "Formato de imagen no permitido."
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img = img.convert("RGB")
        img.thumbnail(AVATAR_DIMENSIONS, Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=JPEG_QUALITY)
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}", None
    except Exception as e:
        logger.error("Error procesando avatar: %s", e, exc_info=True)
        return None, "No se pudo procesar la imagen."
