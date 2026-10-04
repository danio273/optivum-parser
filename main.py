import copy
from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from logger import get_logger
from timetable_parser import TimetableParser
from substitutions_parser import SubstitutionsParser
from models import ClassSchedule, DaySchedule, DailySchedule, DailySlot, ClassItem

logger = get_logger(__name__)

tt_parser = TimetableParser()
sub_parser = SubstitutionsParser()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application, initializing timetable index data...")
    try:
        tt_parser.get_index_data()
        logger.info("Index data successfully cached.")
    except Exception as e:
        logger.error(f"Failed to initialize index data during startup: {e}")
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title="Optivum Timetable API", 
    description="Query weekly class schedules and dynamic daily substitutions.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}

@app.get("/classes", response_model=Dict[str, ClassItem], tags=["Timetable"])
def get_available_classes():
    try:
        _, classes_map = tt_parser.get_index_data()
        return {
            class_id: ClassItem(
                class_name=data["class_name"],
                full_class_name=data["full_class_name"]
            )
            for class_id, data in classes_map.items()
        }
    except ValueError as e:
        logger.error(f"Error fetching available classes: {e}")
        raise HTTPException(status_code=503, detail="Class mapping not initialized or unavailable.")

@app.get("/schedule/weekly/{class_id}", response_model=ClassSchedule, tags=["Timetable"])
def get_weekly_schedule(class_id: str):
    _, classes_map = tt_parser.get_index_data()
    if class_id not in classes_map:
        raise HTTPException(status_code=404, detail=f"Class ID '{class_id}' does not exist.")
        
    schedule = tt_parser.get_class_schedule(class_id)
    if not schedule:
        logger.error(f"Failed to parse schedule for class_id: {class_id}")
        raise HTTPException(status_code=500, detail="Failed to parse the class timetable.")
        
    return schedule

@app.get("/schedule/daily/{class_id}", response_model=DailySchedule, tags=["Timetable"])
def get_daily_substitutions(class_id: str):
    _, classes_map = tt_parser.get_index_data()
    if class_id not in classes_map:
        raise HTTPException(status_code=404, detail=f"Class ID '{class_id}' does not exist.")
        
    schedule = tt_parser.get_class_schedule(class_id)
    if not schedule:
        logger.error(f"Failed to parse schedule for class_id: {class_id} during daily substitution check.")
        raise HTTPException(status_code=500, detail="Failed to parse the class timetable.")

    schedule_copy = copy.deepcopy(schedule)

    header_info, raw_subs = sub_parser.get_substitutions()
    if not header_info or not header_info.day_of_week:
        logger.warning("No active substitution header found.")
        raise HTTPException(status_code=404, detail="No active substitution header found.")
        
    sub_parser.apply_substitutions(schedule_copy, header_info, raw_subs)
    
    target_day = header_info.day_of_week
    if target_day not in schedule_copy.days:
        raise HTTPException(status_code=404, detail=f"Substitutions target '{target_day}', which is not in the schedule.")
        
    day_schedule = schedule_copy.days[target_day]
    
    daily_slots = [
        DailySlot(
            number=slot.number,
            time=slot.shortened_time if header_info.is_shortened else slot.regular_time,
            lessons=slot.lessons
        )
        for slot in day_schedule.slots
    ]

    return DailySchedule(
        class_name=schedule_copy.class_name,
        full_class_name=schedule_copy.full_class_name,
        day_name=day_schedule.day_name,
        header_info=header_info,
        slots=daily_slots
    )