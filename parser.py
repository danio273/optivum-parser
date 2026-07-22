import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple

import config
from models import Lesson, Slot, DaySchedule

class VulcanParser:
    """Handles fetching and parsing of VULCAN Optivum HTML timetables."""
    
    def __init__(self):
        self.session = requests.Session()
        self.teachers_map: Dict[str, str] = {}
        
    def _fetch_soup(self, url: str) -> BeautifulSoup:
        """Helper method to download a page and parse it into a BeautifulSoup object."""
        response = self.session.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8' 
        return BeautifulSoup(response.text, 'html.parser')

    def initialize_teachers(self):
        """Scrapes the main list URL to dynamically build a map of Teacher Code -> Full Name."""
        soup = self._fetch_soup(config.LIST_URL)
        
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
                
                clean_name = re.sub(r'^([A-ZŻŹĆŃŁŚÓĘĄa-zżźćńłśóęą]\.)([A-ZŻŹĆŃŃŁŚÓĘĄ])', r'\1 \2', raw_name)
                self.teachers_map[code] = clean_name

    def _format_custom_subject(self, subject: str) -> str:
        """
        Standardizes specialized/unmapped subject names:
        - Ensures spaces after periods (e.g., 'Pr.Ap.In.' -> 'Pr. Ap. In.').
        - Capitalizes each word part while keeping 'i' lowercase.
        - Ensures abbreviation dots are consistently applied if the subject uses dots.
        """
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

    def normalize_subject(self, raw_subject: str) -> Tuple[str, Optional[str]]:
        """
        Cleans the subject name, applies config mapping, or formats specialized abbreviations.
        """
        subject = raw_subject.strip()
        group = None
        
        group_match = re.search(r'-(j?\d+/\d+|j?\d+)$', subject)
        if group_match:
            group = group_match.group(1)
            subject = subject[:group_match.start()].strip()
            
        subject = re.sub(r'#\S+', '', subject).strip()
        
        if subject.startswith('r_'):
            subject = subject[2:]
            
        subject_lower = subject.lower()
        if subject_lower in config.GENERAL_SUBJECTS:
            subject = config.GENERAL_SUBJECTS[subject_lower]
        else:
            subject = self._format_custom_subject(subject)
            
        return subject, group

    def parse_class_timetable(self, target_url: str = config.TARGET_CLASS_URL) -> Dict[str, DaySchedule]:
        """Parses a specific class timetable page into structured data."""
        full_url = urllib.parse.urljoin(config.LIST_URL, target_url)
        soup = self._fetch_soup(full_url)
        
        table = soup.find('table', class_='tabela')
        if not table:
            raise ValueError(f"No timetable table found at {full_url}")
            
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        
        raw_days = headers[2:]
        days = [config.DAY_MAPPING.get(day, day) for day in raw_days]
        
        schedule = {day: DaySchedule(day_name=day) for day in days}
        
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if not cells or 'nr' not in cells[0].get('class', []):
                continue 
                
            slot_number = int(cells[0].get_text(strip=True))
            slot_time = cells[1].get_text(strip=True)
            
            for day_index, cell in enumerate(cells[2:]):
                day_name = days[day_index]
                parsed_lessons = self._parse_cell(cell)
                
                slot = Slot(number=slot_number, time=slot_time, lessons=parsed_lessons)
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
            
            p_tag = part_soup.find('span', class_='p')
            n_tag = part_soup.find('a', class_='n')
            s_tag = part_soup.find('a', class_='s')
            
            raw_subject = p_tag.get_text(strip=True) if p_tag else part_soup.get_text(strip=True)
            if not raw_subject:
                continue
                
            clean_subject, group = self.normalize_subject(raw_subject)
            
            teacher_code = n_tag.get_text(strip=True) if n_tag else None
            
            room = s_tag.get_text(strip=True).upper() if s_tag else None
            
            teacher_name = None
            if teacher_code and teacher_code in self.teachers_map:
                teacher_name = self.teachers_map[teacher_code]
                
            lessons.append(Lesson(
                subject=clean_subject,
                teacher_code=teacher_code,
                teacher_name=teacher_name,
                room=room,
                group=group
            ))
            
        return lessons