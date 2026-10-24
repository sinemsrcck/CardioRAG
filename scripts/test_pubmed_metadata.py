
import json
import urllib.parse
import urllib.request

pmcid = "PMC10000063"

params = urllib.parse.urlencode({
    "ids": pmcid,
    "format": "json",
    "tool": "CardioRAG",
    "email": "YOUR_EMAIL@example.com"
})

url = (
    "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
    f"?{params}"
)

try:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CardioRAG/1.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)

    records = data.get("records", [])

    if not records:
        print("Makale bulunamadi.")
    else:
        article = records[0]

        print("PMCID:", article.get("pmcid"))
        print("PMID:", article.get("pmid"))
        print("DOI:", article.get("doi"))

except Exception as exc:
    print("HATA:", exc)
