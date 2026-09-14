from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

@dataclass
class TimeSlot:
    """Stores start and end times in string formats (HH:MM)."""
    start: str
    end: str

@dataclass
class PublicationInfo:
    """Stores normalized publication or update date/time."""
    day_of_week: str
    time: str

@dataclass
class Substitution:
    """Stores isolated substitution details."""
    description: str
    substitute: str
    note: str

@dataclass
class Suspension:
    """Stores information about suspended classes."""
    raw_text: str
    time: Optional[str] = None
    after_lesson: Optional[int] = None

@dataclass
class HeaderInfo:
    """Stores parsed header metadata for a specific day of substitutions."""
    date: str
    day_of_week: str
    last_update: Optional[PublicationInfo] = None
    is_shortened: bool = False
    suspensions: List[Suspension] = field(default_factory=list)
    general_notes: List[str] = field(default_factory=list)

@dataclass
class RawSubstitution:
    """Temporary model to hold parsed rows before merging."""
    teacher_name: str
    lesson_num: int
    description: str
    substitute: str
    note: str

@dataclass
class Lesson:
    """Represents a single lesson for a group in a time slot."""
    subject: str
    teacher_code: Optional[str] = None
    teacher_name: Optional[str] = None
    room: Optional[str] = None
    group: Optional[str] = None
    hash_code: Optional[str] = None
    substitution: Optional[Substitution] = None

@dataclass
class Slot:
    """Represents a time block containing both regular and shortened schedules."""
    number: int
    regular_time: TimeSlot
    shortened_time: TimeSlot
    lessons: List[Lesson] = field(default_factory=list)

@dataclass
class DaySchedule:
    """Represents an entire day of lessons."""
    day_name: str
    header_info: Optional[HeaderInfo] = None
    slots: List[Slot] = field(default_factory=list)

@dataclass
class ClassSchedule:
    """Represents the full weekly schedule for a class."""
    class_name: str
    full_class_name: str
    days: Dict[str, DaySchedule] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the model directly into a JSON-serializable dictionary."""
        return asdict(self)