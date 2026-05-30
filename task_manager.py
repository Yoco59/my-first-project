import json
import os
from datetime import datetime

FILE_NAME = "tasks.json"


def load_tasks_from_file():
    # os.path.exists בודק אם הנתיב שמסרנו לו מצביע על קובץ או תיקייה קיימים בדיסק.
    # הפונקציה מחזירה True אם הקובץ קיים, ו-False אם לא —
    # כך אנו מונעים שגיאת FileNotFoundError לפני שבכלל ניסינו לפתוח אותו.
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        print(f"📂 נטענו {len(tasks)} משימות קיימות מתוך {FILE_NAME}\n")
        return tasks
    # אם הקובץ לא נמצא — מחזירים רשימה ריקה ומתחילים מאפס
    print(f"📂 קובץ {FILE_NAME} לא נמצא — מתחיל רשימה חדשה.\n")
    return []


def save_tasks_to_file(tasks):
    # json.dump ממיר את רשימת המילונים לפורמט JSON ושופך אותה לקובץ.
    # ensure_ascii=False שומר עברית כטקסט קריא. indent=2 מעצב את הפלט.
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    print(f"✔ {len(tasks)} משימות נשמרו בהצלחה לקובץ {FILE_NAME}\n")


# טוען משימות קיימות מהקובץ (או מאתחל רשימה ריקה אם הקובץ לא קיים)
tasks = load_tasks_from_file()

print("--- מנוע המשימות האינטראקטיבי הופעל ---")
print("הקלד 'exit' בשם המשימה כדי לסיים ולראות את התוצאה הממוינת.\n")

# לולאה ראשית - תמשיך לרוץ ללא הפסקה עד שתתקבל פקודת יציאה
while True:
    task_name = input("הכנס שם משימה: ")

    # בדיקת תנאי עצירה: הפיכת הקלט לאותיות קטנות (lower) כדי לזהות גם EXIT או Exit
    if task_name.lower() == 'exit':
        # שמירה אוטומטית לפני הדפסת הדוח
        save_tasks_to_file(tasks)
        break

    # לולאה פנימית מוגנת לקליטת רמת העדיפות
    while True:
        try:
            # ניסיון להפוך את הקלט למספר שלם (Integer)
            priority = int(input("הכנס רמת עדיפות (1 - דחוף, 2 - בינוני, 3 - נמוך): "))

            # בדיקה האם המספר שהוכנס נמצא בטווח המותר (1 עד 3)
            if priority in [1, 2, 3]:
                break  # הקלט תקין! יוצאים מהלולאה הפנימית וממשיכים למשימה הבאה
            else:
                print("⚠ שגיאה: יש להזין מספר בין 1 ל-3 בלבד.")

        except ValueError:
            # מנגנון הגנה: אם המשתמש הקליד אותיות, ה-int() ייכשל והקוד יגיע לכאן במקום לקרוס
            print("⚠ חסימת שגיאה: קלט לא חוקי! נא להזין מספר (1, 2 או 3) ולא טקסט.")

    # datetime.now().isoformat() מייצר חותמת זמן תקנית בפורמט: 2026-05-30T14:35:22.123456
    tasks.append({
        "name": task_name,
        "priority": priority,
        "created_at": datetime.now().isoformat()
    })
    print(f"✔ המשימה '{task_name}' נקלטה במערכת.\n")

# שלב העיבוד והמיון - מתבצע רק לאחר היציאה מהלולאה (כשהמשתמש הקליד exit)
print("--- הפקת תוכנית עבודה ממוינת ---")
sorted_tasks = sorted(tasks, key=lambda x: x["priority"], reverse=True)

# הדפסת התוצאה הסופית בצורה ממוספרת, כולל תאריך יצירה
for index, task in enumerate(sorted_tasks, 1):
    status = "Urgent" if task["priority"] == 1 else "Medium" if task["priority"] == 2 else "Low"
    created = task.get("created_at", "לא ידוע")
    print(f"{index}. [{status}] {task['name']}  |  נוצר: {created}")
