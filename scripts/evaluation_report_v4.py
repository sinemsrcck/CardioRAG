
import csv
import statistics
from pathlib import Path

EVALUATION_DIR = Path("data/evaluation")


def main():
    files = sorted(EVALUATION_DIR.glob("rag_evaluation_*.csv"))

    if not files:
        print("Henuz degerlendirme sonucu bulunamadi.")
        return

    latest = files[-1]

    with latest.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    successful = [row for row in rows if not row["error"]]
    failed = [row for row in rows if row["error"]]

    times = [
        float(row["response_time_seconds"])
        for row in successful
    ]

    source_counts = [
        int(row["source_count"])
        for row in successful
    ]

    rejected = [
        row for row in successful
        if row["rejected"].lower() == "true"
    ]

    print("\n========== CARDIORAG V4 TEST RAPORU ==========")
    print("Dosya:", latest)
    print("Toplam soru:", len(rows))
    print("Basarili calisan:", len(successful))
    print("Hata veren:", len(failed))
    print("Reddedilen soru:", len(rejected))

    if successful:
        print(
            "Ortalama yanit suresi:",
            round(statistics.mean(times), 2),
            "saniye"
        )
        print(
            "Medyan yanit suresi:",
            round(statistics.median(times), 2),
            "saniye"
        )
        print(
            "Ortalama kaynak sayisi:",
            round(statistics.mean(source_counts), 2)
        )

    print("\n========== SORU BAZINDA SONUCLAR ==========")

    for row in rows:
        status = (
            "HATA" if row["error"]
            else "RED" if row["rejected"].lower() == "true"
            else "YANIT"
        )

        print(
            f"Soru {row['id']}: {status} | "
            f"{row['response_time_seconds']} sn | "
            f"{row['source_count']} kaynak"
        )


if __name__ == "__main__":
    main()
