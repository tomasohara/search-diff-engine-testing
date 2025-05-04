#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web automation script using Selenium to query Scrappycito search engine.
Enhanced for comprehensive end-to-end testing with improved stability.
"""

## TODO: Add cases for its-me=off
## TODO: Fetch image results (TBD)

# Standard Modules
import time
import urllib.parse
from datetime import datetime
import gc

# Installed Modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    SessionNotCreatedException,
    InvalidSessionIdException,
    JavascriptException
)

# Mezcla Modules 
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla.my_regex import my_re
from mezcla import system
from mezcla import file_utils as fu

# Constants
TL = debug.TL
SCRAPPYCITO_MAIN = "http://scrappycito.com:9330"
SCRAPPYCITO_ALT = "http://tomasohara.trade:9330"
DEFAULT_EXPECTED_RESULTS = 10
MIN_RELEVANCE_RATIO = 0.5
DEFAULT_OUTPUT_DIR = "./output"
MAX_RETRIES = 3  # Maximum number of retries for browser operations

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
EXPECTED_RESULTS_COUNT = system.getenv_int(
    "EXPECTED_RESULTS_COUNT", DEFAULT_EXPECTED_RESULTS,
    description="Expected number of search results"
)
EXPECTED_RELEVANCE_RATIO = system.getenv_float(
    "EXPECTED_RELEVANCE_RATIO", MIN_RELEVANCE_RATIO,
    description="Expected minimum relevance ratio"
)
BROWSER_TIMEOUT = system.getenv_int(
    "BROWSER_TIMEOUT", 30,
    description="Browser timeout in seconds"
)
OUTPUT_DIRECTORY = system.getenv_text(
    "OUTPUT_DIRECTORY", DEFAULT_OUTPUT_DIR,
    description="Directory to output test results"
)
TAKE_SCREENSHOTS = system.getenv_bool(
    "TAKE_SCREENSHOTS", False,
    description="Whether to take screenshots during the test"
)
ADD_TIMESTAMP = system.getenv_bool(
    "ADD_TIMESTAMP", False,
    description="Whether to add timestamp to output filename"
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
QUERY_WAIT_TIMEOUT = 15  
# Command line arguments
QUERY_ARG = "query"
HEADLESS_ARG = "headless"
EXPECTED_RESULTS_ARG = "expected-results"
RELEVANCE_THRESHOLD_ARG = "relevance-threshold"
OUTPUT_ARG = "output"
ADD_TIMESTAMP_ARG = "add-timestamp"
VERIFY_STATS_ARG = "verify-stats"
TAKE_SCREENSHOTS_ARG = "take-screenshots"
BROWSER_TIMEOUT_ARG = "browser-timeout"
MAX_RETRIES_ARG = "max-retries"

class QueryInvoker:
    """Class for handling search query construction, browser setup and result extraction"""
    
    def __init__(
            self, 
            use_chrome=USE_CHROME_DRIVER, 
            headless=SELENIUM_HEADLESS, 
            base_url=SCRAPPYCITO_URL if not USE_ALTERNATIVE_URL else SCRAPPYCITO_ALT,
            expected_results=EXPECTED_RESULTS_COUNT,
            relevance_threshold=EXPECTED_RELEVANCE_RATIO,
            take_screenshots=TAKE_SCREENSHOTS,
            browser_timeout=BROWSER_TIMEOUT,
            max_retries=MAX_RETRIES,
            output_dir=None
        ):
        """Initialize with browser configuration options and set up the WebDriver"""
        self.base_url = base_url
        self.use_chrome = use_chrome
        self.headless = headless
        self.browser_timeout = browser_timeout
        self.max_retries = max_retries
        self.driver = None
        self._setup_browser()  # Setup the browser
        
        self.page_load_timeout = PAGE_LOAD_TIMEOUT
        self.query_wait_timeout = QUERY_WAIT_TIMEOUT
        self.expected_results = expected_results
        self.relevance_threshold = relevance_threshold
        self.take_screenshots = take_screenshots
        self.output_dir = output_dir
        self.test_results = {
            "passed": False,
            "total_results": 0,
            "relevant_results": 0,
            "relevance_ratio": 0.0,
            "expected_results": expected_results,
            "expected_relevance": relevance_threshold,
            "response_code": None,
            "response_message": None,
            "error": None,
            "individual_results": []  # Added to store individual results
        }
        
    def _setup_browser(self):
        """Set up and configure the browser with improved error handling"""
        retry_count = 0
        last_exception = None
        
        while retry_count < self.max_retries:
            try:
                if self.use_chrome:
                    debug.trace(3, "Setting up Chrome browser")
                    options = ChromeOptions()
                    if self.headless:
                        options.add_argument("--headless=new")
                        debug.trace(4, "Running Chrome in headless mode")
                    
                    # Add stability options
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--window-size=1920,1080")
                    options.add_argument("--disable-extensions")
                    options.add_argument("--disable-browser-side-navigation")
                    options.add_argument("--disable-infobars")
                    options.add_argument("--disable-web-security")
                    options.add_argument("--allow-running-insecure-content")
                    options.add_argument("--ignore-certificate-errors")
                    
                    # Increase connection timeout
                    options.add_argument("--timeout=60000")
                    
                    # Create the driver with service
                    try:
                        service = ChromeService()
                        self.driver = webdriver.Chrome(service=service, options=options)
                    except (SessionNotCreatedException, WebDriverException) as e:
                        debug.trace(2, f"Error creating Chrome WebDriver: {str(e)}")
                        # Try without service
                        self.driver = webdriver.Chrome(options=options)
                else:
                    debug.trace(3, "Setting up Firefox browser")
                    options = FirefoxOptions()
                    
                    # These are the critical settings for Firefox stability
                    options.set_preference("marionette.debugging.clicktostart", False)
                    options.set_preference("marionette", True)
                    
                    # Add stability settings
                    options.set_preference("browser.tabs.remote.autostart", False)
                    options.set_preference("browser.tabs.remote.autostart.2", False)
                    options.set_preference("app.update.auto", False)
                    options.set_preference("app.update.enabled", False)
                    options.set_preference("dom.ipc.processCount", 1)
                    options.set_preference("browser.sessionstore.interval", 60000)
                    
                    # Increase timeouts
                    options.set_preference("marionette.timeout.script", 60000)
                    options.set_preference("marionette.timeout.pageload", 60000)
                    options.set_preference("dom.max_script_run_time", 0)
                    
                    # Disable features that might cause instability
                    options.set_preference("browser.download.folderList", 2)
                    options.set_preference("browser.download.manager.showWhenStarting", False)
                    options.set_preference("browser.cache.disk.enable", False)
                    options.set_preference("browser.cache.memory.enable", False)
                    options.set_preference("browser.cache.offline.enable", False)
                    options.set_preference("network.http.use-cache", False)
                    
                    if self.headless:
                        options.add_argument("--headless")
                        debug.trace(4, "Running Firefox in headless mode")
                    
                    try:
                        service = FirefoxService()
                        self.driver = webdriver.Firefox(service=service, options=options)
                    except (SessionNotCreatedException, WebDriverException) as e:
                        debug.trace(2, f"Error creating Firefox WebDriver: {str(e)}")
                        # Try without service
                        self.driver = webdriver.Firefox(options=options)
                
                # Configure timeouts
                if self.driver:
                    self.driver.set_page_load_timeout(self.browser_timeout)
                    self.driver.set_script_timeout(self.browser_timeout)
                    debug.trace(3, f"Browser setup successful with {self.browser_timeout}s timeout")
                    return
            
            except (WebDriverException, SessionNotCreatedException, ConnectionError, OSError) as e:
                debug.trace_fmtd(2, "Browser setup attempt {retry} failed: {e}", 
                                retry=retry_count+1, e=str(e))
                last_exception = e
                retry_count += 1
                
                # Close any existing driver before retrying
                if hasattr(self, 'driver') and self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    finally:
                        self.driver = None
                
                # Wait before retry
                time.sleep(2)
        
        # If we've exhausted retries, try fallback to Chrome if Firefox failed
        if not self.use_chrome and not self.driver:
            debug.trace(2, "Firefox setup failed after retries, falling back to Chrome")
            self.use_chrome = True
            try:
                chrome_options = ChromeOptions()
                if self.headless:
                    chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.set_page_load_timeout(self.browser_timeout)
                self.driver.set_script_timeout(self.browser_timeout)
                debug.trace(3, "Successfully fell back to Chrome")
                return
            except (WebDriverException, SessionNotCreatedException, ConnectionError, OSError) as e:
                last_exception = e
                debug.trace_fmtd(1, "Chrome fallback also failed: {e}", e=str(e))
                
        # If all attempts failed, raise the last exception
        if last_exception:
            raise WebDriverException(f"Failed to initialize browser after {self.max_retries} attempts: {str(last_exception)}")
        
    def _ensure_browser_active(self):
        """Ensure that the browser is active and restart if necessary"""
        if not self.driver:
            debug.trace(2, "Browser not initialized, creating new instance")
            self._setup_browser()
            return
            
        try:
            # Simple test to check if browser is responsive
            if self.driver.current_url is not None:  # This gives the statement an effect
                debug.trace(5, f"Browser is active at {self.driver.current_url}")
            else:
                debug.trace(5, "Browser is active but current_url is None")
        except (InvalidSessionIdException, WebDriverException) as e:
            debug.trace_fmtd(2, "Browser session invalid, restarting: {e}", e=str(e))
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
                self._setup_browser()
                
    def create_url(self, query, its_me="on", additional_params:dict=None):
        """Create the search URL with the encoded query and optional parameters"""
        encoded_query = urllib.parse.quote_plus(query)
        url = f"{self.base_url}/run_search?query={encoded_query}&its-me={its_me}"
        
        # Add additional parameters if provided
        if additional_params and isinstance(additional_params, dict):
            for key, value in additional_params.items():
                url += f"&{key}={value}"
                
        return url
    
    def _get_non_function_words(self, query):
        """Extract non-function words from query"""
        words = my_re.findall(r'\w+', query.lower())
        non_function_words = {word for word in words if word not in FUNCTION_WORDS}
        return non_function_words
    
    def _is_result_relevant(self, result, query_terms):
        """Check if a result is relevant based on query terms"""
        # Check title and snippet
        text = (result.get("title", "") + " " + result.get("snippet", "")).lower()
        
        # Check if any query term is in the text
        found_terms = []
        for term in query_terms:
            if term.lower() in text:
                debug.trace(4, f"Found relevant term '{term}' in result")
                found_terms.append(term)
                
        if found_terms:
            result["relevant"] = True
            result["relevant_terms"] = found_terms
            return True
        
        debug.trace(4, f"No relevant terms found in result: {text[:50]}...")
        result["relevant"] = False
        result["relevant_terms"] = []
        return False
    
    def wait_for_results(self, timeout=None):
        """Wait for search results to appear on the page"""
        if timeout is None:
            timeout = self.query_wait_timeout
            
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "cell-text"))
            )
            debug.trace(3, "Results found on the page")
            return True
        except TimeoutException:
            debug.trace(2, f"Timeout waiting for results after {timeout} seconds")
            return False
    
    def get_stats_from_page(self):
        """Extract search statistics from the page if available"""
        try:
            stats_elem = self.driver.find_element(By.ID, "search-stats")
            if stats_elem:
                stats_text = stats_elem.text
                debug.trace(3, f"Found stats: {stats_text}")
                
                # Try to extract numbers from stats text
                numbers = my_re.findall(r'\d+', stats_text)
                if numbers:
                    debug.trace(4, f"Extracted numbers from stats: {numbers}")
                    return {
                        "total_results": int(numbers[0]) if len(numbers) > 0 else 0,
                        "query_time": float(numbers[1]) if len(numbers) > 1 else 0.0
                    }
        except NoSuchElementException:
            debug.trace(3, "No search stats element found")
        except (ValueError, IndexError) as e:  # Handle int/float conversion & index errors
            debug.trace_fmtd(2, f"Error parsing stats numbers: {e}")
        except Exception as e:  # Only if truly unexpected (should ideally never happen)
            debug.trace_fmtd(1, f"Unexpected error in get_stats_from_page(): {e}")
            raise  # Re-raise if it's critical
            
        return None
    
    def get_response_info(self):
        """Get response code and message from the current page"""
        try:
            # Try to get response code via JavaScript
            response_code = self.driver.execute_script(
                "return window.performance.getEntries()[0].responseStatus || null;"
            )

            # Fallback to title-based detection if JS method fails
            if response_code is None:
                title = self.driver.title.lower()
                code_mapping = {
                    '404': 404,
                    'not found': 404,
                    '403': 403,
                    'forbidden': 403,
                    '500': 500,
                    'server error': 500
                }
                response_code = next(
                    (code for text, code in code_mapping.items() if text in title),
                    200  # Default to 200 if no matches found
                )

            # Define response messages
            response_messages = {
                200: "OK",
                201: "Created",
                204: "No Content",
                400: "Bad Request",
                401: "Unauthorized",
                403: "Forbidden",
                404: "Not Found",
                500: "Internal Server Error",
                503: "Service Unavailable"
            }
            
            message = response_messages.get(response_code, "Unknown")
            debug.trace(3, f"Response: {response_code} {message}")
            return response_code, message

        except (JavascriptException, WebDriverException) as e:
            debug.trace_fmtd(2, f"Error getting response info: {str(e)}")
            return None, "Error retrieving response info"
    
    def load_page_with_retry(self, url, max_retries=None):
        """Load a page with retry logic for connection issues"""
        if max_retries is None:
            max_retries = self.max_retries
            
        retry_count = 0
        last_exception = None
        
        while retry_count < max_retries:
            try:
                # Ensure the browser is active
                self._ensure_browser_active()
                
                debug.trace(3, f"Attempt {retry_count+1}: Loading {url}")
                self.driver.get(url)
                
                # Wait a bit for the page to stabilize
                time.sleep(1)
                
                # Check if the page loaded successfully
                if self.driver.current_url:
                    debug.trace(3, f"Successfully loaded: {self.driver.current_url}")
                    return True
                    
            except WebDriverException as e:
                last_exception = e
                debug.trace_fmtd(2, "Error loading page (attempt {retry}): {e}", 
                                retry=retry_count+1, e=str(e))
                
                # Try to recover the browser session
                try:
                    self.driver.quit()
                except:
                    pass
                finally:
                    self.driver = None
                    self._setup_browser()
                    
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(retry_count * 2)  # Progressive backoff
                
        # If we've exhausted all retries
        if last_exception:
            debug.trace_fmtd(1, "Failed to load page after {max_retry} attempts: {e}", 
                            max_retry=max_retries, e=str(last_exception))
            return False
        
        return False
        
    def extract_query_results(self, url, query=None):
        """Navigate to URL and extract search results"""
        response_code = None
        response_message = None
        error_response = {
            "total": 0,
            "relevant": 0,
            "error": "",
            "response_code": response_code,
            "response_message": response_message
        }

        try:
            debug.trace(3, f"Navigating to: {url}")
            
            # Use retry logic for page loading
            if not self.load_page_with_retry(url):
                debug.trace(2, "Failed to load page after retries")
                error_response.update({
                    "error": "Failed to load page after retries",
                    "response_message": "Connection failed"
                })
                return [], 0, 0.0, error_response
            
            # Get response information
            response_code, response_message = self.get_response_info()
            error_response.update({
                "response_code": response_code,
                "response_message": response_message
            })
            
            # Store response info in test results
            self.test_results.update({
                "response_code": response_code,
                "response_message": response_message
            })
            
            # Wait for results with explicit wait instead of sleep
            if not self.wait_for_results():
                debug.trace(2, "No results found within timeout period")
                error_response["error"] = "Timeout waiting for results"
                return [], 0, 0.0, error_response
            
            # Add a small sleep to ensure page is fully loaded
            time.sleep(2)
            
            debug.trace(3, "Looking for search results")
            search_results = self.driver.find_elements(By.CLASS_NAME, "cell-text")
            result_list = []
            
            if len(search_results) < 3:
                debug.trace(2, "Warning: Not enough search results found")
                error_response["error"] = "Not enough search results"
                return result_list, 0, 0.0, error_response
                
            debug.trace(4, f"Found {len(search_results)} elements")
            for i in range(0, len(search_results) - 2, 3):
                try:
                    title = search_results[i].text.strip()
                    website = search_results[i + 1].text.strip()
                    terms = search_results[i + 2].text.strip().split("; ")
                    
                    if title and website:
                        result_list.append({
                            "title": title,
                            "website": website,
                            "query_terms": terms,
                            "snippet": terms[0] if terms else ""
                        })
                except IndexError as e:
                    debug.trace_fmtd(2, "Error processing result at index {i}: {e}", i=i, e=str(e))
                    continue

            # Remove last item if it's incomplete
            if result_list and (len(search_results) % 3 != 0):
                result_list.pop()

            # Relevance calculation
            relevant_count = 0
            if query:
                query_terms = self._get_non_function_words(query)
                debug.trace(3, f"Non-function query terms: {query_terms}")
                relevant_count = sum(1 for result in result_list if self._is_result_relevant(result, query_terms))
            
            total_count = len(result_list)
            relevance_ratio = relevant_count / total_count if total_count > 0 else 0.0
            
            # Combine stats
            stats = {
                "total": total_count,
                "relevant": relevant_count,
                "relevance_ratio": relevance_ratio,
                "response_code": response_code,
                "response_message": response_message
            }
            
            # Add page stats if available
            if (page_stats := self.get_stats_from_page()):
                stats.update(page_stats)
                
            debug.trace(3, f"Extracted {len(result_list)} results, {relevant_count} relevant ({relevance_ratio:.2f})")
            
            # Update test results
            self.test_results.update({
                "total_results": total_count,
                "relevant_results": relevant_count,
                "relevance_ratio": relevance_ratio,
                "individual_results": result_list,
                "passed": (
                    total_count >= self.expected_results and 
                    relevance_ratio >= self.relevance_threshold
                )
            })
            
            return result_list, relevant_count, relevance_ratio, stats
            
        except WebDriverException as e:
            debug.trace_fmtd(2, "Error extracting results: {e}", e=str(e))
            error_response["error"] = str(e)
            self.test_results["error"] = str(e)
            return [], 0, 0.0, error_response      
    
    def run_query(self, query, its_me="on", additional_params=None):
        """Run a query and return results"""
        url = self.create_url(query, its_me, additional_params)
        results, relevant_count, relevance_ratio, stats = self.extract_query_results(url, query)
        return results, stats
    
    def verify_results(self, results, stats):
        """Verify that results meet expectations"""
        total_count = stats.get("total", 0)
        relevance_ratio = stats.get("relevance_ratio", 0.0)
        
        results_check = total_count >= self.expected_results
        relevance_check = relevance_ratio >= self.relevance_threshold
        
        if results_check and relevance_check:
            debug.trace(2, "✓ Test PASSED - Results meet criteria")
            return True

        reasons = []
        if not results_check:
            reasons.append(f"Expected at least {self.expected_results} results, got {total_count}")
        if not relevance_check:
            reasons.append(f"Expected relevance ratio of {self.relevance_threshold}, got {relevance_ratio:.2f}")
        
        debug.trace(2, f"✗ Test FAILED - {'; '.join(reasons)}")
        return False
    
    def save_test_results(self, filename):
        """Save test results to a JSON file."""
        try:
            # Create directory if it doesn't exist
            output_dir = gh.dir_path(filename)
            if output_dir and not system.file_exists(output_dir):
                system.create_directory(output_dir)
        
            fu.write_json(filename, self.test_results)
            debug.trace(3, f"Test results saved to {filename}")
            return True
            
        except (IOError, OSError, PermissionError) as e:
            debug.trace_fmtd(2, f"Filesystem error saving test results: {str(e)}")
            return False
            
        except (TypeError, ValueError) as e:
            debug.trace_fmtd(2, f"Data serialization error: {str(e)}")
            return False
            
        except Exception as e:
            debug.trace_fmtd(1, f"Unexpected error saving results: {str(e)}")
            raise
        
    def close(self):
        """Close the browser and clean up resources with improved error handling.
        
        Handles browser window closing and WebDriver cleanup separately with specific
        exception handling for each operation.
        """
        debug.trace(5, "Closing browser")
        try:
            if not hasattr(self, 'driver') or not self.driver:
                debug.trace(4, "No active WebDriver instance to close")
                return

            # Close browser window
            try:
                self.driver.close()
                debug.trace(4, "Browser window closed")
            except (InvalidSessionIdException, WebDriverException) as e:
                debug.trace_fmtd(3, "Error closing browser window: {e}", e=str(e))
            
            # Quit WebDriver
            try:
                self.driver.quit()
                debug.trace(4, "WebDriver quit successfully")
            except (InvalidSessionIdException, WebDriverException) as e:
                debug.trace_fmtd(3, "Error quitting WebDriver: {e}", e=str(e))
            finally:
                self.driver = None
                
        except Exception as e:  # pragma: no cover
            debug.trace_fmtd(2, "Unexpected error during browser cleanup: {e}", e=str(e))
            raise
        finally:
            gc.collect()
    
    def take_screenshot(self, filename):
        """Take screenshot of current page if enabled, returning success status."""
        if not self.take_screenshots:
            debug.trace(4, "Screenshots disabled")
            return False
            
        try:
            if (screenshot_dir := gh.dir_path(filename)) and not system.file_exists(screenshot_dir):
                system.create_directory(screenshot_dir)
            
            self._ensure_browser_active()
            self.driver.save_screenshot(filename)
            debug.trace(3, f"Screenshot saved to {filename}")
            return True
            
        except (WebDriverException, OSError) as e:
            debug.trace_fmtd(2, f"Screenshot failed: {str(e)}")
            return False
    
    def __enter__(self):
        """Support for context manager protocol"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up when exiting context"""
        self.close()

