# Optivum Parser API

API do pobierania i normalizowania planu lekcji oraz zastępstw z systemu Plan lekcji Optivum firmy VULCAN.

Projekt powstał głównie po to, aby udostępnić **czyste i ujednolicone dane**, które mogą być łatwo wykorzystywane np. przez AI agentów, aplikacje szkolne czy inne integracje, zamiast bezpośrednio przetwarzać HTML generowany przez Optivum.

> **⚠️ Status kompatybilności**
> 
> Optivum jest starym systemem, a sposób jego konfiguracji może różnić się pomiędzy szkołami. Dotyczy to m.in. formatu planów, nazw przedmiotów oraz struktury informacji o zastępstwach. Parser został napisany możliwie uniwersalnie, więc po niewielkich zmianach powinien być możliwy do wykorzystania w innych szkołach.
>
> Parser posiada m.in. normalizację standardowych nazw przedmiotów (np. `j.polski` → `Język polski`) oraz ogólną normalizację niestandardowych nazw.

## Funkcjonalność

* lista dostępnych klas,
* tygodniowy plan lekcji,
* dzienny plan lekcji,
* informacje o zastępstwach,
* nauczyciele i ich kody,
* sale,
* grupy,
* rozkład normalny i skrócony,
* informacje o zawieszeniu lekcji,
* notatki z nagłówka zastępstw,
* cache danych z Optivum.

Dane są zwracane jako JSON zgodny z modelami Pydantic.

## Uruchomienie

Wymagany jest Python 3.10+ (testowano na Python 3.14.6).

```bash
git clone <repo>
cd danio273-optivum-parser

python -m venv .venv
.venv\Scripts\activate             # Windows
# source .venv/bin/activate        # Linux/macOS

pip install -r requirements.txt
```

Następnie:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

API będzie dostępne pod:

```text
http://localhost:8000
```

Dokumentacja FastAPI:

```text
http://localhost:8000/docs
```

## Konfiguracja

Konfigurację można zmienić przez `.env`. Dostępne są m.in.:

```ini
LOG_LEVEL=INFO
CORS_ORIGINS=["*"]

BASE_URL=https://plan.zse.bydgoszcz.pl/
LIST_URL=https://plan.zse.bydgoszcz.pl/lista.html
SUBSTITUTIONS_URL=https://zastepstwa.zse.bydgoszcz.pl/

SCHEDULE_TTL=10800
SUBSTITUTIONS_TTL=300
```

`SCHEDULE_TTL` określa czas cache planów lekcji, a `SUBSTITUTIONS_TTL` czas cache zastępstw.

## API

### `GET /health`

Sprawdzenie dostępności API.

```json
{
  "status": "ok"
}
```

### `GET /classes`

Zwraca mapowanie ID klas na ich nazwy.

```json
{
  "o1": {
    "class_name": "1A",
    "full_class_name": "1A 1A Ivy"
  },
  "o2": {
    "class_name": "1B",
    "full_class_name": "1B"
  }
}
```

ID (`o1`, `o2`, itd.) należy później przekazywać do endpointów planu.

### `GET /schedule/weekly/{class_id}`

Zwraca pełny tygodniowy plan wybranej klasy.

Przykład:

```text
GET /schedule/weekly/o13
```

Struktura odpowiedzi:

```json
{
  "class_name": "3A",
  "full_class_name": "3A 3A Ivy",
  "days": {
    "monday": {
      "class_name": "3A",
      "full_class_name": "3A 3A Ivy",
      "day_name": "monday",
      "header_info": null,
      "slots": [
        {
          "number": 0,
          "regular_time": {
            "start": "07:05",
            "end": "07:50"
          },
          "shortened_time": {
            "start": "07:05",
            "end": "07:35"
          },
          "lessons": [
            {
              "subject": "Zaj. Prakt_1.",
              "teacher_code": "Tr",
              "teacher_name": "J. Truszkowski",
              "room": "W-2",
              "group": "2/3",
              "hash_code": null,
              "substitution": null
            }
          ]
        }
      ]
    }
  }
}
```

`lessons` może zawierać kilka pozycji w jednej godzinie, np. gdy klasa jest podzielona na grupy.

### `GET /schedule/daily/{class_id}`

Zwraca plan na dzień wynikający z aktualnie dostępnych zastępstw.

Przykład:

```text
GET /schedule/daily/o13
```

Oprócz lekcji zwracane są informacje dotyczące danego dnia:

```json
{
  "class_name": "3A",
  "full_class_name": "3A 3A Ivy",
  "day_name": "monday",
  "header_info": {
    "date": "05.10.2026",
    "day_of_week": "monday",
    "last_update": null,
    "is_shortened": false,
    "suspension": null,
    "general_notes": []
  },
  "slots": []
}
```

Jeżeli występuje zastępstwo, zostanie ono zapisane w polu `substitution` konkretnej lekcji. Parser próbuje dopasować zastępstwo najpierw po nauczycielu, a następnie korzysta z dopasowania po klasie jako fallback.

## Błędne ID

Jeżeli podane ID klasy nie istnieje:

```text
GET /schedule/daily/o67
```

API zwróci:

```json
{
  "detail": "Class ID 'o67' does not exist."
}
```

ze statusem HTTP `404`.

## Ważne informacje

Parser nie jest bezpośrednim proxy dla Planu lekcji Optivum. HTML jest pobierany, parsowany i przekształcany do własnego, stabilniejszego modelu danych.

Nazwy dni są normalizowane do języka angielskiego (`monday`, `tuesday`, itd.), a standardowe nazwy przedmiotów są ujednolicane.

Rozkłady godzin są zdefiniowane osobno dla normalnego oraz skróconego dnia.

Domyślnie dane planu są cache'owane przez **3 godziny**, natomiast zastępstwa przez **5 minut**.

## Struktura projektu

```text
├── config.py                # konfiguracja, normalizacja i godziny
├── logger.py                # logging
├── main.py                  # API FastAPI
├── models.py                # modele odpowiedzi
├── timetable_parser.py      # parser planu lekcji
├── substitutions_parser.py  # parser zastępstw
├── requirements.txt
└── .env.example
```

## Przeznaczenie

Projekt jest szczególnie przydatny jako warstwa pośrednia między Optivum a innymi aplikacjami. Zamiast zmuszać klienta do rozumienia struktury HTML Optivum, otrzymuje on prosty i przewidywalny JSON.
