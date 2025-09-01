import json
import os
from datetime import datetime
import locale
import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_dagens_timeplaner(planmappe='./timeplaner'):
    # Sørg for norsk ukedag hvis ønskelig (må være installert på systemet)
    try:
        locale.setlocale(locale.LC_TIME, "nb_NO.UTF-8")
    except locale.Error:
        pass  # fallback til engelsk

    # Finn riktig ukedag som nøkkel
    today = datetime.now()
    weekday_key = today.strftime('%A').lower()  # f.eks. 'mandag'

    resultater = {}

    # Gå gjennom alle .json-filer i angitt mappe
    for filnavn in os.listdir(planmappe):
        if not filnavn.endswith('.json'):
            continue

        barn_navn = os.path.splitext(filnavn)[0]  # f.eks. "ola"
        filsti = os.path.join(planmappe, filnavn)

        try:
            with open(filsti, 'r', encoding='utf-8') as f:
                plan = json.load(f)
            dagens_fag = plan.get(weekday_key, [])
        except Exception as e:
            dagens_fag = [f"<Feil ved lesing: {e}>"]

        resultater[barn_navn] = dagens_fag

    return resultater