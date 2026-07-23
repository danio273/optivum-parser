from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

@dataclass
class TimeSlot:
    """Stores start and end times in string formats (HH:MM)."""
    start: str
    end: str

@dataclass
class Lesson:
    """Represents a single lesson for a group in a time slot."""
    subject: str
    teacher_code: Optional[str] = None
    teacher_name: Optional[str] = None
    room: Optional[str] = None
    group: Optional[str] = None
    hash_code: Optional[str] = None

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
    slots: List[Slot] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the model directly into a JSON-serializable dictionary."""
        return asdict(self)