"""scripts/capture_screenshots.py

Automated screenshot capture script for ZK-CaMBio Streamlit UI (Phase 8).
Connects to the local Streamlit application on http://localhost:8501 and saves
high-resolution screenshots of each page to docs/screenshots/.
"""

import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = Path("docs/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

PAGES = [
    ("Enroll", "01_enroll_page.png"),
    ("Verify (1:1)", "02_verify_page.png"),
    ("Identify (1:N)", "03_identify_page.png"),
    ("Revoke", "04_revoke_page.png"),
    ("Results", "05_results_page.png"),
    ("Threat demo", "06_threat_demo_page.png"),
]


def capture_all_pages():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 950})
        page = context.new_page()

        print("Navigating to http://localhost:8501...")
        page.goto("http://localhost:8501", timeout=30000)
        # Wait for Streamlit React app to connect and render sidebar
        page.wait_for_selector("section[data-testid='stSidebar']", timeout=30000)
        time.sleep(4)

        for page_name, out_filename in PAGES:
            print(f"Capturing: {page_name} -> {out_filename}...")
            try:
                # Find by role or text inside sidebar
                target = page.locator("section[data-testid='stSidebar']").get_by_text(page_name, exact=True)
                if target.count() > 0:
                    target.first.click()
                    time.sleep(2)
                else:
                    target = page.get_by_text(page_name, exact=True)
                    if target.count() > 0:
                        target.first.click()
                        time.sleep(2)
                    else:
                        print(f"Warning: could not find selector for {page_name}")
            except Exception as e:
                print(f"Error selecting {page_name}: {e}")

            out_path = SCREENSHOT_DIR / out_filename
            page.screenshot(path=str(out_path), full_page=True)
            print(f"Saved: {out_path} ({os.path.getsize(out_path)} bytes)")

        browser.close()
    print("All screenshots successfully captured!")


if __name__ == "__main__":
    capture_all_pages()
