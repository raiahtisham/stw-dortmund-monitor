import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.message import EmailMessage
from datetime import datetime

URL = "https://www.stwdo.de/wohnen/aktuelle-wohnangebote"
STATE_FILE = "room_state.txt"

EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def read_state():
    if not os.path.exists(STATE_FILE):
        return "no_room"
    with open(STATE_FILE, "r") as f:
        return f.read().strip()

def write_state(state):
    with open(STATE_FILE, "w") as f:
        f.write(state)

def room_is_available():
    response = requests.get(URL, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Blue "NO OFFERS" info box
    no_offers_box = soup.find('div', class_='notification--info')

    return no_offers_box is None

def extract_room_details(soup):
    cards = soup.find_all('div', class_='news-list-item')
    if not cards:
        return "Room detected! Check website immediately."
    return "\n".join(card.get_text(strip=True) for card in cards)

def send_email(details):
    msg = EmailMessage()
    msg.set_content(
        f"🎉 A room is AVAILABLE at Studentenwerk Dortmund!\n\n"
        f"{details}\n\n"
        f"Link: {URL}"
    )
    msg['Subject'] = "🚨 Studentenwerk Dortmund – Room Available!"
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

if __name__ == "__main__":
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    previous_state = read_state()
    available = room_is_available()

    if available and previous_state == "no_room":
        print(f"[{now}] ROOM APPEARED → sending email")
        send_email("New room listing detected.")
        write_state("room")

    elif not available:
        print(f"[{now}] No rooms available")
        write_state("no_room")

    else:
        print(f"[{now}] Room already detected earlier → no email")
