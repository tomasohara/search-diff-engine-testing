#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced ScrappyCito Search Engine Testing Suite
A comprehensive blackbox testing framework for the ScrappyCito search engine.
"""
# Standard Modules
import time
import urllib.parse
import json
import csv
import argparse
import os
from datetime import datetime

# Installed Modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Constants
SCRAPPYCITO_MAIN = "http://scrappycito.com:9330"
SCRAPPYCITO_ALT = "http://tomasohara.trade:9330"
SLEEP_TIME = 5
PAGE_LOAD_TIMEOUT = 30
QUERY_WAIT_TIMEOUT = 10

# Function Words for non-function word filtering
FUNCTION_WORDS = {
    "the", "a", "an", "and", "but", "or", "nor", "for", "yet", "so", 
    "of", "in", "to", "by", "at", "as", "with", "on", "from", "about", 
    "into", "through", "after", "before", "during", "under", "over",
    "this", "that", "these", "those", "my", "your", "his", "her", "its", 
    "our", "their", "is", "am", "are", "was", "were", "be", "been", "being"
}

# Test cases - a variety of search queries with expected minimum result counts
TEST_QUERIES = [
    {"query": "python programming", "min_results": 3, "min_relevance": 0.7},
    {"query": "machine learning", "min_results": 3, "min_relevance": 0.7},
    {"query": "artificial intelligence", "min_results": 3, "min_relevance": 0.7},
    {"query": "natural language processing", "min_results": 2, "min_relevance": 0.6},
    {"query": "web scraping", "min_results": 2, "min_relevance": 0.7},
    {"query": "data analysis", "min_results": 3, "min_relevance": 0.6},
    {"query": "computer science", "min_results": 3, "min_relevance": 0.7},
    # Add more test cases as needed
]

class ScrappycitoTester:
    """Class for comprehensive testing of the ScrappyCito search engine"""
    
    def __init__(self, use_chrome=False, headless=True, base_url=SCRAPPYCITO_MAIN, 
                 alt_url=SCRAPPYCITO_ALT, output_dir="test_results"):
        """Initialize with browser configuration options and set up the WebDriver"""
        self.base_url = base_url
        self.alt_url = alt_url
        self.active_url = base_url
        self.use_chrome = use_chrome
        self.headless = headless
        self.driver = None
        self.output_dir = output_dir
        self.test_results = []
        self.server_status = {"main": None, "alt": None}
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def _setup_browser(self):
        """Set up and configure the browser"""
        if self.use_chrome:
            print("Setting up Chrome browser")
            options = ChromeOptions()
            if self.headless:
                options.add_argument("--headless=new")
                print("Running Chrome in headless mode")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            return webdriver.Chrome(options=options)
        else:
            print("Setting up Firefox browser")
            options = FirefoxOptions()
            options.set_preference("marionette.debugging.clicktostart", False)
            options.set_preference("marionette", True)
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.manager.showWhenStarting", False)
            if self.headless:
                options.add_argument("--headless")
                print("Running Firefox in headless mode")
            return webdriver.Firefox(options=options)
    
    def start_browser(self):
        """Initialize the browser if not already running"""
        if self.driver is None:
            self.driver = self._setup_browser()
            self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    
    def close_browser(self):
        """Close the browser if it's running"""
        if self.driver is not None:
            self.driver.quit()
            self.driver = None
    
    def check_server_status(self):
        """Check if both main and alternative servers are up"""
        self.start_browser()
        
        # Check main server
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            self.server_status["main"] = True
            print(f"✓ Main server ({self.base_url}) is UP")
        except Exception as e:
            self.server_status["main"] = False
            print(f"✗ Main server ({self.base_url}) is DOWN: {str(e)}")
        
        # Check alternative server
        try:
            self.driver.get(self.alt_url)
            time.sleep(2)
            self.server_status["alt"] = True
            print(f"✓ Alternative server ({self.alt_url}) is UP")
        except Exception as e:
            self.server_status["alt"] = False
            print(f"✗ Alternative server ({self.alt_url}) is DOWN: {str(e)}")
        
        # Determine which URL to use for testing
        if self.server_status["main"]:
            self.active_url = self.base_url
        elif self.server_status["alt"]:
            self.active_url = self.alt_url
        else:
            print("ALERT: BOTH SERVERS DOWN FOR SCRAPPYCITO")
            return False
        
        return True
    
    def create_search_url(self, query):
        """Create the search URL with the encoded query"""
        encoded_query = urllib.parse.quote_plus(query)
        return f"{self.active_url}/run_search?query={encoded_query}&its-me=on"
    
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
            print(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for results to load
            try:
                WebDriverWait(self.driver, QUERY_WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "cell-text"))
                )
            except TimeoutException:
                print("Warning: Timeout waiting for search results")
            
            time.sleep(SLEEP_TIME)
            
            print("Looking for search results")
            search_results = self.driver.find_elements(By.CLASS_NAME, "cell-text")
            result_list = []
            
            if len(search_results) < 3:
                print("Warning: Not enough search results found")
                return result_list, 0, 0.0, {"total": 0, "relevant": 0}
                
            print(f"Found {len(search_results)} elements")
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
                
            print(f"Extracted {len(result_list)} results")
            return result_list, relevant_count, relevance_ratio, stats
            
        except Exception as e:
            print(f"Error extracting results: {str(e)}")
            return [], 0, 0.0, {"total": 0, "relevant": 0, "error": str(e)}
    
    def test_search_query(self, query, min_results=3, min_relevance=0.7):
        """Test a single search query and evaluate results"""
        url = self.create_search_url(query)
        results, relevant_count, relevance_ratio, stats = self.extract_query_results(url, query)
        
        # Determine if the test passed
        has_enough_results = len(results) >= min_results
        is_relevant_enough = relevance_ratio >= min_relevance
        passed = has_enough_results and is_relevant_enough
        
        # Create test result record
        test_result = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "results_count": len(results),
            "relevant_count": relevant_count,
            "relevance_ratio": relevance_ratio,
            "min_results_required": min_results,
            "min_relevance_required": min_relevance,
            "passed": passed,
            "server": self.active_url,
            "results": results
        }
        
        self.test_results.append(test_result)
        
        # Print test results
        print(f"\nTest Results for '{query}':")
        print(f"  Results: {len(results)} (minimum: {min_results})")
        print(f"  Relevant: {relevant_count}")
        print(f"  Relevance Ratio: {relevance_ratio:.2f} (minimum: {min_relevance:.2f})")
        print(f"  {'✓ PASSED' if passed else '✗ FAILED'}")
        
        return passed
    
    def run_all_tests(self, test_queries=TEST_QUERIES):
        """Run all test queries and report results"""
        if not self.check_server_status():
            return False
        
        self.start_browser()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print("\n============================================")
        print(f"Starting ScrappyCito Tests at {timestamp}")
        print("============================================")
        
        # Track overall test results
        total_tests = len(test_queries)
        passed_tests = 0
        
        # Run each test query
        for test_case in test_queries:
            query = test_case["query"]
            min_results = test_case.get("min_results", 3)
            min_relevance = test_case.get("min_relevance", 0.7)
            
            print(f"\nTesting query: '{query}'")
            if self.test_search_query(query, min_results, min_relevance):
                passed_tests += 1
        
        # Calculate success rate
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Print summary
        print("\n============================================")
        print(f"Test Summary: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print("============================================")
        
        # Save results
        self._save_test_results(timestamp)
        
        return success_rate >= 80  # Consider the run successful if 80% of tests pass
    
    def _save_test_results(self, timestamp):
        """Save test results to files"""
        # Create a unique filename based on timestamp
        base_filename = f"scrappycito_test_{timestamp}"
        
        # Save detailed results as JSON
        json_path = os.path.join(self.output_dir, f"{base_filename}.json")
        with open(json_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Save summary results as CSV
        csv_path = os.path.join(self.output_dir, f"{base_filename}_summary.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Query', 'Results', 'Relevant', 'Relevance Ratio', 'Passed', 'Server'])
            for result in self.test_results:
                writer.writerow([
                    result['query'],
                    result['results_count'],
                    result['relevant_count'],
                    f"{result['relevance_ratio']:.2f}",
                    'Pass' if result['passed'] else 'Fail',
                    result['server']
                ])
        
        print(f"\nResults saved to:")
        print(f"  - {json_path}")
        print(f"  - {csv_path}")
    
    def run_test_suite(self):
        """Run the complete test suite including server checks"""
        try:
            self.start_browser()
            if not self.check_server_status():
                return "BOTH SERVERS DOWN FOR SCRAPPYCITO"
            
            success = self.run_all_tests()
            return "Test suite completed successfully" if success else "Test suite completed with failures"
        except Exception as e:
            return f"Test suite failed with error: {str(e)}"
        finally:
            self.close_browser()
            
    def __enter__(self):
        """Support for context manager protocol"""
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up when exiting context"""
        self.close_browser()


def main():
    """Entry point for the script"""
    parser = argparse.ArgumentParser(description="ScrappyCito Search Engine Testing Suite")
    parser.add_argument("--chrome", action="store_true", help="Use Chrome WebDriver instead of Firefox")
    parser.add_argument("--visible", action="store_true", help="Run browser in visible mode (not headless)")
    parser.add_argument("--main-url", default=SCRAPPYCITO_MAIN, help=f"Main ScrappyCito URL (default: {SCRAPPYCITO_MAIN})")
    parser.add_argument("--alt-url", default=SCRAPPYCITO_ALT, help=f"Alternative ScrappyCito URL (default: {SCRAPPYCITO_ALT})")
    parser.add_argument("--output-dir", default="test_results", help="Directory to save test results")
    parser.add_argument("--query", help="Run a single query instead of the full test suite")
    args = parser.parse_args()
    
    tester = ScrappycitoTester(
        use_chrome=args.chrome,
        headless=not args.visible,
        base_url=args.main_url,
        alt_url=args.alt_url,
        output_dir=args.output_dir
    )
    
    try:
        if args.query:
            # Run a single query test
            tester.start_browser()
            if tester.check_server_status():
                tester.test_search_query(args.query)
        else:
            # Run the full test suite
            result = tester.run_test_suite()
            print(f"\nFinal result: {result}")
    finally:
        tester.close_browser()


if __name__ == "__main__":
    main()