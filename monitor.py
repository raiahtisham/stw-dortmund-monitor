import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.message import EmailMessage
from datetime import datetime

# 1. Configuration
URL = "https://www.stwdo.de/en/living-houses-application/aktuelle-wohnangebote"

# 2. Get Secrets from GitHub Environment
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')

def check_for_rooms():
    # Get current timestamp for logs
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Convert all text to lowercase for reliable matching
        page_text = soup.get_text().lower()
        
        # The specific phrase that indicates the site is EMPTY
        no_vacancy_phrase = "currently have no vacancies"
        
        if no_vacancy_phrase in page_text:
            print(f"[{now}] Status: Still no rooms. No email sent.")
            return None # No room found
        else:
            # If the phrase is GONE, we want to capture the new content
            print(f"[{now}] ALERT: Vacancy message is GONE! Room found.")
            
            # Try to find the specific content area to send in the email
            # This targets the main body text where rooms are usually listed
            offer_section = soup.find('div', class_='ce-bodytext')
            if offer_section:
                return offer_section.get_text(separator="\n", strip=True)
            return "New rooms found! Check the website immediately as I couldn't parse the specific text."
            
    except Exception as e:
        print(f"[{now}] Error checking website: {e}")
        return None

def send_alert(details):
    if not EMAIL_USER or not EMAIL_PASS:
        print("Error: Email credentials missing in GitHub Secrets.")
        return

    msg = EmailMessage()
    msg.set_content(f"URGENT: New Room Offers Detected at STW Dortmund!\n\nDetails found:\n{details}\n\nLink: {URL}")
    msg['Subject'] = "STW Dortmund Room Alert!"
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER 

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        print("Success: Notification email sent.")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    # Check for rooms and get the details
    room_details = check_for_rooms()
    
    # ONLY send the email if room_details is NOT None
    if room_details:
        send_alert(room_details)
