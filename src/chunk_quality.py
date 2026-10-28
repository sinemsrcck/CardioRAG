
import re


def is_reference_chunk(text):
    """
    Yüksek güvenle kaynakça olduğu anlaşılan
    chunk'ları tespit eder.

    True: Muhtemelen kaynakça
    False: Kaynakça olduğuna dair yeterli kanıt yok
    """
    if not text or not text.strip():
        return False

    # Satır başında referans numarası: 112. Yazar...
    reference_numbers = re.findall(
        r"(?m)^\s*(\d{1,3})\.\s+[A-ZÀ-ÖØ-Þ]",
        text
    )

    numbers = [int(n) for n in reference_numbers]

    consecutive_pairs = sum(
        b == a + 1
        for a, b in zip(numbers, numbers[1:])
    )

    # Bibliyografik işaretler
    has_author_pattern = bool(
        re.search(r"\bet\s+al\.", text, re.IGNORECASE)
    )

    has_journal_pattern = bool(
        re.search(
            r"\b(?:19|20)\d{2}\s*;\s*\d+",
            text
        )
    )

    return (
        consecutive_pairs >= 1
        and (has_author_pattern or has_journal_pattern)
    )
