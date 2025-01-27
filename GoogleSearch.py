from RequestSession import createSession
from bs4 import BeautifulSoup
import time
import random
from ProcessingTools import get_cookies, getBestMatch
from concurrent.futures import ThreadPoolExecutor
from Database import saveHTML,update_url
import sys

import stealth_requests as requests
from urllib.parse import urlencode

def google_search(query, cookies=None, headers={}):
    try:
        # s = createSession(proxy=False,cookies=cookies, headers=headers)
        sleep_duration = random.uniform(5, 25)
        print("sleeping for :",sleep_duration)
        time.sleep(sleep_duration)

        encoded_query = urlencode({"q": query}) 
        url = f"https://www.google.com/search?{encoded_query}"
        response = requests.get(url, impersonate='safari',cookies=cookies)
        saveHTML(response.soup(), f"https://www.google.com/search")

        if response.status_code == 200:
            soup = response.soup()
            links = []
            
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.startswith("/url?q="):
                    actual_url = href.split("/url?q=")[1].split("&")[0]
                    links.append(actual_url)
            
            return query, links
        elif response.status_code == 429:
            print(f"BOT DETECTED {query}, Status Code : ", response.status_code)
            saveHTML(f"https://www.google.com/search",response.soup())
            return []
        else:
            print(f"Failed to fetch results on {query}, Status Code : ", response.status_code)
            saveHTML(f"https://www.google.com/search",response.soup(),encoded_query)
            return []
    except Exception as e:
            print(f"Error sending Request: {e}")

def SearchForCompaniesWebsites(df,max_workers=10):
    cookies,localStorage = get_cookies(f"https://www.google.com/search",r"Your browser Profile Path")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    }
    with ThreadPoolExecutor(max_workers=max_workers) as website_executor:
        futures = [
            website_executor.submit(google_search,row["Organisation Name"], cookies)
            for index, row in df.iterrows()
        ]

        for future in futures:
            try:
                name, urls = future.result()
                if urls:
                    best_match = getBestMatch(name,urls,threshold=0.4)
                    update_url(name,best_match)
            except Exception as e:
                print(f"Error processing website: {e}")