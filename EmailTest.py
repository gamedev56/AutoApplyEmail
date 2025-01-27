import pandas as pd
from urllib.parse import urlparse

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

from dotenv import load_dotenv
import os

load_dotenv()

saved_companies_excel_path = os.getenv("SAVED_COMPANIES_EXCEL_PATH")
saved_companies_df = pd.read_excel(saved_companies_excel_path) 
companies_with_website_email = saved_companies_df[
    saved_companies_df["Website"].notna() & saved_companies_df["Emails"].notna()
]

selected_email = select_email_by_url(companies_with_website_email)

for index, row in selected_email.iterrows():
    if index in saved_companies_df.index: 
        saved_companies_df.loc[index, :] = row 
        
print(saved_companies_df)
saved_companies_df.to_excel("companies.xlsx", index=False)