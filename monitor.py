import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.message import EmailMessage

# 1. Configuration - Target URL
URL = "https://www.stwdo.de/wohnen/aktuelle-wohnangebote"

# 2. Get Secrets from GitHub Environment
# These names must match what you put in your .yml file
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')

def check_for_rooms():
    # User-Agent makes the bot look like a real browser to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # We look for the "No Vacancies" text shown in your screenshot
        page_text = soup.get_text().lower()
        
        if "currently have no vacancies" in page_text:
            print("Status: No rooms available yet.")
            return False
        else:
            # If that specific "No vacancies" text is missing, something has changed!
            print("ALERT: Possible room found!")
            return True
            
    except Exception as e:
        print(f"Error checking website: {e}")
        return False

def send_alert():
    if not EMAIL_USER or not EMAIL_PASS:
        print("Error: Email credentials not found in environment.")
        return

    msg = EmailMessage()
    msg.set_content(f"A room offer might be live at STW Dortmund! Check now: {URL}")
    msg['Subject'] = "STW Dortmund Room Alert!"
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER # Sends the email to yourself

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        print("Success: Notification email sent.")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    if check_for_rooms():
        send_alert()