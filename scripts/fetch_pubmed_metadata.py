
import csv
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

INPUT = Path("data/pmcid_pmid_new.csv")
OUTPUT = Path("data/pubmed_metadata_new.csv")

URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

BATCH_SIZE = 100
WAIT_SECONDS = 0.5

FIELDS = [
    "pmid", "pmcid", "doi", "baslik", "yazarlar",
    "dergi", "yil", "abstract", "status"
]


def node_text(node):
    if node is None:
        return ""
    return " ".join("".join(node.itertext()).split())


def fetch_batch(pmids):
    payload = urllib.parse.urlencode({
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "tool": "CardioRAG"
    }).encode("utf-8")

    for attempt in range(5):
        try:
            request = urllib.request.Request(
                URL,
                data=payload,
                headers={
                    "User-Agent": "CardioRAG/1.0",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                method="POST"
            )

            with urllib.request.urlopen(request, timeout=90) as response:
                return ET.fromstring(response.read())

        except Exception as exc:
            if attempt == 4:
                raise

            delay = 2 ** (attempt + 1)
            print(f"Baglanti hatasi: {exc}; {delay} sn bekleniyor.")
            time.sleep(delay)


def parse_article(article):
    citation = article.find("MedlineCitation")
    pubmed_data = article.find("PubmedData")

    if citation is None:
        return None

    pmid = node_text(citation.find("PMID"))
    article_node = citation.find("Article")

    if article_node is None:
        return None

    baslik = node_text(article_node.find("ArticleTitle"))

    authors = []
    for author in article_node.findall("./AuthorList/Author"):
        collective = node_text(author.find("CollectiveName"))

        if collective:
            authors.append(collective)
            continue

        fore = node_text(author.find("ForeName"))
        last = node_text(author.find("LastName"))

        name = " ".join(x for x in [fore, last] if x)

        if name:
            authors.append(name)

    journal = article_node.find("Journal")
    dergi = (
        node_text(journal.find("Title"))
        if journal is not None else ""
    )

    yil = ""

    if journal is not None:
        yil = node_text(
            journal.find("./JournalIssue/PubDate/Year")
        )

        if not yil:
            medline_date = node_text(
                journal.find("./JournalIssue/PubDate/MedlineDate")
            )
            if len(medline_date) >= 4 and medline_date[:4].isdigit():
                yil = medline_date[:4]

    if not yil:
        for path in [
            "./ArticleDate/Year",
            "./Journal/JournalIssue/PubDate/Year"
        ]:
            value = node_text(article_node.find(path))
            if value:
                yil = value
                break

    abstract_parts = []

    for section in article_node.findall("./Abstract/AbstractText"):
        label = section.attrib.get("Label", "")
        content = node_text(section)

        if content:
            abstract_parts.append(
                f"{label}: {content}" if label else content
            )

    abstract = "\n".join(abstract_parts)

    doi = ""
    pmcid = ""

    if pubmed_data is not None:
        for identifier in pubmed_data.findall(
            "./ArticleIdList/ArticleId"
        ):
            id_type = identifier.attrib.get("IdType", "").lower()
            value = node_text(identifier)

            if id_type == "doi":
                doi = value
            elif id_type == "pmc":
                pmcid = value

    return {
        "pmid": pmid,
        "pmcid": pmcid,
        "doi": doi,
        "baslik": baslik,
        "yazarlar": "; ".join(authors),
        "dergi": dergi,
        "yil": yil,
        "abstract": abstract,
        "status": "matched"
    }


def save_results(results):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    temporary = OUTPUT.with_suffix(".tmp")

    with temporary.open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results.values())

    temporary.replace(OUTPUT)


def main():
    with INPUT.open(
        encoding="utf-8-sig", newline=""
    ) as f:
        source = list(csv.DictReader(f))

    source_by_pmid = {
        row["pmid"].strip(): row
        for row in source
        if row.get("pmid", "").strip()
    }

    if len(source_by_pmid) != 7307:
        raise RuntimeError(
            f"Beklenen 7307 PMID; bulunan {len(source_by_pmid)}"
        )

    results = {}

    if OUTPUT.exists():
        with OUTPUT.open(
            encoding="utf-8-sig", newline=""
        ) as f:
            for row in csv.DictReader(f):
                if row.get("pmid") in source_by_pmid:
                    results[row["pmid"]] = row

    pending = [
        pmid for pmid in source_by_pmid
        if results.get(pmid, {}).get("status") != "matched"
    ]

    print("Toplam makale:", len(source_by_pmid))
    print("Onceden tamamlanan:", len(source_by_pmid) - len(pending))
    print("Bekleyen:", len(pending))

    for start in range(0, len(pending), BATCH_SIZE):
        batch = pending[start:start + BATCH_SIZE]

        try:
            root = fetch_batch(batch)

            fetched = {}

            for article in root.findall("PubmedArticle"):
                record = parse_article(article)

                if record and record["pmid"] in batch:
                    fetched[record["pmid"]] = record

            for pmid in batch:
                expected = source_by_pmid[pmid]
                record = fetched.get(pmid)

                if record is None:
                    results[pmid] = {
                        "pmid": pmid,
                        "pmcid": expected["pmcid"],
                        "doi": expected["doi"],
                        "baslik": "",
                        "yazarlar": "",
                        "dergi": "",
                        "yil": "",
                        "abstract": "",
                        "status": "not_found"
                    }
                    continue

                # PMCID eslesmesini kontrol et.
                fetched_pmcid = record["pmcid"].upper()
                expected_pmcid = expected["pmcid"].upper()

                if fetched_pmcid and fetched_pmcid != expected_pmcid:
                    record["status"] = "pmcid_mismatch"

                if not record["pmcid"]:
                    record["pmcid"] = expected["pmcid"]

                if not record["doi"]:
                    record["doi"] = expected["doi"]

                results[pmid] = record

        except Exception as exc:
            print("BATCH HATASI:", exc)

            for pmid in batch:
                expected = source_by_pmid[pmid]

                results[pmid] = {
                    "pmid": pmid,
                    "pmcid": expected["pmcid"],
                    "doi": expected["doi"],
                    "baslik": "",
                    "yazarlar": "",
                    "dergi": "",
                    "yil": "",
                    "abstract": "",
                    "status": "error"
                }

        save_results(results)

        print(
            f"Islenen: {min(start + BATCH_SIZE, len(pending))}"
            f"/{len(pending)}"
        )

        time.sleep(WAIT_SECONDS)

    counts = {}

    for row in results.values():
        status = row["status"]
        counts[status] = counts.get(status, 0) + 1

    print("\nTamamlandi:", OUTPUT)
    print("Sonuclar:", counts)

    matched = [
        r for r in results.values()
        if r["status"] == "matched"
    ]

    print("Baslik bulunan:", sum(bool(r["baslik"]) for r in matched))
    print("Yazar bulunan:", sum(bool(r["yazarlar"]) for r in matched))
    print("Dergi bulunan:", sum(bool(r["dergi"]) for r in matched))
    print("Yil bulunan:", sum(bool(r["yil"]) for r in matched))
    print("Abstract bulunan:", sum(bool(r["abstract"]) for r in matched))


if __name__ == "__main__":
    main()
