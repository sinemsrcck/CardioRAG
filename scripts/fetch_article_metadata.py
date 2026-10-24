
import getpass
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import mysql.connector


def get_text(element, path):
    """XML alanindaki metni birlestir."""
    node = element.find(path)
    if node is None:
        return None

    value = "".join(node.itertext()).strip()
    return " ".join(value.split()) or None


def fetch_pubmed_metadata(pmids, email):
    """NCBI PubMed'den makale metadata bilgilerini al."""
    params = urllib.parse.urlencode({
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "tool": "CardioRAG",
        "email": email,
    })

    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        f"efetch.fcgi?{params}"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"CardioRAG/1.0 ({email})"
        }
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        root = ET.parse(response).getroot()

    articles = []

    for article in root.findall(".//PubmedArticle"):
        citation = article.find("MedlineCitation")
        if citation is None:
            continue

        pmid = get_text(citation, "PMID")
        if not pmid:
            continue

        title = get_text(
            citation, "Article/ArticleTitle"
        )

        journal = get_text(
            citation, "Article/Journal/Title"
        )

        year = get_text(
            citation,
            "Article/Journal/JournalIssue/PubDate/Year"
        )

        if not year:
            medline_date = get_text(
                citation,
                "Article/Journal/JournalIssue/PubDate/MedlineDate"
            )
            if medline_date:
                import re
                match = re.search(r"\b(?:19|20)\d{2}\b", medline_date)
                year = match.group(0) if match else None

        authors = []

        for author in citation.findall(
            "Article/AuthorList/Author"
        ):
            collective = get_text(author, "CollectiveName")

            if collective:
                authors.append(collective)
                continue

            last = get_text(author, "LastName")
            fore = get_text(author, "ForeName")

            name = " ".join(
                part for part in [fore, last] if part
            )

            if name:
                authors.append(name)

        abstract_parts = []

        for section in citation.findall(
            "Article/Abstract/AbstractText"
        ):
            content = " ".join(
                "".join(section.itertext()).split()
            )

            if not content:
                continue

            label = section.get("Label")
            if label:
                content = f"{label}: {content}"

            abstract_parts.append(content)

        articles.append({
            "pmid": pmid,
            "baslik": title,
            "yazarlar": "; ".join(authors) or None,
            "dergi": journal,
            "yil": int(year) if year and year.isdigit() else None,
            "abstract": "\n\n".join(abstract_parts) or None,
        })

    return articles


def main():
    email = os.environ.get("NCBI_EMAIL", "").strip()

    if not email or "@" not in email:
        raise SystemExit(
            "Once NCBI_EMAIL ortam degiskenini ayarla."
        )

    password = getpass.getpass("MySQL root sifresi: ")

    connection = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password=password,
        database="cardiorag"
    )

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT pmid
            FROM makaleler
            ORDER BY pmid
            LIMIT 50
        """)

        pmids = [row[0] for row in cursor.fetchall()]

        if not pmids:
            print("MySQL'de makale bulunamadi.")
            return

        print(f"{len(pmids)} makalenin metadata bilgileri aliniyor...")

        articles = fetch_pubmed_metadata(pmids, email)

        updated = 0

        for article in articles:
            cursor.execute(
                """
                UPDATE makaleler
                SET
                    baslik = COALESCE(%s, baslik),
                    yazarlar = COALESCE(%s, yazarlar),
                    dergi = COALESCE(%s, dergi),
                    yil = COALESCE(%s, yil),
                    abstract = COALESCE(%s, abstract)
                WHERE pmid = %s
                """,
                (
                    article["baslik"],
                    article["yazarlar"],
                    article["dergi"],
                    article["yil"],
                    article["abstract"],
                    article["pmid"],
                )
            )

            updated += cursor.rowcount

        connection.commit()

        print("PubMed'den gelen makale:", len(articles))
        print("Guncellenen MySQL kaydi:", updated)

        cursor.execute("""
            SELECT
                COUNT(*) AS toplam,
                SUM(baslik IS NOT NULL) AS baslikli,
                SUM(abstract IS NOT NULL) AS ozetli
            FROM makaleler
        """)

        total, titled, abstracted = cursor.fetchone()

        print("MySQL toplam makale:", total)
        print("Basligi olan:", titled)
        print("Ozeti olan:", abstracted)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
