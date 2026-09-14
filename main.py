import json
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
    
    if not schedule:
        print("[!] Failed to parse timetable.")
        return

    print(f"\n=== SCHEDULE FOR CLASS: {schedule.class_name} (Full Name: '{schedule.full_class_name}') ===")

    for day_name, day_schedule in schedule.days.items():
        print(f"\n--- {day_name.upper()} ---")
        if not day_schedule.slots:
            print("  Brak zajęć w tym dniu.")
            continue

        for slot in day_schedule.slots:
            reg = f"{slot.regular_time.start}-{slot.regular_time.end}"
            short = f"{slot.shortened_time.start}-{slot.shortened_time.end}"
            
            lesson_details = [
                f"{l.subject}"
                f"{f' [Group: {l.group}]' if l.group else ''}"
                f"{f' [Hash: {l.hash_code}]' if l.hash_code else ''}"
                f" (Teacher: {l.teacher_name or l.teacher_code})"
                f" Room: {l.room}"
                for l in slot.lessons
            ]
            print(f"  {slot.number:2} (Reg: {reg} | Short: {short}) | {' AND '.join(lesson_details)}")

    # print("\n--- Full Weekly Schedule JSON Structure ---")
    # print(json.dumps(schedule.to_dict(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()