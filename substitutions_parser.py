import re
import threading
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Tuple
from cachetools import TTLCache

import config
from config import settings
from logger import get_logger
from models import (
    ClassSchedule, HeaderInfo, RawSubstitution, Substitution, Suspension, PublicationInfo
)

logger = get_logger(__name__)

class SubstitutionsParser:
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.cache = TTLCache(maxsize=1, ttl=settings.SUBSTITUTIONS_TTL)
        self.lock = threading.Lock()

    def get_substitutions(self) -> Tuple[Optional[HeaderInfo], List[RawSubstitution]]:
        with self.lock:
            if 'data' in self.cache:
                return self.cache['data']
            
            data = self._fetch_substitutions()
            self.cache['data'] = data
            return data

    def _fetch_substitutions(self, url: str = None) -> Tuple[Optional[HeaderInfo], List[RawSubstitution]]:
        target_url = url or settings.SUBSTITUTIONS_URL
        try:
            response = self.session.get(target_url, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'iso-8859-2'
            return self.parse_substitutions_html(response.text)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch substitutions from {target_url}: {e}")
            return None, []

    def parse_substitutions_html(self, html_content: str) -> Tuple[Optional[HeaderInfo], List[RawSubstitution]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        header_info = None
        raw_subs = []
        
        table = soup.find('table')
        if not table:
            logger.warning("No substitutions table found in the HTML content.")
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
        date = day_of_week = ""
        last_update = None
        is_shortened = False
        suspension = None
        general_notes = []
        
        for line in lines:
            line_lower = line.lower()
            if line_lower.startswith("zastępstwa w dniu"):
                parts = line.split()
                if len(parts) >= 5:
                    date, day_of_week = parts[3], config.normalize_day(parts[4])
            elif line_lower.startswith("publikacja:") or line_lower.startswith("aktualizacja:"):
                match = re.search(r'([a-zA-ZźżćłąśęóńŹŻĆŁĄŚĘÓŃ]+)[,\s]+(\d{1,2})[.:](\d{2})', line)
                if match:
                    last_update = PublicationInfo(
                        day_of_week=config.normalize_day(match.group(1)),
                        time=f"{match.group(2).zfill(2)}:{match.group(3)}"
                    )
            elif "zawieszone" in line_lower:
                time_m = re.search(r'godzinie\s+(\d{1,2})[.:](\d{2})', line_lower)
                lesson_m = re.search(r'po\s+(\d+)\s+godzinie', line_lower)
                suspension = Suspension(
                    raw_text=line,
                    time=f"{time_m.group(1).zfill(2)}:{time_m.group(2)}" if time_m else None,
                    after_lesson=int(lesson_m.group(1)) if lesson_m else None
                )
            elif "skrócony" in line_lower:
                is_shortened = True
            elif "rozkład godzinowy" not in line_lower:
                clean_note = re.sub(r'^Uwaga\s*\d*\s*[!.]*\s*(?:\.\s*\.\s*\.\s*)?', '', line, flags=re.IGNORECASE).strip()
                if clean_note:
                    general_notes.append(clean_note)
                    
        return HeaderInfo(
            date=date, day_of_week=day_of_week, last_update=last_update,
            is_shortened=is_shortened, suspension=suspension, general_notes=general_notes
        )

    def apply_substitutions(self, schedule: ClassSchedule, header_info: HeaderInfo, raw_subs: List[RawSubstitution]):
        if not header_info or not header_info.day_of_week: return
            
        target_day = header_info.day_of_week
        if target_day not in schedule.days: return
            
        day_schedule = schedule.days[target_day]
        day_schedule.header_info = header_info
        
        for raw_sub in raw_subs:
            clean_desc = raw_sub.description.split("-", 1)[1].strip() if "-" in raw_sub.description else raw_sub.description.strip()
            sub_obj = Substitution(description=clean_desc, substitute=raw_sub.substitute, note=raw_sub.note)
            
            target_slot = next((s for s in day_schedule.slots if s.number == raw_sub.lesson_num), None)
            if not target_slot: continue
                
            matched = False
            for lesson in target_slot.lessons:
                if self._match_teacher(raw_sub.teacher_name, lesson.teacher_name):
                    lesson.substitution = sub_obj
                    matched = True
                    break
                    
            if matched: continue
                
            for lesson in target_slot.lessons:
                if self._match_class_fallback(schedule.class_name, raw_sub.description):
                    lesson.substitution = sub_obj
                    break

    def _match_teacher(self, sub_teacher: Optional[str], lesson_teacher: Optional[str]) -> bool:
        if not sub_teacher or not lesson_teacher: return False
        sub_parts, les_parts = sub_teacher.strip().lower().split(), lesson_teacher.strip().lower().split()
        if sub_parts[-1] == les_parts[-1]:
            if len(les_parts) > 1 and les_parts[0].endswith('.'):
                return sub_parts[0][0] == les_parts[0][0]
            return True
        return False

    def _match_class_fallback(self, target_class_name: str, description: str) -> bool:
        match = re.search(r'^(\d+\s*[A-Za-z]+)', description.strip())
        if match:
            extracted = match.group(1).replace(" ", "").lower()
            target = target_class_name.replace(" ", "").lower()
            return target.startswith(extracted) or extracted.startswith(target)
        return False