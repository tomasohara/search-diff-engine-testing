#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web automation script using Selenium.

Sample usage:
    python template.py --open-url https://example.com
"""

# Standard Modules
import time

# Installed Modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Mezcla Modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla.my_regex import my_re
from mezcla import system

# Constants
TL = debug.TL

# Environment Options
SELENIUM_HEADLESS = system.getenv_bool(
    "SELENIUM_HEADLESS", True,
    description="Run browser in headless mode")

# Argument Constants
URL_ARG = "open-url"

class Script(Main):
    """Selenium automation script"""

    open_url = None

    def setup(self):
        """Extract argument values and set up browser"""
        self.open_url = self.get_parsed_option(URL_ARG)
        debug.trace_fmtd(TL.VERBOSE, "Opening URL: {u}", u=self.open_url)

        options = webdriver.ChromeOptions()
        if SELENIUM_HEADLESS:
            options.add_argument("--headless")
            debug.trace(4, "Running in headless mode")

        self.browser = webdriver.Chrome(options=options)
        debug.trace(3, f"Browser initialized: {self.browser}")

    def run_main_step(self):
        """Main script logic"""
        debug.trace(3, f"Navigating to: {self.open_url}")
        self.browser.get(self.open_url)
        time.sleep(2)
        debug.trace(3, f"Page title: {self.browser.title}")
        print(f"Loaded: {self.browser.title}")

        # Example: search box logic (can customize later)
        # try:
        #     search_box = self.browser.find_element(By.NAME, "q")
        #     search_box.send_keys("Mezcla AI" + Keys.RETURN)
        #     time.sleep(2)
        # except Exception as e:
        #     debug.trace_fmtd(2, "Search failed: {e}", e=str(e))

    def wrap_up(self):
        """Cleanup resources"""
        debug.trace(5, "Closing browser")
        self.browser.quit()


def main():
    """Entry point"""
    app = Script(
        description=__doc__,
        manual_input=True,
        skip_input=True,
        text_options=[(URL_ARG, "URL to open with Selenium")],
        auto_help=True
    )
    app.run()
    debug.assertion("TODO" not in __doc__)

if __name__ == "__main__":
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    main()