class InvokeQueryScript(Main):
    """Selenium automation script for Scrappycito search engine"""
    
    def __init__(self, *args, **kwargs):
        """Initialize all instance attributes"""
        super().__init__(*args, **kwargs)
        self.query = None
        self.invoker = None
        self.expected_results = EXPECTED_RESULTS_COUNT
        self.relevance_threshold = EXPECTED_RELEVANCE_RATIO
        self.browser_timeout = BROWSER_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.output_file = None
        self.output_enabled = False
        self.verify_stats = True
        self.take_screenshots = TAKE_SCREENSHOTS
        self.add_timestamp = ADD_TIMESTAMP
        self.output_dir = None
        self.timestamp = None
        self.headless = False
        self.screenshots_dir = None

    def setup(self):
        """Extract argument values and set up QueryInvoker"""
        self.query = self.get_parsed_option(QUERY_ARG)
        self.headless = self.get_parsed_option(HEADLESS_ARG)
        self.expected_results = int(self.get_parsed_option(EXPECTED_RESULTS_ARG, str(EXPECTED_RESULTS_COUNT)))
        self.relevance_threshold = float(self.get_parsed_option(RELEVANCE_THRESHOLD_ARG, str(EXPECTED_RELEVANCE_RATIO)))
        self.output_file = self.get_parsed_option(OUTPUT_ARG)
        self.output_enabled = bool(self.output_file)
        self.verify_stats = self.get_parsed_option(VERIFY_STATS_ARG, True)
        self.take_screenshots = self.get_parsed_option(TAKE_SCREENSHOTS_ARG, TAKE_SCREENSHOTS)
        self.add_timestamp = self.get_parsed_option(ADD_TIMESTAMP_ARG, ADD_TIMESTAMP)        
        # Generate timestamp for this run
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Set up output directory structure if output is enabled
        if self.output_enabled:
            base_dir = DEFAULT_OUTPUT_DIR
            self.output_dir = system.form_path(base_dir, f"invoke_query_{self.timestamp}")
            if not system.file_exists(self.output_dir):
                system.create_directory(self.output_dir)
            
            # Create screenshots directory if enabled
            if self.take_screenshots:
                self.screenshots_dir = system.form_path(self.output_dir, "screenshots")
                if not system.file_exists(self.screenshots_dir):
                    system.create_directory(self.screenshots_dir)
        
        debug.trace_fmtd(TL.VERBOSE, "Query to search: {q}", q=self.query)
        debug.trace_fmtd(TL.VERBOSE, "Headless Mode: {h}", h=self.headless)
        debug.trace_fmtd(TL.VERBOSE, "Expected Results: {er}", er=self.expected_results)
        debug.trace_fmtd(TL.VERBOSE, "Relevance Threshold: {rt}", rt=self.relevance_threshold)
        debug.trace_fmtd(TL.VERBOSE, "Output Enabled: {oe}", oe=self.output_enabled)
        debug.trace_fmtd(TL.VERBOSE, "Output Directory: {od}", od=self.output_dir if self.output_enabled else "N/A")
        debug.trace_fmtd(TL.VERBOSE, "Take Screenshots: {ts}", ts=self.take_screenshots)
        
        # Create the QueryInvoker which handles browser setup
        self.invoker = QueryInvoker(
            USE_CHROME_DRIVER, 
            self.headless, 
            expected_results=self.expected_results,
            relevance_threshold=self.relevance_threshold,
            take_screenshots=self.take_screenshots,
            output_dir=self.output_dir
        )
        debug.trace(3, "QueryInvoker initialized with browser")

    def run_main_step(self):
        """Main script logic"""
        try:
            if self.take_screenshots and self.output_enabled:
                initial_screenshot = system.form_path(self.screenshots_dir, "initial_state.png")
                self.invoker.take_screenshot(initial_screenshot)
            
            results, stats = self.invoker.run_query(self.query)
            
            if self.take_screenshots and self.output_enabled:
                results_screenshot = system.form_path(self.screenshots_dir, "search_results.png")
                self.invoker.take_screenshot(results_screenshot)
                
            # Verify results if requested
            if self.verify_stats:
                self.invoker.verify_results(results, stats)
            
            if self.output_enabled:
                json_filename = system.form_path(self.output_dir, f"results_{self.timestamp}.json")
                self.invoker.save_test_results(json_filename)

            self._print_individual_results(results)
            self._print_results_summary(stats)
            
            if self.output_enabled:
                print(f"\nResults saved to directory: {self.output_dir}")
                
        finally:
            self.invoker.close()

    def _print_individual_results(self, results):
        """Print individual search results with relevance information"""
        print(f"\n{'='*60}")
        print(f"INDIVIDUAL SEARCH RESULTS FOR QUERY: '{self.query}'")
        print(f"{'='*60}")
        
        if not results:
            print("No results found.")
            return
            
        for i, result in enumerate(results, 1):
            relevance_status = "✓ RELEVANT" if result.get("relevant", False) else "✗ NOT RELEVANT"
            relevance_marker = "✓" if result.get("relevant", False) else "✗"
            
            print(f"\nResult {i}: {relevance_marker}")
            print(f"  Title: {result['title']}")
            print(f"  Website: {result['website']}")
            print(f"  Query Terms: {', '.join(result['query_terms'])}")
            
            if result.get("relevant", False) and result.get("relevant_terms"):
                print(f"  Relevant Terms Found: {', '.join(result['relevant_terms'])}")
            
            print(f"  Relevance: {relevance_status}")
            print("-" * 40)

    def _print_results_summary(self, stats):
        """Print a summary of the search results"""
        print(f"\n{'='*60}")
        print(f"SUMMARY FOR SEARCH QUERY: '{self.query}'")
        print(f"{'='*60}")
        print(f"Total Results: {stats.get('total', 0)}")
        print(f"Relevant Results: {stats.get('relevant', 0)}")
        print(f"Relevance Ratio: {stats.get('relevance_ratio', 0.0):.2f}")
        print(f"Response Code: {stats.get('response_code', 'Unknown')}")
        print(f"Response Message: {stats.get('response_message', 'Unknown')}")
        if 'query_time' in stats:
            print(f"Query Time: {stats['query_time']:.2f} seconds")
        print(f"{'='*60}")
        
        if self.invoker.test_results['passed']:
            print("✓ TEST PASSED - Results meet expectations")
        else:
            print("✗ TEST FAILED - Results do not meet expectations")
            if self.invoker.test_results.get('error'):
                print(f"Error: {self.invoker.test_results['error']}")
        print(f"{'='*60}")

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
            (QUERY_ARG, "Search query for Scrappycito"),
            (OUTPUT_ARG, "Enable output and save results to structured directory"),
            (RELEVANCE_THRESHOLD_ARG, f"Minimum ratio of relevant results (default: {EXPECTED_RELEVANCE_RATIO})"),
            (EXPECTED_RESULTS_ARG, f"Expected number of search results (default: {EXPECTED_RESULTS_COUNT})")
        ],
        boolean_options=[
            (HEADLESS_ARG, "Run selenium tests under headless mode"),
            (VERIFY_STATS_ARG, "Verify that results meet expectations"),
            (TAKE_SCREENSHOTS_ARG, f"Take screenshots during testing (default: {TAKE_SCREENSHOTS})")
        ],
        auto_help=True
    )
    app.run()


if __name__ == "__main__":
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    main()