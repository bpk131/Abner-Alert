import os
import time
import requests
from datetime import datetime
from twilio.rest import Client

# ---- CONFIG ----
PITCHER_ID = 691769          # Philip Abner
TEAM_ID = 109                # Arizona Diamondbacks
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "30"))

TWILIO_SID = os.environ["TWILIO_SID"]
TWILIO_AUTH = os.environ["TWILIO_AUTH"]
TWILIO_FROM = os.environ["TWILIO_FROM"]
TWILIO_TO = os.environ["TWILIO_TO"]

client = Client(TWILIO_SID, TWILIO_AUTH)

alerted_game_pks = set()

def todays_game_pks():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={TEAM_ID}&date={today}&gameTypes=R,S,P"
    data = requests.get(url, timeout=15).json()
    dates = data.get("dates", [])
    if not dates:
        return []
    return [g.get("gamePk") for g in dates[0].get("games", []) if g.get("gamePk")]

def abner_is_pitching_now(live):
    defense = live.get("liveData", {}).get("linescore", {}).get("defense", {})
    pid = defense.get("pitcher", {}).get("id")
    return pid == PITCHER_ID

def text(game_pk):
    body = f"🚨 Philip Abner just entered the game for ARI. (gamePk: {game_pk})"
    client.messages.create(body=body, from_=TWILIO_FROM, to=TWILIO_TO)

while True:
    try:
        for game_pk in todays_game_pks():
            if game_pk in alerted_game_pks:
                continue
            live_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
            live = requests.get(live_url, timeout=15).json()
            if abner_is_pitching_now(live):
                text(game_pk)
                alerted_game_pks.add(game_pk)
    except Exception as e:
        print("Error:", e)

    time.sleep(POLL_SECONDS)
