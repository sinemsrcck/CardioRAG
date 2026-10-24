
import re

REFERENCE_HEADINGS = {
    "references",
    "bibliography",
    "works cited",
    "literature cited",
    "kaynakça",
    "kaynaklar",
}

HEADING_PATTERN = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*[\.\)]?\s+)?(.+?)\s*:?\s*$"
)


def remove_references(text, min_position_ratio=0.5):
    """
    Kaynakça bölümünü yalnızca metnin son kısmında
    başlık tespit edilirse kaldırır.

    min_position_ratio=0.5:
    İlk %50'lik bölümde kaynakça kesme işlemi yapılmaz.
    """
    if not text or not text.strip():
        return ""

    lines = text.splitlines()
    total_length = len(text)
    current_position = 0

    for i, line in enumerate(lines):
        match = HEADING_PATTERN.match(line)

        if match:
            heading = re.sub(
                r"\s+", " ", match.group(1)
            ).strip().lower()

            position_ratio = current_position / max(
                total_length, 1
            )

            if (
                heading in REFERENCE_HEADINGS
                and position_ratio >= min_position_ratio
            ):
                return "\n".join(lines[:i]).strip()

        current_position += len(line) + 1

    return text.strip()
