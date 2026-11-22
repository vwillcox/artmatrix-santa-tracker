"""Opens the board's Santa Tracker settings page in a headless browser and presses the
"jump to a moment" buttons, to see what they would save. Every save the page tries to
send is caught here and never reaches the board, so its settings are left alone.

    uv run --with playwright cap/page_test.py
"""
from urllib.parse import parse_qs

from playwright.sync_api import sync_playwright

PAGE = "http://10.0.0.51/config?plugin=santa_tracker"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/chromium")
    page = browser.new_page()
    saved = []

    def catch(route):
        if route.request.method == "POST":
            saved.append(parse_qs(route.request.post_data or ""))
            route.fulfill(status=200, body="OK")
        else:
            route.continue_()

    page.route("**/config?plugin=santa_tracker", catch)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(PAGE, wait_until="domcontentloaded")
    page.wait_for_selector("#moments button")
    print("note:", page.inner_text("#moments-note"))
    buttons = page.query_selector_all("#moments button")
    print(len(buttons), "buttons")
    for button in buttons:
        before = len(saved)
        button.click()
        page.wait_for_timeout(400)
        sent = saved[-1] if len(saved) > before else None
        got = {k: sent[k][0] for k in ("show", "pretend", "speed")} if sent else "NOTHING SAVED"
        print(f"  {button.inner_text():42s} {got}")
    print("page errors:", errors or "none")
    browser.close()
