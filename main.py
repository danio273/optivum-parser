import json
from dataclasses import asdict
import config
from parser import VulcanParser

def main():
    print(f"[*] Initializing parser using List URL: {config.LIST_URL}")
    parser = VulcanParser()
    
    print("[*] Building dynamic teacher map...")
    parser.initialize_teachers()
    print(f"[+] Parsed {len(parser.teachers_map)} teachers.")
    
    print(f"\n[*] Parsing Target Class: {config.TARGET_CLASS_URL}")
    schedule = parser.parse_class_timetable(config.TARGET_CLASS_URL)
    
    target_day = "monday"
    if target_day in schedule:
        print(f"\n--- Output for: {target_day.upper()} ---")
        for slot in schedule[target_day].slots:
            reg = f"{slot.regular_time.start}-{slot.regular_time.end}"
            short = f"{slot.shortened_time.start}-{slot.shortened_time.end}"
            
            if slot.lessons:
                lesson_details = [
                    f"{l.subject}"
                    f"{f' [Group: {l.group}]' if l.group else ''}"
                    f"{f' [Hash: {l.hash_code}]' if l.hash_code else ''}"
                    f" (Teacher: {l.teacher_name or l.teacher_code})"
                    f" Room: {l.room}"
                    for l in slot.lessons
                ]
                print(f"{slot.number:2} (Reg: {reg} | Short: {short}) | {' AND '.join(lesson_details)}")
            else:
                print(f"{slot.number:2} (Reg: {reg} | Short: {short}) | -")

    if target_day in schedule:
        print("\n--- Example JSON Structure for API Response ---")
        day_dict = schedule[target_day].to_dict()
        # Displaying first 2 slots serialized to JSON string
        day_dict["slots"] = day_dict["slots"][:3]
        print(json.dumps(day_dict, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()