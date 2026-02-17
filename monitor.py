import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.message import EmailMessage
from datetime import datetime
import pytz

# =========================
# CONFIGURATION
# =========================
URL = "https://www.stwdo.de/wohnen/aktuelle-wohnangebote"
STATE_FILE = "room_state.txt"

EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# =========================
# TIME WINDOW CHECK (CET)
# =========================
def is_within_release_window():
    """
    Release windows (CET / Germany):
    - Monday 10:00 → Tuesday 12:00
    - Wednesday 10:00 → Thursday 12:00
    """
    tz = pytz.timezone("Europe/Berlin")
    now = datetime.now(tz)

    weekday = now.weekday()  # Monday = 0
    hour = now.hour

    # Monday 10:00 → Tuesday 12:00
    if weekday == 0 and hour >= 10:
        return True
    if weekday == 1 and hour < 12:
        return True

    # Wednesday 10:00 → Thursday 12:00
    if weekday == 2 and hour >= 10:
        return True
    if weekday == 3 and hour < 12:
        return True

    return False

# =========================
# STATE HANDLING
# =========================
def read_state():
    if not os.path.exists(STATE_FILE):
        return "no_room"
    with open(STATE_FILE, "r") as f:
        return f.read().strip()

def write_state(state):
    with open(STATE_FILE, "w") as f:
        f.write(state)

# =========================
# ROOM DETECTION (ROBUST)
# =========================
def room_is_available():
    response = requests.get(URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    # Main container always exists
    form = soup.find("form", id="residential-offer-list-form")
    if not form:
        return False

    # Explicit "NO OFFERS" info box
    no_offers = form.find("div", class_="notification--info")
    if no_offers:
        return False

    # Real offers are links/cards (only appear when rooms exist)
    offers = form.find_all("a", href=True)
    return len(offers) > 0

# =========================
# EMAIL ALERT
# =========================
def send_email():
    if not EMAIL_USER or not EMAIL_PASS:
        print("Email credentials missing.")
        return

    msg = EmailMessage()
    msg["Subject"] = "🚨 Studentenwerk Dortmund – Room Available!"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_USER
    msg.set_content(
        "🎉 A room has just become available at Studentenwerk Dortmund!\n\n"
        f"Check immediately: {URL}\n\n"
        "This alert is sent only once per vacancy."
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] Job started")

    # 1️⃣ Time window check
    if not is_within_release_window():
        print("Outside release window (CET). Skipping check.")
        exit(0)

    # 2️⃣ Read previous state
    previous_state = read_state()

    # 3️⃣ Check availability
    available = room_is_available()
    print(f"Room available: {available} | Previous state: {previous_state}")

    # 4️⃣ Transition logic
    if available and previous_state == "no_room":
        print("ROOM APPEARED → Sending email")
        send_email()
        write_state("room")

    elif not available:
        print("No rooms available")
        write_state("no_room")

    else:
        print("Room already detected earlier → No email sent")
