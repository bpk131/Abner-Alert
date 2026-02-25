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
    # 1. Handle Manual Test
    if os.getenv('TEST_MODE') == '1':
        send_sms("🚨 ABNER BOT: Online. Watching for Philip Abner.")
        return

    # 2. Load State
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    else:
        state = {"alerted_game_pks": []}

    # 3. Check for Active Game
    sched = statsapi.schedule(team=TEAM_ID)
    active_game_id = next((g['game_id'] for g in sched if g['status'] == "In Progress"), None)

    if not active_game_id:
        print("No active D-backs game. Shutting down.")
        return

    # 4. Long-Loop (55 minutes)
    print(f"Game {active_game_id} active. Starting 55-min watch...")
    for _ in range(55):
        # If already alerted for this game, stop
        if active_game_id in state['alerted_game_pks']:
            break

        try:
            # linescore is the fastest real-time source
            line = statsapi.linescore(active_game_id)
            if PLAYER_NAME in line:
                send_sms(f"🚨 ABNER ALERT: Philip Abner is pitching now!")
                state['alerted_game_pks'].append(active_game_id)
                with open(STATE_FILE, 'w') as f:
                    json.dump(state, f)
                break
        except Exception as e:
            print(f"API Error: {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()
