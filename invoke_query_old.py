#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web automation script using Selenium to query Scrappycito search engine.
"""

## TODO: Add support for additional query parameters
## TODO: Add cases for its-me=off
## TODO: Fetch image results (TBD)

# Standard Modules
import time
import urllib.parse

# Installed Modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Mezcla Modules 
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla.my_regex import my_re
from mezcla import system

# Constants
TL = debug.TL
SCRAPPYCITO_MAIN = "http://scrappycito.com:9330"
SCRAPPYCITO_ALT = "http://tomasohara.trade:9330"

# Environment Options
SCRAPPYCITO_URL = system.getenv_text(
    "SCRAPPYCITO_URL", SCRAPPYCITO_MAIN, 
    description="Scrappycito URL for scraping"
)
USE_ALTERNATIVE_URL = system.getenv_bool(
    "USE_ALTERNATIVE_URL", False, 
    description=f"Use alternative URL for scraping ({SCRAPPYCITO_ALT})"
)
USE_CHROME_DRIVER = system.getenv_bool(
    "USE_CHROME_DRIVER", False, 
    description="Use Chrome WebDriver for Selenium (uses Firefox by default)"
)
SELENIUM_HEADLESS = system.getenv_bool(
    "SELENIUM_HEADLESS", True,
    description="Run browser in headless mode"
)
SLEEP_TIME = system.getenv_int(
    "SLEEP_TIME", 5, 
    description="Sleep time in seconds after loading the page"
)

# Function Words for non-function word filtering
FUNCTION_WORDS = {
    "the", "a", "an", "and", "but", "or", "nor", "for", "yet", "so", 
    "of", "in", "to", "by", "at", "as", "with", "on", "from", "about", 
    "into", "through", "after", "before", "during", "under", "over",
    "this", "that", "these", "those", "my", "your", "his", "her", "its", 
    "our", "their", "is", "am", "are", "was", "were", "be", "been", "being"
}

# Query wait timeout (for test checks)
PAGE_LOAD_TIMEOUT = 30
QUERY_WAIT_TIMEOUT = 10

# Command line argument for query
QUERY_ARG = "query"
HEADLESS_ARG = "headless"

class QueryInvoker:
    """Class for handling search query construction, browser setup and result extraction"""
    
    def __init__(
            self, 
            use_chrome=USE_CHROME_DRIVER, 
            headless=SELENIUM_HEADLESS, 
            base_url=SCRAPPYCITO_URL if not USE_ALTERNATIVE_URL else SCRAPPYCITO_ALT
        ):
        """Initialize with browser configuration options and set up the WebDriver"""
        self.base_url = base_url
        self.driver = self._setup_browser(use_chrome, headless)
        self.page_load_timeout = PAGE_LOAD_TIMEOUT
        self.query_wait_timeout = QUERY_WAIT_TIMEOUT
        
    def _setup_browser(self, use_chrome, headless):
        """Set up and configure the browser"""
        if use_chrome:
            debug.trace(3, "Setting up Chrome browser")
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless")
                debug.trace(4, "Running Chrome in headless mode")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            return webdriver.Chrome(options=options)
        else:
            debug.trace(3, "Setting up Firefox browser")
            options = FirefoxOptions()
            options.set_preference("marionette.debugging.clicktostart", False)
            options.set_preference("marionette", True)
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.manager.showWhenStarting", False)
            if headless:
                options.add_argument("--headless")
                debug.trace(4, "Running Firefox in headless mode")
            return webdriver.Firefox(options=options)
        
    def create_url(self, query):
        """Create the search URL with the encoded query"""
        encoded_query = urllib.parse.quote_plus(query)
        return f"{self.base_url}/run_search?query={encoded_query}&its-me=on"
    
    def _get_non_function_words(self, query):
        """Extract non-function words from query"""
        words = query.lower().split()
        non_function_words = {word for word in words if word not in FUNCTION_WORDS}
        return non_function_words
    
    def _is_result_relevant(self, result, query_terms):
        """Check if a result is relevant based on query terms"""
        # Check title and snippet
        text = (result.get("title", "") + " " + result.get("snippet", "")).lower()
        
        # Check if any query term is in the text
        for term in query_terms:
            if term.lower() in text:
                return True
        return False
        
    def extract_query_results(self, url, query=None):
        """Navigate to URL and extract search results"""
        try:
            debug.trace(3, f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(SLEEP_TIME)
            
            debug.trace(3, "Looking for search results")
            search_results = self.driver.find_elements(By.CLASS_NAME, "cell-text")
            result_list = []
            
            if len(search_results) < 3:
                debug.trace(2, "Warning: Not enough search results found")
                return result_list, 0, 0.0, {"total": 0, "relevant": 0}
                
            debug.trace(4, f"Found {len(search_results)} elements")
            for i in range(0, len(search_results) - 2, 3):
                title = search_results[i].text.strip()
                website = search_results[i + 1].text.strip()
                terms = search_results[i + 2].text.strip().split("; ")
                
                if title and website:
                    result = {"title": title, "website": website, "query_terms": terms, "snippet": terms[0] if terms else ""}
                    result_list.append(result)

            # Remove last item if it exists and has incomplete data
            if result_list and len(result_list) > 0 and (len(search_results) % 3 != 0):
                result_list.pop()
                
            # Calculate relevance if query is provided
            relevant_count = 0
            if query:
                query_terms = self._get_non_function_words(query)
                for result in result_list:
                    if self._is_result_relevant(result, query_terms):
                        relevant_count += 1
            
            total_count = len(result_list)
            relevance_ratio = relevant_count / total_count if total_count > 0 else 0.0
            stats = {"total": total_count, "relevant": relevant_count}
                
            debug.trace(3, f"\nExtracted {len(result_list)} results")
            return result_list, relevant_count, relevance_ratio, stats
            
        except Exception as e:
            debug.trace_fmtd(2, "Error extracting results: {e}", e=str(e))
            return [], 0, 0.0, {"total": 0, "relevant": 0, "error": str(e)}
            
    def run_query(self, query):
        """Run a query and return results"""
        url = self.create_url(query)
        results, relevant_count, relevance_ratio, stats = self.extract_query_results(url, query)
        return results
        
    def close(self):
        """Close the browser and clean up resources"""
        debug.trace(5, "Closing browser")
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
    
    def __enter__(self):
        """Support for context manager protocol"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up when exiting context"""
        self.close()

