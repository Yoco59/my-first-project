import json
import os
from datetime import datetime

FILE_NAME = "tasks.json"


CORRUPTED_FILE_NAME = "tasks_corrupted.json"


def load_tasks_from_file():
    # os.path.exists בודק אם הנתיב שמסרנו לו מצביע על קובץ או תיקייה קיימים בדיסק.
    # הפונקציה מחזירה True אם הקובץ קיים, ו-False אם לא —
    # כך אנו מונעים שגיאת FileNotFoundError לפני שבכלל ניסינו לפתוח אותו.
    if not os.path.exists(FILE_NAME):
        print(f"📂 קובץ {FILE_NAME} לא נמצא — מתחיל רשימה חדשה.\n")
        return []

    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            # json.load קורא את תוכן הקובץ וממיר אותו לאובייקט Python.
            # אם הקובץ הושחת (תחביר JSON שגוי), השורה הזו תזרוק JSONDecodeError.
            # אם אין הרשאת קריאה לקובץ, היא תזרוק PermissionError.
            # שתי השגיאות נתפסות בבלוק ה-except מטה — התוכנית לא תקרוס.
            tasks = json.load(f)
        print(f"📂 נטענו {len(tasks)} משימות קיימות מתוך {FILE_NAME}\n")
        return tasks

    except json.JSONDecodeError:
        # JSONDecodeError נזרקת כשמבנה ה-JSON פגום (למשל: סוגרים חסרים, פסיק עודף).
        # os.rename מגבה את הקובץ הפגום בשם חדש לפני שמאתחלים מחדש —
        # כך לא מאבדים את הנתונים המקוריים ואפשר לבדוק מה קרה מאוחר יותר.
        print(f"⚠ אזהרה: הקובץ {FILE_NAME} פגום ולא ניתן לקריאה.")
        os.rename(FILE_NAME, CORRUPTED_FILE_NAME)
        print(f"💾 הקובץ הפגום גובה אוטומטית ל-{CORRUPTED_FILE_NAME}")
        print("🔄 מאתחל רשימת משימות חדשה ונקייה...\n")
        return []

    except PermissionError:
        # PermissionError נזרקת כשלתהליך Python אין הרשאת קריאה לקובץ
        # (למשל: הקובץ נעול על ידי תוכנה אחרת, או הרשאות מערכת הפעלה שגויות).
        # במקרה זה לא מנסים לגבות — אולי גם כתיבה חסומה — פשוט מתחילים מאפס.
        print(f"⚠ אזהרה: אין הרשאת גישה לקובץ {FILE_NAME}.")
        print("🔄 מאתחל רשימת משימות חדשה ונקייה...\n")
        return []


TEMP_FILE_NAME = "tasks.tmp"


def save_tasks_to_file(tasks):
    # שלב 1: כותבים את כל המידע לקובץ זמני — לא לקובץ האמיתי.
    # אם הכתיבה תיכשל באמצע (נפילת חשמל, דיסק מלא), הקובץ המקורי tasks.json
    # נשאר שלם ולא נפגע — עדיין מכיל את הגרסה האחרונה התקינה.
    with open(TEMP_FILE_NAME, "w", encoding="utf-8") as f:
        # indent=4 מייצר JSON מסודר עם 4 רווחי הזחה — קריא יותר לעין אנושית.
        json.dump(tasks, f, ensure_ascii=False, indent=4)

    # שלב 2: os.replace מבצע החלפה אטומית ברמת מערכת ההפעלה —
    # הקובץ הזמני מוחלף בקובץ המקורי בפעולה אחת בלתי-ניתנת-לחלוקה.
    # לא קיים מצב ביניים שבו tasks.json חסר או חלקי:
    # כל קורא אחר יראה תמיד גרסה שלמה — לפני ההחלפה או אחריה.
    os.replace(TEMP_FILE_NAME, FILE_NAME)
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
