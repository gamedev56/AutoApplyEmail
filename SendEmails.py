import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import os
from Database import update_email_sent

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

load_dotenv(override=True)
email_address = os.getenv("EMAIL_ADDRESS")
email_password = os.getenv("EMAIL_PASSWORD")

# Send email function
def send_email(to_address, subject, body, attachment_path=None):
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(email_address, email_password)

        msg = MIMEMultipart()
        msg['From'] = email_address
        msg['To'] = to_address
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(attachment_path)}",
            )
            msg.attach(part)

        server.send_message(msg)
        print(f"Email sent to {to_address}")
        server.quit()

    except Exception as e:
        print(f"Failed to send email to {to_address}: {e}")

# Main function
def send_emails(data):
    cv_file = r"Your CV PATH"

    for index, row in data.iterrows():
        if pd.isna(row['Email Sent']) or row['Email Sent'] == 0:
            email = row['Selected Email']
            companyname = row['Company Name'] 
            subject = "Opportunity Inquiry"
            body = f"To whom it may concern,\n\nI hope this email finds you well. I am interested in{companyname} Please find my CV attached.\n\nBest regards,\nGeorge "
            print(f"sending email to Email : {email}, Name : {companyname}")

            #input user
            user_input = get_user_input()
            if user_input:
                update_email_sent(companyname, 1)
                # send_email(email, subject, body, cv_file)
            else:
                update_email_sent(companyname, 0)

def get_user_input():
    user_input = input("Enter 'yes' or 'no' (default is 'yes'): ").strip().lower()
    if user_input == 'n':
        return 0 
    else:
        return 1  