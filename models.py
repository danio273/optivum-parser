from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class TimeSlot(BaseModel):
    start: str
    end: str

class PublicationInfo(BaseModel):
    day_of_week: str
    time: str

class Substitution(BaseModel):
    description: str
    substitute: str
    note: str

class Suspension(BaseModel):
    raw_text: str
    time: Optional[str] = None
    after_lesson: Optional[int] = None

class HeaderInfo(BaseModel):
    date: str
    day_of_week: str
    last_update: Optional[PublicationInfo] = None
    is_shortened: bool = False
    suspensions: List[Suspension] = Field(default_factory=list)
    general_notes: List[str] = Field(default_factory=list)

class RawSubstitution(BaseModel):
    teacher_name: Optional[str] = None
    lesson_num: int
    description: str
    substitute: str
    note: str

class Lesson(BaseModel):
    subject: str
    teacher_code: Optional[str] = None
    teacher_name: Optional[str] = None
    room: Optional[str] = None
    group: Optional[str] = None
    hash_code: Optional[str] = None
    substitution: Optional[Substitution] = None

class Slot(BaseModel):
    number: int
    regular_time: TimeSlot
    shortened_time: TimeSlot
    lessons: List[Lesson] = Field(default_factory=list)

class DaySchedule(BaseModel):
    day_name: str
    header_info: Optional[HeaderInfo] = None
    slots: List[Slot] = Field(default_factory=list)

class ClassSchedule(BaseModel):
    class_name: str
    full_class_name: str
    days: Dict[str, DaySchedule] = Field(default_factory=dict)