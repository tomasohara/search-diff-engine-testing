from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Set up the WebDriver (make sure you have the right driver installed for your browser)
driver = webdriver.Firefox()  # You can also use Firefox, Edge, etc.
SCRAPPYCITO_URL = "http://www.scrappycito.com:9330"
TOMASOHARA_URL = "http://www.tomasohara.trade:9330"

def create_url(query):
    # return TOMASOHARA_URL + "/run_search?query=" + query + "&its-me=on"
    return "http://www.tomasohara.trade:9330/run_search?query=nightowl&its-me=on"

def extract_query_results(driver, url):
    driver.get(url)
    time.sleep(2)
    search_results = driver.find_elements(By.CLASS_NAME, "cell-text")

    result_list = []
    for i in range(0, len(search_results) - 2, 3):
        result_list.append({
            "title": search_results[i].text,
            "website": search_results[i + 1].text,
            "query_terms": (search_results[i + 2].text).split("; ")
        })

    result_list.pop()
    return result_list

url = create_url("democracy at risk")
results = extract_query_results(driver, url)
print("Results:")
for result in results:
    print(f"Title: {result['title']}")
    print(f"Website: {result['website']}")
    print(f"Query Terms: {', '.join(result['query_terms'])}")
    print()

assert results, "No results found"
assert len(results) == 10, "Less than 10 results found"

driver.quit()
