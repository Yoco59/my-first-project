import json

# הגדרת רשימה ריקה לקליטת המשימות בזמן אמת
tasks = []


def save_tasks_to_file(tasks):
    # פותחים את הקובץ tasks.json לכתיבה (מצב 'w').
    # אם הקובץ לא קיים - Python ייצור אותו אוטומטית.
    # אם הקובץ כבר קיים - תוכנו יימחק ויוחלף בנתונים החדשים.
    with open("tasks.json", "w", encoding="utf-8") as f:
        # json.dump ממיר את רשימת המילונים (tasks) לפורמט JSON טקסטואלי
        # ושופך אותה ישירות לתוך אובייקט הקובץ f.
        # ensure_ascii=False מאפשר שמירה תקינה של תווים בעברית ללא קידוד אסקי.
        # indent=2 מוסיף הזחה של 2 רווחים לכל שדה — הקובץ יהיה קריא לעין אנושית.
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    print(f"✔ {len(tasks)} משימות נשמרו בהצלחה לקובץ tasks.json\n")


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
                break # הקלט תקין! יוצאים מהלולאה הפנימית וממשיכים למשימה הבאה
            else:
                print("⚠ שגיאה: יש להזין מספר בין 1 ל-3 בלבד.")

        except ValueError:
            # מנגנון הגנה: אם המשתמש הקליד אותיות, ה-int() ייכשל והקוד יגיע לכאן במקום לקרוס
            print("⚠ חסימת שגיאה: קלט לא חוקי! נא להזין מספר (1, 2 או 3) ולא טקסט.")

    # הוספת המשימה התקינה שנאספה אל מערך המשימות
    tasks.append({"name": task_name, "priority": priority})
    print(f"✔ המשימה '{task_name}' נקלטה במערכת.\n")

# שלב העיבוד והמיון - מתבצע רק לאחר היציאה מהלולאה (כשהמשתמש הקליד exit)
print("--- הפקת תוכנית עבודה ממוינת ---")
sorted_tasks = sorted(tasks, key=lambda x: x["priority"], reverse=True)

# הדפסת התוצאה הסופית בצורה ממוספרת
for index, task in enumerate(sorted_tasks, 1):
    status = "Urgent" if task["priority"] == 1 else "Medium" if task["priority"] == 2 else "Low"
    print(f"{index}. [{status}] {task['name']}")
