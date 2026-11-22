"""Takes a picture of the settings page's test controls. Reads only; saves nothing to the board."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/chromium")
    page = browser.new_page(viewport={"width": 900, "height": 1000})
    page.route("**/config?plugin=santa_tracker", lambda r: r.fulfill(status=200, body="OK") if r.request.method == "POST" else r.continue_())
    page.goto("http://10.0.0.51/config?plugin=santa_tracker", wait_until="domcontentloaded")
    page.wait_for_selector("#moments button")
    page.wait_for_timeout(1500)
    for i, b in enumerate(page.query_selector_all("#moments button")[:4]):
        print(i, b.inner_text(), b.bounding_box())
    page.locator("#moments").scroll_into_view_if_needed()
    page.screenshot(path="cap/page.png")
    browser.close()
