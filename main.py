import os
import time
import json
import statsapi
from twilio.rest import Client

# Target: Philip Abner (LHP, Arizona Diamondbacks)
TEAM_ID = 109 
PLAYER_NAME = "Philip Abner"
STATE_FILE = 'state.json'

def send_sms(message):
    """Sends SMS to multiple numbers from the TWILIO_TO secret."""
    try:
        client = Client(os.environ['TWILIO_SID'], os.environ['TWILIO_AUTH'])
        
        # Splits "+1814..., +1704..." into a list of individual numbers
        to_numbers = os.environ['TWILIO_TO'].split(',')
        
        for number in to_numbers:
            clean_number = number.strip()
            if clean_number:
                client.messages.create(
                    body=message,
                    from_=os.environ['TWILIO_FROM'],
                    to=clean_number
                )
                print(f"✅ Message sent to {clean_number}")
    except Exception as e:
        print(f"❌ Twilio Error: {e}")

def main():
    # 1. Handle Manual Test Mode from GitHub Actions
    if os.getenv('TEST_MODE') == '1':
        print("Running in TEST_MODE...")
        test_msg = os.getenv('TEST_MESSAGE', "🚨 TEST: Abner alert bot is working.")
        send_sms(test_msg)
        return

    # 2. Load State (to prevent double-texting in the same game)
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    else:
        state = {"alerted_game_pks": []}

    # 3. Check if a game is currently live
    print("Checking MLB schedule for active D-backs games...")
    sched = statsapi.schedule(team=TEAM_ID)
    active_game = next((g for g in sched if g['status'] == "In Progress"), None)

    if not active_game:
        print("No active Diamondbacks game found. Shutting down to save minutes.")
        return

    game_pk = active_game['game_id']
    # Updated text to reflect the new 65-minute window
    print(f"Game {game_pk} is live. Starting 65-minute internal watch...")

    # 4. THE LONG LOOP (Checks every 60s for 65 minutes)
    for i in range(65):  # Changed to 65 for the overlap!
        # This print acts as a "heartbeat" so you can watch it live in GitHub Actions
        print(f"Minute {i+1}/65: Checking boxscore for {PLAYER_NAME}...")

        # Stop if we already sent a text for this specific game
        if game_pk in state['alerted_game_pks']:
            print(f"Already alerted for Game {game_pk}. Ending loop.")
            break

        try:
            # Linescore is the fastest way to see the current pitcher
            ls = statsapi.linescore(game_pk)
            if PLAYER_NAME in ls:
                send_sms(f"🚨 ABNER ALERT: Philip Abner is now pitching!")
                
                # Update state and save immediately
                state['alerted_game_pks'].append(game_pk)
                with open(STATE_FILE, 'w') as f:
                    json.dump(state, f)
                
                print(f"Abner detected. Alert sent for game {game_pk}.")
                break 
        except Exception as e:
            print(f"Error checking game data: {e}")

        time.sleep(60) 

if __name__ == "__main__":
    main()
