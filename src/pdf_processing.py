
import re

REFERENCE_HEADINGS = {
    "references",
    "bibliography",
    "works cited",
    "literature cited",
    "kaynakça",
    "kaynaklar",
}


def remove_references(text):
    """
    PDF metninin sonundaki kaynakça bölümünü,
    başlık açıkça tespit edilebiliyorsa kaldırır.
    """
    lines = text.splitlines()

    for i, line in enumerate(lines):
        heading = re.sub(r"\s+", " ", line).strip()
        heading = re.sub(r"^\d+[\.\)]\s*", "", heading)
        heading = heading.rstrip(":").strip().lower()

        if heading in REFERENCE_HEADINGS:
            return "\n".join(lines[:i]).strip()

    return text.strip()
