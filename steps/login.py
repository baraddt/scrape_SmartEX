from playwright.sync_api import sync_playwright
import time


def login_to_smartex(member_id: str, password: str):
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://shinkansen2.jr-central.co.jp/RSV_P/smart_en_index.htm")

    # input acc
    page.fill('input[name="01"]', member_id)
    page.fill('input[name="02"]', password)

    # tombol login
    page.evaluate("cfEXPY_doAction('RSWP100AIDP330')")

    try:
        # Tunggu sampai benar-benar masuk ke halaman utama (ClientService)
        page.wait_for_url("**/RSV_P/ClientService", timeout=15000)
        print("Login success")

        # Pastikan tombol Search Train muncul, lalu klik
        page.wait_for_selector("a[name='b-1']", timeout=10000)
        page.click("a[name='b-1']")
        time.sleep(2)
    except:
        print("login failed")
        browser.close()
        playwright.stop()
        return None, None, None

    return page, context, browser
