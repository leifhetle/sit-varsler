import os
import json
import time
import random
import logging
import argparse
import sys
import subprocess
import requests
import tomllib
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# --- Konfigurasjon og Logging ---
load_dotenv()

def parse_arguments():
    parser = argparse.ArgumentParser(description="SIT Bolig-overvåker")
    parser.add_argument("--activate-alert", action="store_true", help="Aktiverer faktiske varsler ved funn.")
    parser.add_argument("--list-all", action="store_true", help="Viser alle boliger i terminalen.")
    parser.add_argument("--debug", action="store_true", help="Viser detaljert logg og nettleser.")
    parser.add_argument("--test-alert", action="store_true", help="Sender en test-melding til Pushover og avslutter.")
    return parser.parse_args()

ARGS = parse_arguments()

logging.basicConfig(
    level=logging.DEBUG if ARGS.debug else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_config():
    try:
        with open("config.toml", "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        logging.error("Konfigurasjonsfil 'config.toml' ikke funnet!")
        exit(1)

CONFIG = load_config()
APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN")
USER_KEY = os.getenv("PUSHOVER_USER_KEY")
LAST_SEEN_FILE = "last_seen_id.txt"

def send_phone_alarm(message: str, is_test=False):
    """Sender varsel til Pushover. is_test=True overstyrer --activate-alert sjekken."""
    if not ARGS.activate_alert and not is_test:
        logging.info(f"[SIMULERING] Varsel ville blitt sendt: {message}")
        return

    if not APP_TOKEN or not USER_KEY:
        logging.error("Pushover-nøkler mangler i .env! Sjekk PUSHOVER_APP_TOKEN og PUSHOVER_USER_KEY.")
        return

    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": APP_TOKEN, 
        "user": USER_KEY, 
        "message": message, 
        "title": "SIT Bolig-Varsler",
        "priority": 1
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            logging.info("🔔 Pushover-melding sendt suksessfullt!")
        else:
            logging.error(f"Pushover feilet (Status {response.status_code}): {response.text}")
    except Exception as e:
        logging.error(f"Kunne ikke koble til Pushover API: {e}")

# ... (resten av check_housing funksjonen forblir som før) ...
def check_housing():
    # (Samme logikk som i forrige versjon, bruker filtrering fra config.toml)
    with sync_playwright() as p:
        is_headless = not ARGS.debug
        browser = p.chromium.launch(headless=is_headless)
        context = browser.new_context()
        page = context.new_page()
        raw_boliger = []

        def handle_response(response):
            try:
                if "graphql" in response.url.lower() and response.status == 200:
                    data = response.json()
                    if isinstance(data, dict) and "data" in data:
                        inner = data["data"]
                        for key in inner.keys():
                            if key == "housings" or "housingRentalObjects" in str(inner[key]):
                                items = inner[key].get("housingRentalObjects", [])
                                if items: raw_boliger.extend(items)
            except Exception: pass

        page.on("response", handle_response)

        try:
            logging.info("Sjekker SIT via API-avlytting...")
            page.goto(CONFIG["site"]["url"], wait_until="domcontentloaded")
            filters_json = json.dumps(CONFIG["filters"])
            page.evaluate(f"sessionStorage.setItem('filters', '{filters_json}')")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            filtrerte_boliger = []
            onskede_typer = CONFIG["filters"].get("housingType", [])

            for b in raw_boliger:
                b_type = b.get("categoryName") or b.get("typeName") or ""
                if not onskede_typer or any(t.lower() in b_type.lower() for t in onskede_typer):
                    filtrerte_boliger.append(b)

            if filtrerte_boliger:
                count = len(filtrerte_boliger)
                logging.info(f"Fant {count} boliger som matcher filteret.")
                if ARGS.list_all:
                    print("\n" + "="*40)
                    for i, b in enumerate(filtrerte_boliger[:10]):
                        print(f"[{i+1}] {b.get('categoryName', 'Bolig')} - ID: {b.get('rentalObjectId')}")
                    print("="*40 + "\n")
                
                # Her lagres ID og sendes alarm (forkortet for dette eksempelet)
                send_phone_alarm(f"SIT: {count} boliger funnet!")
            else:
                logging.info("Ingen boliger funnet som matcher filteret.")
        finally:
            browser.close()

def main():
    if ARGS.test_alert:
        logging.info("🚀 Kjører test-varsel til Pushover...")
        send_phone_alarm("Hallo Elise! Test-varsel fra SIT-overvåkeren fungerer! 🏠🔔", is_test=True)
        return

    if ARGS.list_all:
        check_housing()
    else:
        while True:
            check_housing()
            delay = CONFIG["scraping"]["base_delay"] + random.randint(0, CONFIG["scraping"]["random_delay_max"])
            logging.info(f"Venter {delay} sekunder...")
            time.sleep(delay)

if __name__ == "__main__":
    main()
