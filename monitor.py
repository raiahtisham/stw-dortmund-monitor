import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.message import EmailMessage
from datetime import datetime

# 1. Configuration
URL = "https://www.stwdo.de/wohnen/aktuelle-wohnangebote"

# 2. Get Secrets from GitHub Environment
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')

def check_for_rooms():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. VISUAL CHECK: Look for the blue 'NO OFFERS' box specifically
        # Your screenshot shows it uses class 'notification--info'
        no_offers_box = soup.find('div', class_='notification--info')
        
        # 2. LOGIC: If the blue box is MISSING, a room is likely live!
        if no_offers_box is None:
            print(f"[{now}] ALERT: The 'NO OFFERS' blue box is GONE! Room detected.")
            
            # Try to grab the room details from the new view
            room_cards = soup.find_all('div', class_='news-list-item')
            if room_cards:
                return "\n".join([card.get_text(strip=True) for card in room_cards])
            return "The vacancy alert disappeared. Check the site immediately!"
            
        else:
            # The blue box still exists, so we stay silent
            print(f"[{now}] Status: Blue 'NO OFFERS' box is still visible. No email sent.")
            return None
            
    except Exception as e:
        print(f"[{now}] Error: {e}")
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

