from typing import Dict
from models import TimeSlot

# --- Main Configuration ---
LIST_URL = "https://plan.zse.bydgoszcz.pl/lista.html"
TARGET_CLASS_URL = "https://plan.zse.bydgoszcz.pl/plany/o1.html"

# --- Time Schedules ---
REGULAR_SCHEDULE: Dict[int, TimeSlot] = {
    0: TimeSlot(start="07:05", end="07:50"),
    1: TimeSlot(start="08:00", end="08:45"),
    2: TimeSlot(start="08:55", end="09:40"),
    3: TimeSlot(start="09:50", end="10:35"),
    4: TimeSlot(start="10:45", end="11:30"),
    5: TimeSlot(start="11:40", end="12:25"),
    6: TimeSlot(start="12:45", end="13:30"),
    7: TimeSlot(start="13:40", end="14:25"),
    8: TimeSlot(start="14:45", end="15:30"),
    9: TimeSlot(start="15:40", end="16:25"),
    10: TimeSlot(start="16:35", end="17:20"),
    11: TimeSlot(start="17:25", end="18:10"),
    12: TimeSlot(start="18:15", end="19:00"),
}

SHORTENED_SCHEDULE: Dict[int, TimeSlot] = {
    0: TimeSlot(start="07:05", end="07:35"),
    1: TimeSlot(start="07:40", end="08:10"),
    2: TimeSlot(start="08:15", end="08:45"),
    3: TimeSlot(start="08:50", end="09:20"),
    4: TimeSlot(start="09:30", end="10:00"),
    5: TimeSlot(start="10:05", end="10:35"),
    6: TimeSlot(start="10:40", end="11:10"),
    7: TimeSlot(start="11:15", end="11:45"),
    8: TimeSlot(start="11:50", end="12:20"),
    9: TimeSlot(start="12:30", end="13:00"),
    10: TimeSlot(start="13:05", end="13:35"),
    11: TimeSlot(start="13:40", end="14:10"),
    12: TimeSlot(start="14:15", end="14:45"),
}

# --- Subject Normalization ---
GENERAL_SUBJECTS = {
    "j.polski": "Język polski",
    "j.angielski": "Język angielski",
    "j.niemiecki": "Język niemiecki",
    "matematyka": "Matematyka",
    "fizyka": "Fizyka",
    "chemia": "Chemia",
    "biologia": "Biologia",
    "geografia": "Geografia",
    "historia": "Historia",
    "hist.i teraź": "Historia i teraźniejszość",
    "informatyka": "Informatyka",
    "informat.": "Informatyka",
    "religia": "Religia",
    "e_zdrowotna": "Edukacja zdrowotna",
    "wf": "Wychowanie fizyczne",
    "zaj.z wych.": "Zajęcia z wychowawcą",
    "e_obywatel.": "Edukacja obywatelska",
    "bizn.i zarz.": "Biznes i zarządzanie"
}

# --- Day Normalization ---
DAY_MAPPING = {
    "poniedziałek": "monday",
    "wtorek": "tuesday",
    "środa": "wednesday",
    "czwartek": "thursday",
    "piątek": "friday",
    "sobota": "saturday",
    "niedziela": "sunday"
}

def normalize_day(day_name: str) -> str:
    """Normalizes Polish day name to lowercase standard identifier (e.g. 'Środa' -> 'wednesday')."""
    cleaned = day_name.strip().lower()
    return DAY_MAPPING.get(cleaned, cleaned)