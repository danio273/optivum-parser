import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple

import config
from models import Lesson, Slot, DaySchedule, ClassSchedule, TimeSlot

class TimetableParser:
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.teachers_map: Dict[str, str] = {}
        self.classes_map: Dict[str, Dict[str, str]] = {}
        
    def _fetch_soup(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException:
            return None

    def initialize_data(self):
        soup = self._fetch_soup(config.LIST_URL)
        if not soup:
            raise ValueError(f"Could not load main index from {config.LIST_URL}")
            
        teachers_header = soup.find('h4', string=re.compile("Nauczyciele", re.I))
        if teachers_header:
            ul = teachers_header.find_next_sibling('ul')
            if ul:
                for li in ul.find_all('li'):
                    text = li.get_text(strip=True)
                    match = re.search(r'^(.*?)\s*\((.*?)\)$', text)
                    if match:
                        raw_name, code = match.group(1).strip(), match.group(2).strip()
                        clean_name = re.sub(r'^([A-ZŻŹĆŃŁŚÓĘĄa-zżźćńłśóęą]\.)([A-ZŻŹĆŃŁŚÓĘĄ])', r'\1 \2', raw_name)
                        self.teachers_map[code] = clean_name

        classes_header = soup.find('h4', string=re.compile("Oddziały", re.I))
        if classes_header:
            ul = classes_header.find_next_sibling('ul')
            if ul:
                for a in ul.find_all('a', href=True):
                    href = a['href']
                    match = re.search(r'plany/(o\d+)\.html', href)
                    if match:
                        class_id = match.group(1)
                        raw_name = a.get_text(strip=True)
                        short_name = raw_name.split()[0] if raw_name else ""
                        self.classes_map[class_id] = {
                            "class_name": short_name,
                            "full_class_name": raw_name,
                            "url": f"{config.BASE_URL}{href}"
                        }

    def _format_custom_subject(self, subject: str) -> str:
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

    def normalize_subject(self, raw_text: str) -> Tuple[str, Optional[str], Optional[str]]:
        text = raw_text.strip()
        hash_code = group = None
        
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
        subject = config.GENERAL_SUBJECTS.get(text_lower, self._format_custom_subject(text))
            
        return subject, group, hash_code

    def parse_class_timetable(self, class_id: str) -> Optional[ClassSchedule]:
        if class_id not in self.classes_map:
            return None

        url = self.classes_map[class_id]["url"]
        soup = self._fetch_soup(url)
        if not soup:
            return None

        title_tag = soup.find('span', class_='tytulnapis')
        full_class_name = title_tag.get_text(strip=True) if title_tag else (soup.title.get_text(strip=True).replace("Plan lekcji oddziału -", "").strip() if soup.title else "")
        main_class_name = full_class_name.split()[0] if full_class_name else ""

        if class_id in self.classes_map:
            self.classes_map[class_id]["class_name"] = main_class_name
            self.classes_map[class_id]["full_class_name"] = full_class_name

        table = soup.find('table', class_='tabela')
        if not table:
            return None

        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        days = [config.normalize_day(day) for day in headers[2:]]
        
        class_schedule = ClassSchedule(
            class_name=main_class_name,
            full_class_name=full_class_name,
            days={
                day: DaySchedule(
                    class_name=main_class_name,
                    full_class_name=full_class_name,
                    day_name=day
                ) for day in days
            }
        )
        
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if not cells or 'nr' not in cells[0].get('class', []):
                continue 
                
            slot_number = int(cells[0].get_text(strip=True))
            reg_dict = config.REGULAR_SCHEDULE.get(slot_number)
            short_dict = config.SHORTENED_SCHEDULE.get(slot_number)
            
            if not reg_dict or not short_dict:
                continue
                
            regular_time = TimeSlot(**reg_dict)
            shortened_time = TimeSlot(**short_dict)
            
            for day_index, cell in enumerate(cells[2:]):
                day_name = days[day_index]
                parsed_lessons = self._parse_cell(cell)
                
                if parsed_lessons:
                    class_schedule.days[day_name].slots.append(Slot(
                        number=slot_number, 
                        regular_time=regular_time,
                        shortened_time=shortened_time,
                        lessons=parsed_lessons
                    ))
                
        return class_schedule

    def _parse_cell(self, cell) -> List[Lesson]:
        lessons = []
        html_content = cell.decode_contents()
        parts = re.split(r'<br\s*/?>', html_content, flags=re.IGNORECASE)
        
        for part in parts:
            if not part.strip() or part.strip() == '&nbsp;':
                continue
                
            part_soup = BeautifulSoup(part, 'html.parser')
            n_tag = part_soup.find('a', class_='n')
            s_tag = part_soup.find('a', class_='s')
            
            teacher_code = n_tag.get_text(strip=True) if n_tag else None
            room = s_tag.get_text(strip=True).upper() if s_tag else None
            
            if n_tag: n_tag.decompose()
            if s_tag: s_tag.decompose()
                
            raw_remaining_text = part_soup.get_text(strip=True)
            if not raw_remaining_text:
                continue
                
            clean_subject, group, hash_code = self.normalize_subject(raw_remaining_text)
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