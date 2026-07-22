import config
from parser import VulcanParser

def main():
    print(f"[*] Initializing parser using List URL: {config.LIST_URL}")
    parser = VulcanParser()
    
    print("[*] Building dynamic teacher map...")
    parser.initialize_teachers()
    print(f"[+] Parsed {len(parser.teachers_map)} teachers.")
    
    print(f"\n[*] Parsing Target Class Timetable: {config.TARGET_CLASS_URL}")
    schedule = parser.parse_class_timetable(config.TARGET_CLASS_URL)
    
    target_day = "monday"
    print(f"\n--- Output for: {target_day.upper()} ---")
    
    for slot in schedule[target_day].slots:
        if slot.lessons:
            lesson_details = []
            for l in slot.lessons:
                group_info = f" [Group: {l.group}]" if l.group else ""
                teacher_info = f" (Teacher: {l.teacher_name or l.teacher_code})"
                room_info = f" Room: {l.room}"
                
                lesson_details.append(f"{l.subject}{group_info}{teacher_info}{room_info}")
                
            print(f"{slot.number:2} ({slot.time}) | {'  AND  '.join(lesson_details)}")

if __name__ == "__main__":
    main()