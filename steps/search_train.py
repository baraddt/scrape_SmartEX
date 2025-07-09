from playwright.sync_api import Page, Response
from datetime import date
import time


def search_train(
    page: Page, from_val: str, to_val: str, travel_date: date
) -> Response | None:
    try:
        page.select_option("#s6", from_val)
        page.select_option("#s7", to_val)

        formatted_date = travel_date.strftime("%Y%m%d")
        page.eval_on_selector("#hd_cal_val", f"(el) => el.value = '{formatted_date}'")

        page.select_option("#s-3", "06")
        page.select_option("#s-4", "00")
        page.select_option("#s-5", "1")
        page.select_option("#s10", "01")
        page.select_option("#s11", "00")

        with page.expect_navigation(
            wait_until="domcontentloaded", timeout=30000
        ) as navigation_info:
            page.click("#sb-1")

        response = navigation_info.value
        print(
            f"Form pencarian diisi: {from_val} → {to_val} untuk {travel_date.strftime('%Y-%m-%d')} pukul 06.00"
        )
        return response

    except Exception as e:
        print(f"Error selama pencarian kereta untuk {from_val} → {to_val}: {e}")
        return None
