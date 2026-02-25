import os
import time
import json
import statsapi
from twilio.rest import Client

TEAM_ID = 109  # Arizona Diamondbacks
PLAYER_NAME = "Philip Abner"
STATE_FILE = 'state.json'

def send_sms(message):
    client = Client(os.environ['TWILIO_SID'], os.environ['TWILIO_AUTH'])
    client.messages.create(
        body=message,
        from_=os.environ['TWILIO_FROM'],
        to=os.environ['TWILIO_TO']
    )

def main():
    # 1. Handle Manual Test Mode from GitHub
    if os.getenv('TEST_MODE') == '1':
        send_sms("🚨 ABNER BOT: Test successful. I'm watching the mound.")
        return

    # 2. Load the list of games we've already alerted for
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    else:
        state = {"alerted_game_pks": []}

    # 3. Check if there is a game happening RIGHT NOW
    # This prevents the script from looping 24/7 and wasting your minutes
    sched = statsapi.schedule(team=TEAM_ID)
    active_game = None
    for game in sched:
        if game['status'] == "In Progress":
            active_game = game
            break

    if not active_game:
        print("No active D-backs game. Shutting down to save minutes.")
        return

    # 4. If a game IS happening, stay awake for 55 minutes and check every 60s
    game_pk = active_game['game_id']
    print(f"Game {game_pk} is live. Starting 55-minute Abner watch...")

    for _ in range(55):
        # If we already alerted for this game, we can stop the whole script
        if game_pk in state['alerted_game_pks']:
            print("Already alerted for this game. Standing down.")
            break

        # Check the current pitcher
        # 'linescore' is the most real-time data point in the MLB API
        try:
            ls = statsapi.linescore(game_pk)
            if PLAYER_NAME in ls:
                send_sms(f"🚨 ABNER ALERT: Philip Abner is in the game!")
                
                # Update state and save
                state['alerted_game_pks'].append(game_pk)
                with open(STATE_FILE, 'w') as f:
                    json.dump(state, f)
                
                print("Abner detected! SMS sent and state saved.")
                break # Exit loop after alerting
        except Exception as e:
            print(f"Error checking score: {e}")

        time.sleep(60) # Wait 60 seconds before checking again

if __name__ == "__main__":
    main()
