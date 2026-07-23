import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple

import config
from models import Lesson, Slot, DaySchedule, TimeSlot

class VulcanParser:
    """Handles fetching and parsing of VULCAN Optivum HTML timetables."""
    
    def __init__(self):
        self.session = requests.Session()
        self.teachers_map: Dict[str, str] = {}
        
    def _fetch_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Helper method to download a page and parse it into BeautifulSoup. Returns None on HTTP failure."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            response.encoding = 'utf-8' 
            return BeautifulSoup(response.text, 'html.parser')
        except requests.HTTPError:
            return None

    def initialize_teachers(self):
        """Scrapes the main list URL to dynamically build a map of Teacher Code -> Full Name."""
        soup = self._fetch_soup(config.LIST_URL)
        if not soup:
            raise ValueError(f"Could not load main index from {config.LIST_URL}")
            
        teachers_header = soup.find('h4', string=re.compile("Nauczyciele", re.I))
        if not teachers_header:
            raise ValueError("Could not find 'Nauczyciele' section on the main page.")
            
        ul = teachers_header.find_next_sibling('ul')
        for li in ul.find_all('li'):
            text = li.get_text(strip=True)
            match = re.search(r'^(.*?)\s*\((.*?)\)$', text)
            if match:
                raw_name = match.group(1).strip()
                code = match.group(2).strip()
                clean_name = re.sub(r'^([A-ZŻŹĆŃŁŚÓĘĄa-zżźćńłśóęą]\.)([A-ZŻŹĆŃŁŚÓĘĄ])', r'\1 \2', raw_name)
                self.teachers_map[code] = clean_name

    def is_class_active(self, target_url: str) -> bool:
        """Checks if the requested class exists in the main index (lista.html)."""
        soup = self._fetch_soup(config.LIST_URL)
        if not soup:
            return False
            
        target_file = target_url.split('/')[-1]
        for a in soup.find_all('a', href=True):
            if a['href'].endswith(target_file):
                return True
        return False

    def _format_custom_subject(self, subject: str) -> str:
        """Standardizes unmapped subject names (e.g., 'Pr.Ap.In.' -> 'Pr. Ap. In.')."""
        subject = re.sub(r'\.(?=[^\s$])', '. ', subject)
        has_abbreviation_dots = '.' in subject
        words = subject.split()
        formatted_words = []
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            if word_lower == 'i' and i > 0:
                formatted_words.append('i')
            else:
                if has_abbreviation_dots and not word.endswith('.') and not word.endswith(','):
                    word += '.'
                formatted_word = word[0].upper() + word[1:] if word else ''
                formatted_words.append(formatted_word)
                
        return " ".join(formatted_words)

    def normalize_subject_and_metadata(self, raw_text: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Parses subject string."""
        text = raw_text.strip()
        hash_code = None
        group = None
        
        hash_match = re.search(r'#(\S+)', text)
        if hash_match:
            hash_code = f"#{hash_match.group(1)}"
            text = re.sub(r'#\S+', '', text).strip()
            
        group_match = re.search(r'-(j?\d+/\d+|j?\d+)$', text)
        if group_match:
            group = group_match.group(1)
            text = text[:group_match.start()].strip()
            
        if text.startswith('r_'):
            text = text[2:]
            
        text_lower = text.lower()
        if text_lower in config.GENERAL_SUBJECTS:
            subject = config.GENERAL_SUBJECTS[text_lower]
        else:
            subject = self._format_custom_subject(text)
            
        return subject, group, hash_code

    def parse_class_timetable(self, target_url: str = config.TARGET_CLASS_URL) -> Dict[str, DaySchedule]:
        """Parses a specific class timetable page into structured data."""
        if not self.is_class_active(target_url):
            print(f"[!] Target class '{target_url}' is not active or present on the list. Returning empty schedule.")
            return {}

        full_url = urllib.parse.urljoin(config.LIST_URL, target_url)
        soup = self._fetch_soup(full_url)
        if not soup:
            return {}

        table = soup.find('table', class_='tabela')
        if not table:
            return {}

        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        raw_days = headers[2:]
        days = [config.DAY_MAPPING.get(day, day) for day in raw_days]
        
        schedule = {day: DaySchedule(day_name=day) for day in days}
        
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if not cells or 'nr' not in cells[0].get('class', []):
                continue 
                
            slot_number = int(cells[0].get_text(strip=True))
            
            reg_t = config.REGULAR_SCHEDULE.get(slot_number)
            short_t = config.SHORTENED_SCHEDULE.get(slot_number)
            
            if not reg_t or not short_t:
                continue
                
            regular_time = TimeSlot(start=reg_t["start"], end=reg_t["end"])
            shortened_time = TimeSlot(start=short_t["start"], end=short_t["end"])
            
            for day_index, cell in enumerate(cells[2:]):
                day_name = days[day_index]
                parsed_lessons = self._parse_cell(cell)
                
                slot = Slot(
                    number=slot_number, 
                    regular_time=regular_time,
                    shortened_time=shortened_time,
                    lessons=parsed_lessons
                )
                schedule[day_name].slots.append(slot)
                
        return schedule

    def _parse_cell(self, cell) -> List[Lesson]:
        """Parses a single HTML table cell (`td`), handling multiple groups."""
        lessons = []
        html_content = cell.decode_contents()
        parts = re.split(r'<br\s*/?>', html_content, flags=re.IGNORECASE)
        
        for part in parts:
            if not part.strip():
                continue
                
            part_soup = BeautifulSoup(part, 'html.parser')
            
            n_tag = part_soup.find('a', class_='n')
            s_tag = part_soup.find('a', class_='s')
            
            teacher_code = n_tag.get_text(strip=True) if n_tag else None
            room = s_tag.get_text(strip=True).upper() if s_tag else None
            
            if n_tag:
                n_tag.decompose()
            if s_tag:
                s_tag.decompose()
                
            raw_remaining_text = part_soup.get_text(strip=True)
            if not raw_remaining_text:
                continue
                
            clean_subject, group, hash_code = self.normalize_subject_and_metadata(raw_remaining_text)
            
            teacher_name = self.teachers_map.get(teacher_code) if teacher_code else None
                
            lessons.append(Lesson(
                subject=clean_subject,
                teacher_code=teacher_code,
                teacher_name=teacher_name,
                room=room,
                group=group,
                hash_code=hash_code
            ))
            
        return lessons