from Database import readFromExcelSheet
import pandas as pd
from GoogleSearch import SearchForCompaniesWebsites
from SearchEmails import SearchForEmails
from dotenv import load_dotenv
from ProcessingTools import select_email_by_url
import os
from SendEmails import send_emails

load_dotenv(override=True)
default_firefox_profile_path = os.getenv("FIREFOX_PROFILE")
saved_companies_excel_path = os.getenv("SAVED_COMPANIES_EXCEL_PATH")
uk_gov_excel_path = os.getenv("UK_GOV_EXCEL_PATH")

# SEARCH THE WEBSITES----------------------------------------

saved_companies_df = pd.read_excel(saved_companies_excel_path) # All saved Companies
uk_gov_df = readFromExcelSheet(uk_gov_excel_path, 0, 50000) # First n companies in UK sheet
saved_companies_no_website = saved_companies_df[saved_companies_df["Website"] == "No Best Match"] # All saved Companies that have no website
print(f"Nb of companies saved with no websites: {len(saved_companies_no_website)}", f"out of {len(saved_companies_df)}")

# All Companies that are in the first n companies in UK sheet that we do not have their website
filtered_uk_gov_df = uk_gov_df[ 
    ~uk_gov_df["Organisation Name"].isin(saved_companies_df["Company Name"].values) 
]

print(f"Nb of companies with no websites that we will search: {len(filtered_uk_gov_df)}", f"out of {len(uk_gov_df)}")

SearchForCompaniesWebsites(filtered_uk_gov_df,max_workers=2)

# SEARCH FOR EMAILS------------------------------------------

saved_companies_df = pd.read_excel(saved_companies_excel_path) # All saved Companies
# All saved companies that have a website but no email
companies_with_website_no_email = saved_companies_df[
    saved_companies_df["Website"].notna() & (saved_companies_df["Website"] != "No Best Match") &
    (saved_companies_df["Emails"].isna() | (saved_companies_df["Emails"] == "No Email Found"))
]

# All saved companies that have a website but no email
companies_with_website_no_email_search = saved_companies_df[
    saved_companies_df["Website"].notna() & (saved_companies_df["Website"] != "No Best Match") &
    (saved_companies_df["Emails"].isna())
]

#All companies that have a website
companies_with_website = saved_companies_df[
    saved_companies_df["Website"].notna() &
    (saved_companies_df["Website"] != "No Best Match")
]
print(f"Nb of companies saved with websites and no email: {len(companies_with_website_no_email)} ", f"out of {len(companies_with_website)}")
print(f"Nb of companies with websites and no email that we will search: {len(companies_with_website_no_email_search)}")

SearchForEmails(companies_with_website_no_email_search,max_workers=15)


# SEND THE EMAILS ------------------------------------------------------

saved_companies_df = pd.read_excel(saved_companies_excel_path) # All saved Companies
# All saved companies that have a website with email
companies_with_website_email = saved_companies_df[
    saved_companies_df["Website"].notna() &
    (saved_companies_df["Website"] != "No Best Match") & saved_companies_df["Emails"].notna() & (saved_companies_df["Emails"] != "No Email Found")
]

selected_email_df = select_email_by_url(companies_with_website_email)

for index, row in selected_email_df.iterrows():
    if index in saved_companies_df.index:  
        saved_companies_df.loc[index, :] = row 

# print(saved_companies_df)
saved_companies_df.to_excel(saved_companies_excel_path, index=False)

filtered_emails = selected_email_df[(selected_email_df['Email Sent'] == 0) | (pd.isna(selected_email_df['Email Sent']))]

chosenemails = filtered_emails.head(5)
print(chosenemails)

send_emails(chosenemails)
