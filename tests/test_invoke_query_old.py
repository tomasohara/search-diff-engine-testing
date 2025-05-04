#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for invoke_query module"""

# Standard modules
import os
import sys
import time

# Installed modules
import pytest
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxDriver

# Mezcla modules
from mezcla import debug
from mezcla.unittest_wrapper import TestWrapper
from mezcla import glue_helpers as gh
from mezcla import system

# Add parent directory to path so we can import our module
## TODO: Find a mezcla way to do this
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import the module (assuming it's saved as invoke_query.py in the parent directory)
import invoke_query_old as THE_MODULE  

# Environment options
TEST_WEBDRIVER = system.getenv_bool(
    "TEST_WEBDRIVER", False,
    description="Run Selenium extras tests"
)
RUN_E2E_TEST = system.getenv_bool(
    "RUN_E2E_TEST", False,
    description="Run end-to-end tests"
)
RUN_PERFORMANCE_TEST = system.getenv_bool(
    "RUN_PERFORMANCE_TEST", True,
    description="Run performance tests on invoke_query"
)
USE_ALTERNATIVE_URL = system.getenv_bool(
    "USE_ALTERNATIVE_URL", False,
    description="Use alternative URL for scraping"
)

@pytest.mark.skipif(not THE_MODULE, reason="Unable to load invoke_query module")
class TestQueryInvoker(TestWrapper):
    """Test cases for QueryInvoker class"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)

    @pytest.mark.xfail
    def test_constant_function_words(self):
        """Ensure FUNCTION_WORDS set is not empty"""
        self.assertTrue(len(THE_MODULE.FUNCTION_WORDS) > 0, "FUNCTION_WORDS set is empty")
        self.assertTrue(all(isinstance(word, str) for word in THE_MODULE.FUNCTION_WORDS), "FUNCTION_WORDS set contains non-string elements")
        test_string = "the quick brown fox jumps over the lazy dog"
        self.assertTrue(any(word for word in THE_MODULE.FUNCTION_WORDS), test_string)

    @pytest.mark.xfail
    def test_constant_query_wait_time(self):
        """Ensure query wait time is set correctly"""
        self.assertTrue(THE_MODULE.SLEEP_TIME > 0, "SLEEP_TIME should be greater than 0")
        self.assertTrue(isinstance(THE_MODULE.SLEEP_TIME, int), "SLEEP_TIME should be an integer")
        self.assertTrue(THE_MODULE.PAGE_LOAD_TIMEOUT > 0, "PAGE_LOAD_TIMEOUT should be greater than 0")
        self.assertTrue(isinstance(THE_MODULE.PAGE_LOAD_TIMEOUT, int), "PAGE_LOAD_TIMEOUT should be an integer")
        self.assertTrue(THE_MODULE.QUERY_WAIT_TIMEOUT > 0, "QUERY_WAIT_TIMEOUT should be greater than 0")
        self.assertTrue(isinstance(THE_MODULE.QUERY_WAIT_TIMEOUT, int), "QUERY_WAIT_TIMEOUT should be an integer")

    @pytest.mark.xfail
    def test_function_query_invoker_initialization(self):
        """Test initialization of QueryInvoker class"""
        invoker = THE_MODULE.QueryInvoker()
        self.assertIsNotNone(invoker.driver, "WebDriver should be initialized")
        self.assertEqual(invoker.base_url, THE_MODULE.SCRAPPYCITO_URL, "Base URL should match the environment variable")
        self.assertTrue(isinstance(invoker.page_load_timeout, int), "Page load timeout should be an integer")
        self.assertTrue(isinstance(invoker.query_wait_timeout, int), "Query wait timeout should be an integer")

    @pytest.mark.xfail
    def test_function__setup_browser(self):
        """Test _setup_browser from QueryInvoker class"""
        invoker = THE_MODULE.QueryInvoker()
        ## TODO: Add test support for Chrome (selenium.common.exceptions.NoSuchDriverException: Message: Unable to obtain driver for chrome)
        # wd_chrome_headless = invoker._setup_browser(use_chrome=True, headless=False)
        # wd_chrome = invoker._setup_browser(use_chrome=True, headless=True)
        # self.assertIsInstance(wd_chrome, ChromeDriver, "Object not a Chrome Webdriver")
        # self.assertIsInstance(wd_chrome_headless, ChromeDriver, "Object not a Chrome Webdriver")

        wd_firefox_headless = invoker._setup_browser(use_chrome=False, headless=False)
        wd_firefox = invoker._setup_browser(use_chrome=False, headless=True)
        self.assertIsInstance(wd_firefox, FirefoxDriver, "Object not a Firefox Webdriver")
        self.assertIsInstance(wd_firefox_headless, FirefoxDriver, "Object not a Firefox Webdriver")

    @pytest.mark.xfail
    def test_function_create_url(self):
        """Test URL creation for function words"""
        invoker = THE_MODULE.QueryInvoker()
        test_string = "a test string"
        test_string_for_query = test_string.replace(" ", "+")
        expected_query = f"/run_search?query={test_string_for_query}&its-me=on"
        result = invoker.create_url(test_string)
        self.assertIn(test_string_for_query, result, "Test string not found in URL")
        ## TODO: Create cases using full URLs (self)
        self.assertIn(expected_query, result)

    @pytest.mark.xfail
    def test_function__get_non_function_words(self):
        """Test non-function word filtering"""
        invoker = THE_MODULE.QueryInvoker()
        test_string = "he is from the kingdom of wakanda"
        expected_result = set("he kingdom wakanda".split())
        result = invoker._get_non_function_words(test_string)
        self.assertEqual(result, expected_result, "Non-function words not filtered correctly")

    ## TODO: Complete it
    @pytest.mark.xfail
    def test_function__is_result_relevant(self):
        """Test _is_result_relevant function from InvokeQuery class"""
        invoker = THE_MODULE.QueryInvoker()
        result = {
            "title":"",
            "website":"",
            "query_terms":"",
            "snippet":""
        }
        query_terms = {}
        output = invoker._is_result_relevant(result=result, query_terms=query_terms)
        expected_result = {}
        self.assertEqual(output, expected_result)

    ## TODO: Complete it
    @pytest.mark.xfail
    def test_function_extract_query_results(self):
        """Test extract_query_results function from InvokeQuery class"""
        invoker = THE_MODULE.QueryInvoker()
        url = THE_MODULE.SCRAPPYCITO_URL if not USE_ALTERNATIVE_URL else THE_MODULE.SCRAPPYCITO_ALT
        query = "nightowl"
        output = invoker.extract_query_results(url, query)
        expected_output = ("", "", "", "")
        for _ in range(4):
            self.assertEqual(output[_], expected_output[_])
        
    @pytest.mark.xfail
    def test_function_run_query(self):
        """Test run_query fuction from InvokeQuery class"""
        invoker = THE_MODULE.QueryInvoker()
        query = ""
        result = invoker.run_query(query)
        expected_result = ""
        self.assertEqual(result, expected_result)

    @pytest.mark.xfail
    def test_function_close(self):
        """Test close function from QueryInvoker class"""
        invoker = THE_MODULE.QueryInvoker()
        pass

    @pytest.mark.xfail
    def test_function___enter__(self):
        """Test __enter__ function for QueryInvoker class"""
        pass

    @pytest.mark.xfail
    def test_function___exit__(self):
        """Test __exit__ function for QueryInvoker class"""
        pass

@pytest.mark.skipif(not RUN_E2E_TEST, reason="Selenium extras not available")
class TestQueryInvokerE2E(TestWrapper):
    """Test cases for QueryInvoker standalone mode"""
    pass

@pytest.mark.skipif(not RUN_PERFORMANCE_TEST)
class TestScriptPerformance(TestWrapper):
    """Performance test cases for invoke_query.py scripts"""
    pass
    
@pytest.mark.skipif(not TEST_WEBDRIVER, reason="Selenium extras not available")
class TestQueryInvokerWebDriver(TestWrapper):
    """Test cases for QueryInvoker WebDriver initialization"""

    def test_firefox_driver(self):
        """Test Firefox WebDriver initialization"""
        invoker = THE_MODULE.QueryInvoker(use_chrome=False)
        self.assertIsNotNone(invoker.driver, "WebDriver should be initialized")
        self.assertTrue("firefox" in invoker.driver.capabilities['browserName'].lower(), "WebDriver should be Firefox")

    def test_chrome_headless(self):
        invoker = THE_MODULE.QueryInvoker(use_chrome=True, headless=True)
        self.assertIsInstance(invoker.driver, ChromeDriver)
        self.assertTrue(hasattr(invoker.driver, 'get'))
        self.assertTrue(hasattr(invoker.driver, 'quit'))
        invoker.driver.quit()

    def test_chrome_ui(self):
        invoker = THE_MODULE.QueryInvoker(use_chrome=True, headless=False)
        self.assertIsInstance(invoker.driver, ChromeDriver)
        invoker.driver.get("https://example.com")
        time.sleep(1)
        self.assertIn("Example Domain", invoker.driver.title)
        invoker.driver.quit()

    def test_firefox_headless(self):
        invoker = THE_MODULE.QueryInvoker(use_chrome=False, headless=True)
        self.assertIsInstance(invoker.driver, FirefoxDriver)
        self.assertTrue(hasattr(invoker.driver, 'get'))
        self.assertTrue(hasattr(invoker.driver, 'quit'))
        invoker.driver.quit()

    def test_firefox_ui(self):
        invoker = THE_MODULE.QueryInvoker(use_chrome=False, headless=False)
        self.assertIsInstance(invoker.driver, FirefoxDriver)
        invoker.driver.get("https://example.com")
        time.sleep(1)
        self.assertIn("Example Domain", invoker.driver.title)
        invoker.driver.quit()

if __name__ == "__main__":
    debug.trace_current_context()
    pytest.main([__file__])