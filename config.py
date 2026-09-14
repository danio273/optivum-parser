# --- Main Configuration ---
LIST_URL = "https://plan.zse.bydgoszcz.pl/lista.html"
TARGET_CLASS_URL = "https://plan.zse.bydgoszcz.pl/plany/o1.html"

# --- Time Schedules (Lesson Number -> {"start": "HH:MM", "end": "HH:MM"}) ---
REGULAR_SCHEDULE = {
    0: {"start": "07:05", "end": "07:50"},
    1: {"start": "08:00", "end": "08:45"},
    2: {"start": "08:55", "end": "09:40"},
    3: {"start": "09:50", "end": "10:35"},
    4: {"start": "10:45", "end": "11:30"},
    5: {"start": "11:40", "end": "12:25"},
    6: {"start": "12:45", "end": "13:30"},
    7: {"start": "13:40", "end": "14:25"},
    8: {"start": "14:45", "end": "15:30"},
    9: {"start": "15:40", "end": "16:25"},
    10: {"start": "16:35", "end": "17:20"},
    11: {"start": "17:25", "end": "18:10"},
    12: {"start": "18:15", "end": "19:00"},
}

SHORTENED_SCHEDULE = {
    0: {"start": "07:05", "end": "07:35"},
    1: {"start": "07:40", "end": "08:10"},
    2: {"start": "08:15", "end": "08:45"},
    3: {"start": "08:50", "end": "09:20"},
    4: {"start": "09:30", "end": "10:00"},
    5: {"start": "10:05", "end": "10:35"},
    6: {"start": "10:40", "end": "11:10"},
    7: {"start": "11:15", "end": "11:45"},
    8: {"start": "11:50", "end": "12:20"},
    9: {"start": "12:30", "end": "13:00"},
    10: {"start": "13:05", "end": "13:35"},
    11: {"start": "13:40", "end": "14:10"},
    12: {"start": "14:15", "end": "14:45"},
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
    "Poniedziałek": "monday",
    "Wtorek": "tuesday",
    "Środa": "wednesday",
    "Czwartek": "thursday",
    "Piątek": "friday"
}