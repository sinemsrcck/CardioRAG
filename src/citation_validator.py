
import re


def extract_citations(answer):
    """[1], [1,2], [1, 2, 3] bicimlerini ayristir."""
    numbers = []

    for match in re.finditer(r"\[([\d,\s]+)\]", answer):
        content = match.group(1)

        for part in content.split(","):
            part = part.strip()

            if part.isdigit():
                numbers.append(int(part))

    return numbers


def validate_citations(answer, sources):
    valid_numbers = {
        source["number"]
        for source in sources
    }

    cited_numbers = extract_citations(answer)
    used_numbers = sorted(set(cited_numbers))

    invalid_numbers = sorted(
        set(cited_numbers) - valid_numbers
    )

    uncited_sources = sorted(
        valid_numbers - set(cited_numbers)
    )

    paragraphs = [
        paragraph.strip()
        for paragraph in answer.split("\n\n")
        if paragraph.strip()
    ]

    paragraphs_without_citations = [
        i
        for i, paragraph in enumerate(paragraphs, start=1)
        if not extract_citations(paragraph)
    ]

    unique_documents = {
        source["filename"]
        for source in sources
    }

    return {
        "valid": len(invalid_numbers) == 0,
        "used_citations": used_numbers,
        "invalid_citations": invalid_numbers,
        "uncited_sources": uncited_sources,
        "paragraphs_without_citations": paragraphs_without_citations,
        "unique_document_count": len(unique_documents),
    }
