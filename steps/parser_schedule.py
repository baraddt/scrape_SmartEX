import json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Page


def safe_click_expand(page: Page, idx: int):
    detail_sel = f".plan_detail_{idx}"
    btn_sel = f".open_btn_detail_{idx}"

    detail_div = page.query_selector(detail_sel)
    if not detail_div:
        # plan_detail tidak ada → skip
        return

    # cek apakah hidden (display:none)
    is_hidden = detail_div.evaluate(
        "e => window.getComputedStyle(e).display === 'none'"
    )
    if is_hidden:
        # cari tombol open
        open_btn = page.query_selector(btn_sel)
        if open_btn:
            # pastikan visible
            visible = open_btn.evaluate(
                "e => window.getComputedStyle(e).display !== 'none'"
            )
            if visible:
                print(f"[INFO] Klik open_btn_detail_{idx}")
                open_btn.click()
                page.wait_for_timeout(500)  # kasih waktu DOM update


def parse_and_scrape(page: Page):
    results = []
    while True:
        # Cari semua tombol select yang currently visible
        select_buttons = page.query_selector_all(".start-button-OO")

        for i in range(len(select_buttons)):
            try:
                safe_click_expand(page, i + 1)

                page.click(f".start-button-{i+1}")
                page.wait_for_load_state("networkidle")

                # Data scraping
                date = page.query_selector("table.date td.a").text_content().strip()

                dep_time = (
                    page.query_selector("dl.dep dt")
                    .text_content()
                    .strip()
                    .replace("Dep.", "")
                    .strip()
                )
                arr_time = (
                    page.query_selector("dl.arr dt")
                    .text_content()
                    .strip()
                    .replace("Arr.", "")
                    .strip()
                )

                try:
                    dep_dt = datetime.strptime(dep_time, "%H:%M")
                    arr_dt = datetime.strptime(arr_time, "%H:%M")
                    if arr_dt < dep_dt:
                        arr_dt = arr_dt.replace(day=dep_dt.day + 1)
                    duration_td = arr_dt - dep_dt
                    duration = str(int(duration_td.total_seconds() // 60)) + " min"
                except:
                    duration = "N/A"

                departure_station = (
                    page.query_selector("table.name td.a span").text_content().strip()
                )
                arrival_station = (
                    page.query_selector("table.name td.c span").text_content().strip()
                )

                adult_raw = (
                    page.query_selector("table.count td.a").text_content().strip()
                )
                child_raw = (
                    page.query_selector("table.count td.c").text_content().strip()
                )
                adult = "".join(filter(str.isdigit, adult_raw))
                child = "".join(filter(str.isdigit, child_raw))

                train_name = page.query_selector(".koutei_disp").text_content().strip()

                common = {
                    "date": date,
                    "train_name": train_name,
                    "departure_station": departure_station,
                    "arrival_station": arrival_station,
                    "departure_time": dep_time,
                    "arrival_time": arr_time,
                    "duration": duration,
                    "adult_passengers": adult,
                    "child_passengers": child,
                }

                def extract_price(elem):
                    if not elem:
                        return "-"
                    return (
                        elem.text_content()
                        .replace("\n", "")
                        .replace("○", "")
                        .replace("Y", "")
                        .replace("▲", "")
                        # .replace("￥", "")
                        .replace(",", "")
                        .strip()
                    )

                fare_map = {
                    "rad0-2": ("smart EX", "Ordinary"),
                    "rad0-1": ("smart EX", "Green"),
                    "rad1-3": ("smart EX(Non-reserved seat)", "Ordinary"),
                    "rad1-1": ("smart EX(Non-reserved seat)", "Green"),
                }

                labels = page.query_selector_all(".new_manku .seat label")
                for label in labels:
                    label_for = label.get_attribute("for")
                    if label_for in fare_map:
                        fare_type, seat_class = fare_map[label_for]
                        span = label.query_selector("span")
                        price = extract_price(span)
                        results.append(
                            {
                                **common,
                                "fare_type": fare_type,
                                "class": seat_class,
                                "price": price,
                            }
                        )

                back_button = page.query_selector("button[onclick*='RSWP200AIDP050']")
                if back_button:
                    back_button.click()
                    page.wait_for_load_state("networkidle")

            except Exception as e:
                print(f"[ERROR] Gagal proses opsi ke-{i+1}: {e}")
                continue

        # cek tombol Later Trains
        later_btn = page.query_selector("#l-2")
        if later_btn:
            later_btn.click()
            page.wait_for_load_state("networkidle")
        else:
            print("[INFO] Tidak ada tombol Later Trains lagi. Balik ke form input.")
            back_button = page.query_selector("button[onclick*='RSWP200AIDP008']")
            if back_button:
                back_button.click()
                page.wait_for_load_state("networkidle")
            break

    with open(Path("response.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
