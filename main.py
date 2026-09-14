import config
from timetable_parser import TimetableParser
from substitutions_parser import SubstitutionsParser

def main():
    print(f"[*] Initializing timetable parser using List URL: {config.LIST_URL}")
    tt_parser = TimetableParser()
    
    print("[*] Building dynamic teacher map...")
    tt_parser.initialize_teachers()
    print(f"[+] Parsed {len(tt_parser.teachers_map)} teachers.")
    
    print(f"\n[*] Parsing Target Class: {config.TARGET_CLASS_URL}")
    schedule = tt_parser.parse_class_timetable(config.TARGET_CLASS_URL)
    
    if not schedule:
        print("[!] Failed to parse timetable.")
        return

    print(f"\n[*] Fetching substitutions directly from URL: {config.SUBSTITUTIONS_URL}")
    sub_parser = SubstitutionsParser()
    header_info, raw_subs = sub_parser.fetch_substitutions(config.SUBSTITUTIONS_URL)
    
    if header_info:
        print(f"[+] Parsed substitutions for: {header_info.date} ({header_info.day_of_week})")
        sub_parser.apply_substitutions(schedule, header_info, raw_subs)
    else:
        print("[!] Could not fetch or parse substitutions from URL.")

    print(f"\n=== SCHEDULE FOR CLASS: {schedule.class_name} (Full Name: '{schedule.full_class_name}') ===")

    for day_name, day_schedule in schedule.days.items():
        print(f"\n--- {day_name.upper()} ---")
        
        if day_schedule.header_info:
            hi = day_schedule.header_info
            if hi.last_update:
                print(f"  [!] Substitutions for date: {hi.date} (Last update: {hi.last_update.day_of_week}, {hi.last_update.time})")
            else:
                print(f"  [!] Substitutions for date: {hi.date}")

            if hi.is_shortened:
                print("  [!] Note: Shortened lesson schedule applies.")
            for s in hi.suspensions:
                print(f"  [!] SUSPENSION: After {s.time} (after lesson period {s.after_lesson})")
            for n in hi.general_notes:
                print(f"  [i] Note: {n}")
            print("")

        if not day_schedule.slots:
            print("  No classes on this day.")
            continue

        for slot in day_schedule.slots:
            reg = f"{slot.regular_time.start}-{slot.regular_time.end}"
            short = f"{slot.shortened_time.start}-{slot.shortened_time.end}"
            
            lesson_details = []
            for l in slot.lessons:
                base_str = (
                    f"{l.subject}"
                    f"{f' [Group: {l.group}]' if l.group else ''}"
                    f" (Teacher: {l.teacher_name or l.teacher_code}) Room: {l.room}"
                )
                
                if l.substitution:
                    sub = l.substitution
                    sub_str = f" >> [SUBSTITUTION: '{sub.description}' | Substitute: {sub.substitute} | Notes: {sub.note}]"
                    base_str += sub_str
                    
                lesson_details.append(base_str)
                
            print(f"  {slot.number:2} (Reg: {reg} | Short: {short}) | {' AND '.join(lesson_details)}")

if __name__ == "__main__":
    main()