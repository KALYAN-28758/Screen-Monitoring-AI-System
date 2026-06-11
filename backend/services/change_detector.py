import hashlib
from PIL import Image
import io


def compute_image_hash(image_bytes: bytes) -> str:
    """Create a hash fingerprint of an image."""
    return hashlib.md5(image_bytes).hexdigest()


def compute_change_score(image1_bytes: bytes, image2_bytes: bytes) -> float:
    """
    Compare two screenshots and return how much they differ.

    Returns:
        0.0 = identical
        1.0 = completely different
    """
    try:
        img1 = (
            Image.open(io.BytesIO(image1_bytes))
            .convert("RGB")
            .resize((320, 180))
        )

        img2 = (
            Image.open(io.BytesIO(image2_bytes))
            .convert("RGB")
            .resize((320, 180))
        )

        pixels1 = list(img1.getdata())
        pixels2 = list(img2.getdata())

        total_pixels = len(pixels1)

        if total_pixels == 0:
            return 0.0

        diff_count = 0

        for p1, p2 in zip(pixels1, pixels2):
            if any(abs(c1 - c2) > 30 for c1, c2 in zip(p1, p2)):
                diff_count += 1

        score = diff_count / total_pixels

        return round(score, 4)

    except Exception as e:
        print(f"❌ Change detection error: {e}")
        return 0.0


def is_significant_change(
    change_score: float,
    threshold: float = 0.01
) -> bool:
    """
    Returns True if the screenshot changed enough.
    """
    return change_score >= threshold