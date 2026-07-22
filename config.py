# --- Main Configuration ---
LIST_URL = "https://plan.zse.bydgoszcz.pl/lista.html"
TARGET_CLASS_URL = "https://plan.zse.bydgoszcz.pl/plany/o1.html"

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
    "zaj.z wych.": "Zajęcia z wychowawcą"
}

# --- Day Normalization ---
DAY_MAPPING = {
    "Poniedziałek": "monday",
    "Wtorek": "tuesday",
    "Środa": "wednesday",
    "Czwartek": "thursday",
    "Piątek": "friday"
}