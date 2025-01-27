from RequestSession import createSession
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from Database import update_email,saveHTML
from ProcessingTools import extract_emails_from_html

common_paths = [
    "",
    "about-us",
    "contact-us",
    "about",
    "contact",
    "jobs",
    # "team",
    # "support",
    # "help",
    # "info",
    # "company",
    # "services",
    # "faq",
    # "get-in-touch",
]

def worker(website, emails):
    collected_emails = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    }
    s = createSession(proxy=False,headers=headers)

    with ThreadPoolExecutor(max_workers=20) as path_executor:
        futures = [
            path_executor.submit(fetch_emails_for_path, website, path, s)
            for path in common_paths
        ]

        for future in futures:
            try:
                emails = future.result()
                if emails:
                    collected_emails.extend(emails)
            except Exception as e:
                print(f"Error processing path for {website}: {e}")

    collected_emails = list(set(collected_emails))
    print(f"Collected emails for {website}: {collected_emails}")

    if collected_emails: 
        update_email(website, collected_emails)
    else:
        update_email(website, "No Email Found")


def fetch_emails_for_path(website, path, s):
    full_url = website.rstrip('/') + "/" + path
    try:
        response = s.get(full_url,timeout=10)
        if response.status_code == 200 or response.status_code == 403 :
            print("response code 200, or 403")
        else:
            print(f"Non-200 response for {full_url}. Skipping.")
            return []

        return extract_emails_from_html(response.text)
    except Exception as e:
        print(f"Error fetching URL {full_url}: {e}")
        return []

def SearchForEmails(df,max_workers=10):
    if "Company Name" not in df.columns or "Website" not in df.columns:
        raise ValueError("The Excel file must have 'Company Name' and 'Website' columns.")

    if "Emails" not in df.columns:
        df["Emails"] = ""

    with ThreadPoolExecutor(max_workers=max_workers) as website_executor:
        futures = [
            website_executor.submit(worker, row["Website"], row["Emails"])
            for index, row in df.iterrows()
        ]

        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Error processing website: {e}")
