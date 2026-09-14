import re
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Tuple

import config
from models import (
    ClassSchedule, HeaderInfo, RawSubstitution, Substitution, Suspension, PublicationInfo
)

class SubstitutionsParser:
    """Handles fetching, parsing, and applying school substitutions directly from URL."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    def fetch_substitutions(self, url: str = config.SUBSTITUTIONS_URL) -> Tuple[Optional[HeaderInfo], List[RawSubstitution]]:
        """Downloads substitutions HTML directly from the URL and parses it."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'iso-8859-2'
            return self.parse_substitutions_html(response.text)
        except requests.RequestException as e:
            print(f"[!] Error fetching substitutions from {url}: {e}")
            return None, []

    def parse_substitutions_html(self, html_content: str) -> Tuple[Optional[HeaderInfo], List[RawSubstitution]]:
        """Parses substitution HTML content into header metadata and raw substitution records."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        header_info = None
        raw_subs = []
        
        table = soup.find('table')
        if not table:
            return None, []
            
        header_cell = soup.find('td', class_='st0')
        if header_cell:
            header_info = self._parse_substitution_headers(header_cell)
            
        current_teacher = None
        for tr in table.find_all('tr'):
            cells = tr.find_all('td')
            if not cells:
                continue
            
            if len(cells) == 1 and cells[0].get('colspan') == '4':
                current_teacher = cells[0].get_text(strip=True)
                continue
                
            if len(cells) == 4:
                c0 = cells[0].get_text(strip=True)
                if c0.lower() == 'lekcja' or not c0:
                    continue
                    
                try:
                    lesson_num = int(c0)
                except ValueError:
                    continue
                    
                desc = cells[1].get_text(strip=True)
                substitute = cells[2].get_text(strip=True)
                note = cells[3].get_text(strip=True).replace('\xa0', '')
                
                raw_subs.append(RawSubstitution(
                    teacher_name=current_teacher,
                    lesson_num=lesson_num,
                    description=desc,
                    substitute=substitute,
                    note=note
                ))
                
        return header_info, raw_subs

    def _parse_substitution_headers(self, cell) -> HeaderInfo:
        lines = [line.strip() for line in cell.stripped_strings if line.strip()]
        
        date, day_of_week = "", ""
        last_update: Optional[PublicationInfo] = None
        is_shortened = False
        suspensions = []
        general_notes = []
        
        for line in lines:
            line_lower = line.lower()
            
            if line_lower.startswith("zastępstwa w dniu"):
                parts = line.split()
                if len(parts) >= 5:
                    date = parts[3]
                    day_of_week = config.normalize_day(parts[4])
                    
            elif line_lower.startswith("publikacja:") or line_lower.startswith("aktualizacja:"):
                match = re.search(r'([a-zA-ZźżćłąśęóńŹŻĆŁĄŚĘÓŃ]+)[,\s]+(\d{1,2})[.:](\d{2})', line)
                if match:
                    raw_day = match.group(1)
                    hour = match.group(2).zfill(2)
                    minute = match.group(3)
                    norm_day = config.normalize_day(raw_day)
                    formatted_time = f"{hour}:{minute}"
                    last_update = PublicationInfo(day_of_week=norm_day, time=formatted_time)
                    
            elif "zawieszone" in line_lower:
                time_m = re.search(r'godzinie\s+(\d{1,2})[.:](\d{2})', line_lower)
                time_str = f"{time_m.group(1).zfill(2)}:{time_m.group(2)}" if time_m else None

                lesson_m = re.search(r'po\s+(\d+)\s+godzinie', line_lower)
                lesson_num = int(lesson_m.group(1)) if lesson_m else None
                
                suspensions.append(Suspension(raw_text=line, time=time_str, after_lesson=lesson_num))
                
            elif "skrócony" in line_lower:
                is_shortened = True
                
            elif "rozkład godzinowy" in line_lower:
                continue
                
            else:
                clean_note = re.sub(r'^Uwaga\s*\d*\s*[!.]*\s*(?:\.\s*\.\s*\.\s*)?', '', line, flags=re.IGNORECASE).strip()
                if clean_note:
                    general_notes.append(clean_note)
                    
        return HeaderInfo(date, day_of_week, last_update, is_shortened, suspensions, general_notes)

    def apply_substitutions(self, schedule: ClassSchedule, header_info: HeaderInfo, raw_subs: List[RawSubstitution]):
        """Merges parsed substitutions into the existing timetable."""
        if not header_info or not header_info.day_of_week:
            return
            
        target_day = header_info.day_of_week
        if target_day not in schedule.days:
            return
            
        day_schedule = schedule.days[target_day]
        day_schedule.header_info = header_info
        
        for raw_sub in raw_subs:
            clean_desc = raw_sub.description.split("-", 1)[1].strip() if "-" in raw_sub.description else raw_sub.description.strip()
            
            sub_obj = Substitution(
                description=clean_desc,
                substitute=raw_sub.substitute,
                note=raw_sub.note
            )
            
            target_slot = next((s for s in day_schedule.slots if s.number == raw_sub.lesson_num), None)
            if not target_slot:
                continue
                
            matched = False
            
            for lesson in target_slot.lessons:
                if self._match_teacher(raw_sub.teacher_name, lesson.teacher_name):
                    lesson.substitution = sub_obj
                    matched = True
                    break
                    
            if matched:
                continue
                
            for lesson in target_slot.lessons:
                if self._match_class_fallback(schedule.class_name, raw_sub.description):
                    lesson.substitution = sub_obj
                    break

    def _match_teacher(self, sub_teacher: str, lesson_teacher: Optional[str]) -> bool:
        if not sub_teacher or not lesson_teacher:
            return False
            
        sub_parts = sub_teacher.strip().lower().split()
        les_parts = lesson_teacher.strip().lower().split()
        
        if sub_parts[-1] == les_parts[-1]:
            if len(les_parts) > 1 and les_parts[0].endswith('.'):
                if sub_parts[0][0] == les_parts[0][0]:
                    return True
            else:
                return True
        return False

    def _match_class_fallback(self, target_class_name: str, description: str) -> bool:
        match = re.search(r'^(\d+\s*[A-Za-z]+)', description.strip())
        if match:
            extracted = match.group(1).replace(" ", "").lower()
            target = target_class_name.replace(" ", "").lower()
            return target.startswith(extracted) or extracted.startswith(target)
        return False