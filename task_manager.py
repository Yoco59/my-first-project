PRIORITY_LABELS = {1: "דחוף", 2: "בינוני", 3: "נמוך"}

def get_priority():
    # לולאת while מבטיחה שנחזור לשאול כל עוד הקלט לא תקין
    while True:
        raw = input("  עדיפות (1=דחוף, 2=בינוני, 3=נמוך): ")
        try:
            # try-except תופס שני סוגי שגיאות:
            # 1. קלט שאינו מספר כלל (ValueError מ-int())
            # 2. מספר מחוץ לטווח 1-3 (ValueError שאנחנו זורקים ידנית)
            priority = int(raw)
            if priority not in (1, 2, 3):
                raise ValueError
            return priority
        except ValueError:
            print(f"  ⚠  קלט שגוי '{raw}' — יש להזין 1, 2 או 3 בלבד.\n")

def collect_tasks():
    tasks = []
    print("=" * 45)
    print("   מנהל משימות — הזן משימות או 'exit' לסיום")
    print("=" * 45)

    # לולאת while True רצה ללא הגבלה עד שהמשתמש מקליד 'exit'
    while True:
        name = input("\nשם משימה (או 'exit' לסיום): ").strip()
        if name.lower() == "exit":
            break
        if not name:
            print("  ⚠  שם המשימה לא יכול להיות ריק.")
            continue
        priority = get_priority()
        tasks.append({"name": name, "priority": priority})
        print(f"  ✓  נוספה: '{name}' [{PRIORITY_LABELS[priority]}]")

    return tasks

def sort_tasks(task_list):
    return sorted(task_list, key=lambda task: task["priority"])

def print_work_plan(sorted_tasks):
    if not sorted_tasks:
        print("\nלא הוזנו משימות.")
        return
    print("\n" + "=" * 45)
    print("        תוכנית עבודה לפי עדיפות")
    print("=" * 45)
    for step, task in enumerate(sorted_tasks, start=1):
        label = PRIORITY_LABELS[task["priority"]]
        print(f"שלב {step}: [{label}] {task['name']}")
    print("=" * 45)

tasks = collect_tasks()
sorted_tasks = sort_tasks(tasks)
print_work_plan(sorted_tasks)
