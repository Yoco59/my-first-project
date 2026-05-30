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

# הודעת פתיחה חכמה — len() מחזיר את מספר הפריטים ברשימה
if len(tasks) > 0:
    print(f"ברוך הבא! נטענו בהצלחה {len(tasks)} משימות מהארכיון.")
else:
    print("מערכת המשימות ריקה. אין משימות שמורות בארכיון.")

def show_menu():
    print("\n=============================")
    print("   מנהל המשימות — תפריט ראשי")
    print("=============================")
    print("[1] הצגת כל המשימות")
    print("[2] הוספת משימה חדשה")
    print("[3] סימון משימה כבוצעה")
    print("[4] מחיקת משימה מהמערכת")
    print("[5] יציאה מהתוכנית")
    print("=============================")


def display_tasks(tasks):
    if not tasks:
        print("\nאין משימות להצגה.")
        return
    print("\n--- רשימת המשימות הממוינת ---")
    sorted_tasks = sorted(tasks, key=lambda x: x["priority"], reverse=True)
    for index, task in enumerate(sorted_tasks, 1):
        priority_label = "Urgent" if task["priority"] == 1 else "Medium" if task["priority"] == 2 else "Low"
        status = task.get("status", "Pending")
        created = task.get("created_at", "לא ידוע")
        print(f"{index}. [{status}] [{priority_label}] {task['name']}  |  נוצר: {created}")
    input("\nלחץ Enter כדי לחזור לתפריט הראשי...")


def complete_task(tasks):
    if not tasks:
        print("\nאין משימות לסימון.")
        return
    print("\n--- בחר משימה לסימון כבוצעה ---")
    for index, task in enumerate(tasks, 1):
        priority_label = "Urgent" if task["priority"] == 1 else "Medium" if task["priority"] == 2 else "Low"
        print(f"{index}. [{task.get('status', 'Pending')}] [{priority_label}] {task['name']}")
    try:
        choice = int(input("\nהקש את מספר המשימה: "))
        # בדיקת טווח: המספר חייב להיות בין 1 לאורך הרשימה
        if 1 <= choice <= len(tasks):
            tasks[choice - 1]["status"] = "Completed"
            print(f"✔ המשימה '{tasks[choice - 1]['name']}' סומנה כבוצעה.")
        else:
            print(f"⚠ מספר {choice} אינו קיים ברשימה — יש לבחור בין 1 ל-{len(tasks)}.")
    except ValueError:
        # מונע קריסה אם המשתמש הקליד טקסט במקום מספר
        print("⚠ קלט לא חוקי — יש להקיש מספר משימה.")


def delete_task(tasks):
    if not tasks:
        print("\nאין משימות למחיקה.")
        return
    print("\n--- בחר משימה למחיקה ---")
    for index, task in enumerate(tasks, 1):
        priority_label = "Urgent" if task["priority"] == 1 else "Medium" if task["priority"] == 2 else "Low"
        print(f"{index}. [{task.get('status', 'Pending')}] [{priority_label}] {task['name']}")
    try:
        choice = int(input("\nהקש את מספר המשימה למחיקה: "))
        if not (1 <= choice <= len(tasks)):
            print(f"⚠ מספר {choice} אינו קיים — יש לבחור בין 1 ל-{len(tasks)}.")
            return
        task_name = tasks[choice - 1]["name"]
        confirm = input(f"האם אתה בטוח שברצונך למחוק את '{task_name}'? (y/n): ").strip().lower()
        if confirm == "y":
            tasks.pop(choice - 1)
            print(f"✔ המשימה '{task_name}' נמחקה מהמערכת.")
        else:
            print("המחיקה בוטלה.")
    except ValueError:
        print("⚠ קלט לא חוקי — יש להקיש מספר משימה.")


def add_task(tasks):
    task_name = input("\nהכנס שם משימה: ").strip()
    if not task_name:
        print("⚠ שם המשימה לא יכול להיות ריק.")
        return

    # לולאה פנימית מוגנת לקליטת רמת העדיפות
    while True:
        try:
            priority = int(input("הכנס רמת עדיפות (1 - דחוף, 2 - בינוני, 3 - נמוך): "))
            if priority in [1, 2, 3]:
                break
            else:
                print("⚠ שגיאה: יש להזין מספר בין 1 ל-3 בלבד.")
        except ValueError:
            # מנגנון הגנה: אם המשתמש הקליד אותיות, ה-int() ייכשל והקוד יגיע לכאן במקום לקרוס
            print("⚠ חסימת שגיאה: קלט לא חוקי! נא להזין מספר (1, 2 או 3) ולא טקסט.")

    # datetime.now().isoformat() מייצר חותמת זמן תקנית בפורמט: 2026-05-30T14:35:22.123456
    tasks.append({
        "name": task_name,
        "priority": priority,
        "status": "Pending",
        "created_at": datetime.now().isoformat()
    })
    print(f"✔ המשימה '{task_name}' נקלטה במערכת.")


print("--- מנוע המשימות האינטראקטיבי הופעל ---")

# לולאה ראשית — רצה ללא הפסקה ומציגה תפריט בכל סיבוב עד שהמשתמש בוחר יציאה
while True:
    show_menu()
    try:
        # try-except מגן מפני קלט שאינו מספר כלל (אות, רווח, Enter ריק)
        # ללא הגנה זו, int() היה קורס עם ValueError ומסיים את התוכנית
        choice = int(input("בחר פעולה (1-3): "))
    except ValueError:
        print("⚠ קלט לא חוקי — יש להקיש מספר בין 1 ל-3.")
        continue  # חוזרים לתחילת הלולאה ומציגים את התפריט מחדש

    if choice == 1:
        display_tasks(tasks)
    elif choice == 2:
        add_task(tasks)
    elif choice == 3:
        complete_task(tasks)
    elif choice == 4:
        delete_task(tasks)
    elif choice == 5:
        save_tasks_to_file(tasks)
        print("להתראות!")
        break
    else:
        print("⚠ בחירה לא חוקית — אנא בחר 1, 2, 3, 4 או 5.")
