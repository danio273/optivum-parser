from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Lesson:
    """Represents a single lesson for a specific group in a specific time slot."""
    subject: str
    teacher_code: Optional[str] = None
    teacher_name: Optional[str] = None
    room: Optional[str] = None
    group: Optional[str] = None

@dataclass
class Slot:
    """Represents a time block containing one or more concurrent group lessons."""
    number: int
    time: str
    lessons: List[Lesson] = field(default_factory=list)

@dataclass
class DaySchedule:
    """Represents an entire day of lessons."""
    day_name: str
    slots: List[Slot] = field(default_factory=list)