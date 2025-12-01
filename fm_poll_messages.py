#!/usr/bin/env python3
import time
import json
import hashlib
from textwrap import shorten
import requests
import subprocess

# ========= CONFIG =========

API_URL = "https://www.picnicapp.link/api/v1/fm/get-chat"

# Your Bearer token (from your message)
# WARNING: keep this secret, don't commit to GitHub
API_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJ1c2VySWQiOiJmbV91c2VyX2lkIiwiY3VycmVudEVudiI6InByb2R1Y3Rpb24iLCJpYXQiOjE2NTE0OTU1MTJ9."
    "KnjML_lje96NYUrKchPrI3QCQQ"
)

# The group you want to listen to.
# If you have multiple groups, you can call this script with different IDs
# or extend it to loop over a list.
GROUP_ID = "PUT_GROUP_ID_HERE"  # <-- replace this with actual group_id

PAGE = 1
LIMIT = 10  # how many messages per poll

POLL_INTERVAL_SEC = 5  # how often to check the API for new messages

LOG_FILE = "messages_log.txt"
TEXT_MAX_LENGTH = 300  # limit for FM/TTS message length

# FM config (adjust for your hardware)
FM_FREQUENCY_MHZ = 100.1


# ========= API HELPERS =========

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
}


def fetch_group_messages(page=PAGE, limit=LIMIT, group_id=GROUP_ID):
    """
    Call the API to get messages for a group.
    """
    params = {
        "page": page,
        "limit": limit,
        "group_id": group_id,
    }

    resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)
    resp.raise_for_status()

    try:
        data = resp.json()
    except json.JSONDecodeError:
        print("[!] Response is not valid JSON:")
        print(resp.text[:500])
        raise

    return data


def extract_messages(api_data):
    """
    Try to pull out a list of message objects from any reasonable JSON shape.
    You may want to hard-code keys after you see a real example of the response.
    """
    # For debugging, uncomment:
    # print(json.dumps(api_data, indent=2))

    # Most likely the messages are under "data" or "messages"
    if isinstance(api_data, dict):
        candidate = (
            api_data.get("data")
            or api_data.get("messages")
            or api_data.get("results")
            or api_data
        )

        if isinstance(candidate, list):
            return candidate
        elif isinstance(candidate, dict):
            # Maybe nested in "items" or similar
            for key in ("items", "results", "messages"):
                if isinstance(candidate.get(key), list):
                    return candidate[key]
            # No obvious list found
            return []
    elif isinstance(api_data, list):
        return api_data

    return []


def get_message_id(msg):
    """
    Build a unique ID for each message so we can detect 'new' ones.

    Tries typical keys first; if missing, hashes some fields together.
    """
    # Try common id fields
    for key in ("id", "_id", "message_id", "uuid"):
        if key in msg and msg[key] is not None:
            return str(msg[key])

    # Fallback: hash of content + sender + timestamp
    text = str(msg.get("text") or msg.get("message") or msg.get("body") or "")
    sender = str(msg.get("sender") or msg.get("from") or "")
    ts = str(msg.get("created_at") or msg.get("timestamp") or "")
    raw = f"{sender}|{ts}|{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def format_message_for_log_and_fm(msg):
    """
    Build a human-readable line for the log file and FM transmission.
    Adjust keys based on the real API JSON.
    """
    sender = (
        str(msg.get("sender_name"))
        or str(msg.get("sender"))
        or str(msg.get("from"))
        or "Unknown"
    )

    text = (
        str(msg.get("text"))
        or str(msg.get("message"))
        or str(msg.get("body"))
        or json.dumps(msg)
    )

    ts = str(msg.get("created_at") or msg.get("timestamp") or "")

    # Example final text
    base = f"[{ts}] {sender}: {text}"
    base = base.replace("\n", " ").strip()
    base = shorten(base, width=TEXT_MAX_LENGTH, placeholder=" ...")

    return base


# ========= FILE LOGGING =========

def append_to_log(line, log_file=LOG_FILE):
    """
    Append a single line to the log file.
    """
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ========= FM TRANSMISSION =========

def transmit_over_fm(message):
    """
    Transmit `message` over FM.
    This is a *stub* where you connect your FM transmission tool.

    Example: using `espeak` + `rpitx`:
      echo "Hello world" | espeak --stdout | sudo ./rpitx/sendiq -i - -s 48000 -f 100.1M -t iq

    You MUST adjust the path and arguments for your setup.
    """

    print(f"[*] TX: {message}")

    # --- Example command (commented out for safety) ---
    # cmd = [
    #     "sh", "-c",
    #     f"echo '{message}' | espeak --stdout | "
    #     f"sudo /path/to/rpitx/sendiq -i - -s 48000 -f {FM_FREQUENCY_MHZ}M -t iq"
    # ]
    # subprocess.run(cmd, check=True)

    # For now just print a warning so we don't transmit by accident:
    print("[!] transmit_over_fm() is in demo mode; hook in rpitx/pifm here.")


# ========= MAIN LOOP =========

def main():
    print("[*] Starting message poller...")
    print(f"[*] Group ID: {GROUP_ID}")
    print(f"[*] Poll interval: {POLL_INTERVAL_SEC} seconds")

    seen_ids = set()

    while True:
        try:
            data = fetch_group_messages()
            messages = extract_messages(data)

            # If API returns newest first, you may want to reverse them
            # so you transmit in chronological order.
            messages = list(messages)
            messages.reverse()

            new_count = 0

            for msg in messages:
                msg_id = get_message_id(msg)
                if msg_id in seen_ids:
                    continue  # already processed

                # New message!
                seen_ids.add(msg_id)

                line = format_message_for_log_and_fm(msg)
                append_to_log(line)
                transmit_over_fm(line)

                new_count += 1

            if new_count:
                print(f"[*] Processed {new_count} new message(s).")
            else:
                print("[*] No new messages.")

        except Exception as e:
            print(f"[!] Error while polling: {e}")

        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