class InvokeQueryScript(Main):
    """Selenium automation script for Scrappycito search engine"""
    
    query = None
    invoker = None
    
    def setup(self):
        """Extract argument values and set up QueryInvoker"""
        self.query = self.get_parsed_option("query")
        self.headless = self.get_parsed_option("headless")
        
        debug.trace_fmtd(TL.VERBOSE, "Query to search: {q}", q=self.query)
        debug.trace_fmtd(TL.VERBOSE, "Headless Mode: {h}", h=self.headless)
        
        # Create the QueryInvoker which handles browser setup
        self.invoker = QueryInvoker(USE_CHROME_DRIVER, self.headless)
        debug.trace(3, "QueryInvoker initialized with browser")

    def run_main_step(self):
        """Main script logic"""
        try:
            results = self.invoker.run_query(self.query)
            print(f"Found {len(results)} results for '{self.query}':")
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"  Title: {result['title']}")
                print(f"  Website: {result['website']}")
                print(f"  Query Terms: {', '.join(result['query_terms'])}")
        finally:
            self.invoker.close()

    def wrap_up(self):
        """Cleanup resources"""
        if self.invoker:
            debug.trace(4, "Cleaning up QueryInvoker resources")
            self.invoker.close()

def main():
    """Entry point"""
    app = InvokeQueryScript(
        description=__doc__,
        manual_input=True,
        skip_input=True,
        text_options=[
            (QUERY_ARG, "Search query for Scrappycito")
        ],
        boolean_options=[
            (HEADLESS_ARG, "Run selenium tests under headless mode")
        ],
        auto_help=True
    )
    app.run()


if __name__ == "__main__":
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    main()