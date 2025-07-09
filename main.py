import time
import csv
import os
from datetime import date, timedelta
from steps.login import login_to_smartex
from steps.search_train import search_train
from steps.parser_schedule import parse_and_scrape
from steps.saver import export_to_excel


# -------------------------------
# STATION NAMES → CODE MAPPING
# -------------------------------
STATION_CODES = {
    "tokyo": "010",
    "shinagawa": "020",
    "shin-yokohama": "030",
    "odawara": "040",
    "atami": "050",
    "mishima": "060",
    "shin-fuji": "070",
    "shizuoka": "080",
    "kakegawa": "090",
    "hamamatsu": "100",
    "toyohashi": "110",
    "mikawa-anjo": "120",
    "nagoya": "130",
    "gifu-hashima": "140",
    "maibara": "150",
    "kyoto": "160",
    "shin-osaka": "170",
    "shin-kobe": "180",
    "nishi-akashi": "190",
    "himeji": "200",
    "aioi": "210",
    "okayama": "220",
    "shin-kurashiki": "230",
    "fukuyama": "240",
    "shin-onomichi": "250",
    "mihara": "260",
    "higashi-hiroshima": "270",
    "hiroshima": "280",
    "shin-iwakuni": "290",
    "tokuyama": "300",
    "shin-yamaguchi": "310",
    "asa": "320",
    "shin-shimonoseki": "330",
    "kokura": "340",
    "hakata": "350",
    "shin-tosu": "360",
    "kurume": "370",
    "chikugo-funagoya": "380",
    "shin-omuta": "390",
    "shin-tamana": "400",
    "kumamoto": "410",
    "shin-yatsushiro": "420",
    "shin-minamata": "430",
    "izumi": "440",
    "sendai": "450",
    "kagoshima-chuo": "460",
}

# -------------------------------
# PRIORITY GROUPS
# -------------------------------
PRIORITY_1 = [
    "tokyo",
    "odawara",
    "mishima",
    "nagoya",
    "kyoto",
    "shin-osaka",
    "hakata",
]

PRIORITY_2 = [
    "shinagawa",
    "shin-yokohama",
    "shin-kobe",
    "okayama",
    "hiroshima",
    "sendai",
]

PRIORITY_3 = [
    "atami",
    "shin-fuji",
    "shizuoka",
]

PRIORITY_4 = [
    "kakegawa",
    "hamamatsu",
    "toyohashi",
    "mikawa-anjo",
    "maibara",
    "gifu-hashima",
    "nishi-akashi",
    "himeji",
    "aioi",
    "shin-kurashiki",
    "fukuyama",
    "shin-onomichi",
    "mihara",
    "higashi-hiroshima",
    "shin-iwakuni",
    "tokuyama",
    "shin-yamaguchi",
    "asa",
    "shin-shimonoseki",
    "kokura",
    "shin-tosu",
    "kurume",
    "chikugo-funagoya",
    "shin-omuta",
    "shin-tamana",
    "kumamoto",
    "shin-yatsushiro",
    "shin-minamata",
    "izumi",
    "kagoshima-chuo",
]

PRIORITY_GROUPS = {
    1: PRIORITY_1,
    2: PRIORITY_2,
    3: PRIORITY_3,
    4: PRIORITY_4,
}

ALL_STATIONS = [(name, code) for name, code in STATION_CODES.items()]

PROGRESS_FILE = "progress_done.csv"


# -------------------------------
# SCRAPE FUNCTION
# -------------------------------
def process_station_pair(
    page, from_station_code, to_station_code, travel_date, excel_filename
):
    try:
        print(f"Searching: {from_station_code} → {to_station_code}")

        response = search_train(page, from_station_code, to_station_code, travel_date)

        if response is None or response.status != 200:
            print(
                f"Error: Halaman tidak ditemukan atau error ({response.status if response else 'None'})"
            )
            return

        parse_and_scrape(page)
        export_to_excel(append=True, filename=excel_filename)

        page.wait_for_selector("#sb-1", timeout=10000)

    except Exception as e:
        print(f"Failed process for {from_station_code} → {to_station_code} | {e}")


# -------------------------------
# save progress
# -------------------------------


def load_done_pairs():
    if not os.path.exists(PROGRESS_FILE):
        return set()

    with open(PROGRESS_FILE, newline="") as f:
        reader = csv.reader(f)
        return set((row[0], row[1]) for row in reader)


def save_done_pair(from_code, to_code):
    with open(PROGRESS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([from_code, to_code])


def clear_progress_file():
    with open(PROGRESS_FILE, "w") as f:
        pass
    print("Progress file cleared. Ready for fresh scraping.")


# -------------------------------
# RUN SCRAPING BY PRIORITY
# -------------------------------
def run_scraping(priority_levels):
    priority_str = "_".join([str(p) for p in priority_levels])
    excel_filename = f"train_schedule_PRIORITY_{priority_str}.xlsx"

    # Bangun list FROM station
    selected_stations = []
    for prio in priority_levels:
        station_names = PRIORITY_GROUPS.get(prio, [])
        for s in station_names:
            code = STATION_CODES.get(s)
            if code:
                selected_stations.append((s, code))

    member_id = "1440216686"
    password = "2XeetkDr"
    page, context, browser = login_to_smartex(member_id, password)
    travel_date = date(2025, 8, 1)

    done_pairs = load_done_pairs()

    for from_station_name, from_station_code in selected_stations:

        # ================================================
        # OPTION 1 → FROM priority → TO all stations
        # ================================================
        for to_station_name, to_station_code in ALL_STATIONS:
            if from_station_code == to_station_code:
                continue

            if (from_station_code, to_station_code) in done_pairs:
                print(
                    f"skip bcs {from_station_code} -> {to_station_code} (already scraped)"
                )
                continue

            print(
                f"[INFO] {from_station_name}_{from_station_code} → {to_station_name}_{to_station_code}"
            )
            process_station_pair(
                page, from_station_code, to_station_code, travel_date, excel_filename
            )

            save_done_pair(from_station_code, to_station_code)

        # ================================================
        # OPTION 2 → FROM priority → TO priority only
        # ================================================

        # for to_station_name, to_station_code in selected_stations:
        #     if from_station_code == to_station_code:
        #         continue
        #
        #     print(
        #         f"[INFO] go {from_station_name}_{from_station_code} → {to_station_name}_{to_station_code}"
        #     )
        #     process_station_pair(
        #         page,
        #         from_station_code,
        #         to_station_code,
        #         travel_date,
        #         excel_filename
        #     )

    print("Scraping completed successfully.")
    clear_progress_file()
    browser.close()


def main():
    run_scraping([1])


if __name__ == "__main__":
    main()
