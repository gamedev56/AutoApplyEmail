from difflib import SequenceMatcher
from urllib.parse import urlparse

from bs4 import BeautifulSoup

import browser_cookie3
import sqlite3

from dotenv import load_dotenv
import os

import re

# Website Tools
def extract_base_url(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.split(".")[0]

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def filter_urls(urls, exclude_keywords):
    filtered_urls = []
    for url in urls:
        if not any(keyword in url for keyword in exclude_keywords):
            filtered_urls.append(url)
    return filtered_urls

def find_best_match(company_name, urls, threshold=0.5):
    company_name = company_name.replace(" ", "").lower()
    best_match = "No Best Match"
    highest_similarity = 0

    for url in urls:
        base_url = extract_base_url(url)
        sim_score = similarity(company_name, base_url)

        if sim_score > highest_similarity and sim_score >= threshold:
            highest_similarity = sim_score
            best_match = url
        
    return best_match

def getBestMatch(company_name, urls, threshold=0.5):  
    exclude_keywords = ['google', 'translate', 'support', 'accounts.google']
    filtered_urls = filter_urls(urls, exclude_keywords)

    best_match = find_best_match(company_name, filtered_urls, threshold)
    if not best_match:
        company_name = re.sub(r'\b(Ltd|Limited)\b', '', company_name, flags=re.IGNORECASE).strip()
        company_name = re.sub(r'\s+', ' ', company_name)
        best_match = find_best_match(company_name, filtered_urls, threshold)

    print(f"Best match for {company_name}: {best_match}")
    return best_match

#   HTML Extraction Tools
def decode_cfemail(cfemail):
    r = int(cfemail[:2], 16) 
    email = ''.join(chr(int(cfemail[i:i+2], 16) ^ r) for i in range(2, len(cfemail), 2))
    return email

def normalize_email(email):
    email = email.replace('[at]', '@').replace('(dot)', '.')
    email = re.sub(r'\s*@\s*', '@', email) 
    email = re.sub(r'\s*\.\s*', '.', email) 
    return email.strip()

def extract_emails_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    mailto_links = soup.find_all('a', href=lambda href: href and href.startswith('mailto:'))
    emails = []
    for link in mailto_links:
        href = link['href'].replace('mailto:', '').strip()
        clean_email = href.split('?')[0]
        normalized_email = normalize_email(clean_email)
        emails.append(normalized_email)

    cfemail_elements = soup.find_all(attrs={'data-cfemail': True})
    cfemails = [decode_cfemail(el['data-cfemail']) for el in cfemail_elements]
    
    email_regex = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'

    meaningful_sections = soup.find_all(['p', 'span', 'div', 'li', 'a', 'td'])
    text_content = " ".join(section.get_text(separator=" ") for section in meaningful_sections)

    raw_emails = re.findall(email_regex, text_content)

    cleaned_emails = []
    for email in raw_emails:
        if re.match(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email):
            cleaned_emails.append(email)

    # Combine all emails and remove duplicates
    all_emails = list(set(emails + cfemails + cleaned_emails))
    return all_emails

#   Sending Email Tools

priority = ["careers", "jobs", "contact", "info", "support", "admin", "help", "sales"]

def get_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

def select_best_email(emails, domain):
    if not emails:
        return None
    email_list = emails.split(", ")

    matching_emails = [email for email in email_list if domain in email]

    if not matching_emails:
        email_list.sort(key=email_priority)
        return email_list[0]

    matching_emails.sort(key=email_priority)
    return matching_emails[0]

def email_priority(email):
    prefix = email.split("@")[0].split(".")[0]  
    try:
        return priority.index(prefix)
    except ValueError:
        return len(priority) 
    
def select_email_by_url(dataframe):

    selected_emails = []
    for _, row in dataframe.iterrows():
        domain = get_domain(row['Website'])
        selected_email = select_best_email(row['Emails'], domain)
        selected_emails.append(selected_email)

    dataframe['Selected Email'] = selected_emails
    return dataframe

load_dotenv()
default_firefox_profile_path = os.getenv("FIREFOX_PROFILE")

def get_cookies(url,default_firefox_profile_path=default_firefox_profile_path):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        parts = domain.split('.')
        base_domain = f".{'.'.join(parts[-2:])}"

        domainlist = [domain,base_domain]
        print("DOMAIN : ",base_domain)

        domain_cookies = []
        for basedomain in domainlist:
            domain_cookie = browser_cookie3.firefox(cookie_file=default_firefox_profile_path+"/cookies.sqlite", domain_name=basedomain)
            domain_cookies.append(domain_cookie)
        
        cookies_count = 0
        for i, jar in enumerate(domain_cookies):
            if len(list(jar)) != 0:  
                cookies_count +=1


        if cookies_count>0:
            cookies = browser_cookie3.firefox(cookie_file=default_firefox_profile_path+"/cookies.sqlite")
            conn = sqlite3.connect(default_firefox_profile_path + "/webappsstore.sqlite")
            cursor = conn.cursor()
            query = "SELECT key, value FROM webappsstore2 WHERE originKey LIKE ?"
            cursor.execute(query, ('%' + domain + '%',))
            local_storage = cursor.fetchall()
            conn.close()

        return (cookies,local_storage)
    
    except Exception as e:
        print("Exeption in get_cookies, ", e)
        return([],[])