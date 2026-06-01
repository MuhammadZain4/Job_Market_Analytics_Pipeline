"""Take Playwright screenshot of the pipeline dashboard HTML."""
import sys
import os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
HTML_PATH = BASE / "screenshots" / "pipeline_dashboard.html"
OUTPUT_PATH = BASE / "screenshots" / "pipeline_dashboard.png"

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    os.system(f"{sys.executable} -m pip install playwright")
    os.system(f"{sys.executable} -m playwright install chromium")
    from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 3200})
    page.goto(f"file:///{HTML_PATH.as_posix()}")
    page.wait_for_timeout(2000)
    page.screenshot(path=str(OUTPUT_PATH), full_page=True)
    browser.close()

print(f"Screenshot saved: {OUTPUT_PATH}")
