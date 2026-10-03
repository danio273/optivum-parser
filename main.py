from fastapi import FastAPI, HTTPException
from timetable_parser import TimetableParser
from substitutions_parser import SubstitutionsParser
from models import ClassSchedule, DaySchedule

app = FastAPI(
    title="Optivum Timetable API", 
    description="Query weekly class schedules and dynamic daily substitutions.",
    version="1.0.0"
)

tt_parser = TimetableParser()
sub_parser = SubstitutionsParser()

@app.on_event("startup")
def startup_event():
    tt_parser.initialize_data()

@app.get("/classes")
def get_available_classes():
    if not tt_parser.classes_map:
        raise HTTPException(status_code=503, detail="Class mapping not initialized or unavailable.")
    return {class_id: data["name"] for class_id, data in tt_parser.classes_map.items()}

@app.get("/schedule/weekly/{class_id}", response_model=ClassSchedule)
def get_weekly_schedule(class_id: str):
    if class_id not in tt_parser.classes_map:
        raise HTTPException(status_code=404, detail=f"Class ID '{class_id}' does not exist.")
        
    schedule = tt_parser.parse_class_timetable(class_id)
    if not schedule:
        raise HTTPException(status_code=500, detail="Failed to parse the class timetable.")
        
    return schedule

@app.get("/schedule/daily/{class_id}", response_model=DaySchedule)
def get_daily_substitutions(class_id: str):
    if class_id not in tt_parser.classes_map:
        raise HTTPException(status_code=404, detail=f"Class ID '{class_id}' does not exist.")
        
    schedule = tt_parser.parse_class_timetable(class_id)
    if not schedule:
        raise HTTPException(status_code=500, detail="Failed to parse the class timetable.")

    header_info, raw_subs = sub_parser.fetch_substitutions()
    
    if not header_info or not header_info.day_of_week:
        raise HTTPException(status_code=404, detail="No active substitution header found.")
        
    sub_parser.apply_substitutions(schedule, header_info, raw_subs)
    
    target_day = header_info.day_of_week
    if target_day not in schedule.days:
        raise HTTPException(status_code=404, detail=f"Substitutions target '{target_day}', which is not in the schedule.")
        
    return schedule.days[target_day]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)