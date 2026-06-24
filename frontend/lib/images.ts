import sharp from "sharp";

const ALLOWED_EXTENSIONS = new Set(["jpg", "jpeg", "png", "gif", "webp"]);
const MAX_SIZE_BYTES = 2 * 1024 * 1024;

export async function processAvatar(
  fileBuffer: Buffer,
  ext: string
): Promise<{ dataUrl: string } | { error: string }> {
  if (fileBuffer.length > MAX_SIZE_BYTES) {
    return { error: "La imagen no puede superar los 2MB." };
  }
  if (!ALLOWED_EXTENSIONS.has(ext.toLowerCase())) {
    return { error: "Formato de imagen no permitido." };
  }
  try {
    const processed = await sharp(fileBuffer)
      .resize(200, 200, { fit: "inside" })
      .jpeg({ quality: 75 })
      .toBuffer();
    const b64 = processed.toString("base64");
    return { dataUrl: `data:image/jpeg;base64,${b64}` };
  } catch {
    return { error: "No se pudo procesar la imagen." };
  }
}
