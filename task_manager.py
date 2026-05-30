import json
import logging
import os
import shutil
import time
from datetime import datetime

# ─────────────────────────────────────────────
# שכבת טלמטריה — FileHandler בלבד, ללא StreamHandler.
# כך כל הפלט הטכני הולך ישירות לדיסק ואינו מופיע בטרמינל.
# ─────────────────────────────────────────────
# system.log — שגיאות טכניות בלבד (infrastructure, I/O, exceptions)
_logger = logging.getLogger("TaskManager.System")
_logger.setLevel(logging.DEBUG)
_sys_handler = logging.FileHandler("system.log", encoding="utf-8")
_sys_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
_logger.addHandler(_sys_handler)

# audit.log — אירועים עסקיים בלבד, שורה אחת = אובייקט JSON אחד
# הפורמט %(message)s בלבד — ה-JSON עצמו מכיל את ה-timestamp
_audit_logger = logging.getLogger("TaskManager.Audit")
_audit_logger.setLevel(logging.INFO)
_audit_handler = logging.FileHandler("audit.log", encoding="utf-8")
_audit_handler.setFormatter(logging.Formatter("%(message)s"))
_audit_logger.addHandler(_audit_handler)

FILE_NAME = "tasks.json"
TEMP_FILE_NAME = "tasks.tmp"
CORRUPTED_FILE_NAME = "tasks_corrupted.json"
CONFIG_FILE = "config.json"
BACKUP_DIR = "backups"
MAX_SNAPSHOTS = 10

# ברירות מחדל — בשימוש אם config.json חסר או פגום
_DEFAULT_CONFIG = {
    "edition": "Community",
    "max_tasks_limit": 100,
    "performance_tracking": False,
}


# ─────────────────────────────────────────────
# שכבה 1 — TaskEngine: ליבת הנתונים
# אחראית אך ורק על: טעינה מדיסק, שמירה אטומית,
# והחזקת רשימת המשימות בזיכרון המנוע.
# אינה מכירה את ממשק המשתמש ואינה מכירה לוגיקה עסקית.
# ─────────────────────────────────────────────
class TaskEngine:

    def __init__(self):
        _logger.info("TaskEngine initializing — application startup")
        # קונפיגורציה נטענת ראשונה — כל שאר השכבות יסתמכו עליה
        self.config = self._load_config()
        # תיקיית הגיבויים נוצרת בהפעלה — exist_ok מונע שגיאה אם כבר קיימת
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self._tasks = self._load_from_disk()

    def _load_config(self) -> dict:
        if not os.path.exists(CONFIG_FILE):
            _logger.warning(f"TaskEngine: {CONFIG_FILE} not found — using default config")
            return dict(_DEFAULT_CONFIG)
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            _logger.info(
                f"TaskEngine: config loaded — edition={cfg.get('edition')} "
                f"max_tasks={cfg.get('max_tasks_limit')} "
                f"perf_tracking={cfg.get('performance_tracking')}"
            )
            return cfg
        except (json.JSONDecodeError, PermissionError) as exc:
            _logger.error(f"TaskEngine: failed to load {CONFIG_FILE} ({exc}) — using defaults")
            return dict(_DEFAULT_CONFIG)

    def _is_profiling(self) -> bool:
        # פרופיילינג פעיל רק ב-Enterprise עם הדגל מופעל
        return (
            self.config.get("edition") == "Enterprise"
            and self.config.get("performance_tracking", False)
        )

    def _load_from_disk(self):
        if not os.path.exists(FILE_NAME):
            _logger.info(f"TaskEngine: {FILE_NAME} not found — initializing empty task list")
            print(f"📂 קובץ {FILE_NAME} לא נמצא — מתחיל רשימה חדשה.\n")
            return []
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                # json.load ממיר את תוכן הקובץ לרשימת מילוני Python.
                # אם הקובץ פגום, JSONDecodeError תיתפס מטה.
                tasks = json.load(f)
            _logger.info(f"TaskEngine loaded {len(tasks)} tasks from {FILE_NAME}")
            print(f"📂 נטענו {len(tasks)} משימות קיימות מתוך {FILE_NAME}\n")
            return tasks
        except json.JSONDecodeError:
            _logger.error(f"TaskEngine: {FILE_NAME} is corrupted (JSONDecodeError) — backing up to {CORRUPTED_FILE_NAME}")
            print(f"⚠ אזהרה: הקובץ {FILE_NAME} פגום ולא ניתן לקריאה.")
            os.rename(FILE_NAME, CORRUPTED_FILE_NAME)
            print(f"💾 הקובץ הפגום גובה אוטומטית ל-{CORRUPTED_FILE_NAME}")
            print("🔄 מאתחל רשימת משימות חדשה ונקייה...\n")
            return []
        except PermissionError:
            _logger.error(f"TaskEngine: PermissionError reading {FILE_NAME} — initializing empty task list")
            print(f"⚠ אזהרה: אין הרשאת גישה לקובץ {FILE_NAME}.")
            print("🔄 מאתחל רשימת משימות חדשה ונקייה...\n")
            return []

    # ─── Versioned Snapshots Engine ──────────────────────────────────────────
    # כל לוגיקת הגיבויים חיה כאן בלבד — TaskService ו-CLIAppShell אינן מודעות לה.

    def _create_snapshot(self):
        """מצלם את tasks.json הנוכחי לפני כל כתיבה — כך ניתן לשחזר כל מצב קודם."""
        try:
            if not os.path.exists(FILE_NAME):
                return  # אין מה לגבות בהפעלה הראשונה
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            dest = os.path.join(BACKUP_DIR, f"tasks_{timestamp}.json")
            shutil.copy2(FILE_NAME, dest)
            _logger.info(f"TaskEngine: snapshot created — {dest}")
            self._cleanup_snapshots()
        except Exception as exc:
            # כישלון גיבוי לעולם לא יפיל את המערכת — רק יירשם ביומן
            _logger.error(f"TaskEngine: snapshot creation failed — {exc}")

    def _cleanup_snapshots(self):
        """מחיקת ה-snapshots הישנים ביותר כדי לשמור לכל היותר MAX_SNAPSHOTS קבצים."""
        try:
            files = sorted(
                f for f in os.listdir(BACKUP_DIR)
                if f.startswith("tasks_") and f.endswith(".json")
            )
            # FIFO — נמחק מהקצה הישן עד שנגיע למגבלה
            while len(files) > MAX_SNAPSHOTS:
                oldest = files.pop(0)
                os.remove(os.path.join(BACKUP_DIR, oldest))
                _logger.info(f"TaskEngine: snapshot deleted (retention policy, max={MAX_SNAPSHOTS}) — {oldest}")
        except Exception as exc:
            _logger.error(f"TaskEngine: snapshot cleanup failed — {exc}")

    def restore_snapshot(self, snapshot_file: str) -> bool:
        """מחליף את tasks.json בתמונת מצב נבחרת וטוען מחדש את הזיכרון."""
        try:
            src = os.path.join(BACKUP_DIR, snapshot_file)
            if not os.path.exists(src):
                _logger.error(f"TaskEngine: restore failed — snapshot not found: {src}")
                return False
            shutil.copy2(src, FILE_NAME)
            self._tasks = self._load_from_disk()
            _logger.info(f"TaskEngine: snapshot restored — {snapshot_file}")
            return True
        except Exception as exc:
            _logger.error(f"TaskEngine: restore failed — {exc}")
            return False

    def list_snapshots(self) -> list:
        """מחזיר רשימת שמות ה-snapshots הזמינים, ממוינת מהחדש לישן."""
        try:
            return sorted(
                (f for f in os.listdir(BACKUP_DIR)
                 if f.startswith("tasks_") and f.endswith(".json")),
                reverse=True,
            )
        except Exception:
            return []

    def save_to_disk(self):
        # שלב 1: מצלם את המצב הנוכחי לפני שנדרס — כך כל שמירה יוצרת נקודת שחזור
        self._create_snapshot()
        # שלב 2: כתיבה אטומית — קודם לקובץ זמני, ואז os.replace בפעולה אחת.
        _t0 = time.perf_counter()
        with open(TEMP_FILE_NAME, "w", encoding="utf-8") as f:
            json.dump(self._tasks, f, ensure_ascii=False, indent=4)
        os.replace(TEMP_FILE_NAME, FILE_NAME)
        elapsed_ms = (time.perf_counter() - _t0) * 1000
        _logger.info(f"TaskEngine saved {len(self._tasks)} tasks to {FILE_NAME} (atomic write) [{elapsed_ms:.3f}ms]")
        if self._is_profiling():
            print(f"  ⚡ [Enterprise] save_to_disk: {elapsed_ms:.3f}ms")

    # ─── ממשק CRUD פנימי — כל גישה לרשימה עוברת דרך כאן ─────────────────────

    def next_id(self) -> int:
        """מחזיר את ה-ID הבא — max קיים + 1, או 1 אם הרשימה ריקה."""
        if not self._tasks:
            return 1
        return max(t.get("id", 0) for t in self._tasks) + 1

    def get_all(self):
        # מחזיר עותק כדי שהשכבות החיצוניות לא ישנו את הנתונים הגולמיים ישירות
        return list(self._tasks)

    def append(self, task: dict):
        self._tasks.append(task)

    def remove_at(self, index: int):
        self._tasks.pop(index)

    def set_status(self, index: int, status: str):
        self._tasks[index]["status"] = status

    def count(self) -> int:
        return len(self._tasks)


# ─────────────────────────────────────────────
# שכבה 2 — TaskService: לוגיקה עסקית
# מתווכת בין ממשק המשתמש לבין מנוע הנתונים.
# אחראית על: מיון, בניית אובייקטי משימה, אימות קלט, ופירמוט שורות.
# מקבלת את ה-Engine כ-dependency injection — מאפשר החלפת מנוע בעתיד.
# ─────────────────────────────────────────────
class TaskService:

    PRIORITY_LABELS = {1: "Urgent", 2: "Medium", 3: "Low"}

    def __init__(self, engine: TaskEngine):
        # התקשורת עם שכבת הנתונים מתבצעת אך ורק דרך engine — לא גישה ישירה לקובץ
        self._engine = engine

    def validate_priority(self, raw: str) -> int:
        priority = int(raw)
        if priority not in (1, 2, 3):
            raise ValueError
        return priority

    def build_task(self, name: str, priority: int, task_id: int) -> dict:
        # כל לוגיקת בניית מבנה הנתונים של משימה מרוכזת כאן
        return {
            "id": task_id,
            "name": name,
            "priority": priority,
            "status": "Pending",
            "created_at": datetime.now().isoformat(),
        }

    def record_audit_event(self, event_type: str, task: dict):
        """כותב אירוע עסקי ל-audit.log בפורמט JSON קפדני — שורה אחת לאירוע.
        כישלון בכתיבה נרשם ב-system.log ולעולם לא מפיל את התוכנית."""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "event": event_type,
                "task_id": task.get("id"),
                "data": {
                    "title": task.get("name"),
                    "priority": task.get("priority"),
                    "status": task.get("status"),
                },
            }
            _audit_logger.info(json.dumps(event, ensure_ascii=False))
        except Exception as exc:
            # כישלון audit לא יפיל את המערכת — רק יירשם בלוג הטכני
            _logger.error(f"TaskService: audit logging failed for {event_type} — {exc}")

    def add(self, name: str, priority: int) -> bool:
        limit = self._engine.config.get("max_tasks_limit", 100)
        if self._engine.count() >= limit:
            # חסימת הוספה — המגבלה הוגדרה בקונפיגורציה, לא בקוד
            _logger.warning(
                f"TaskService: add blocked — reached max_tasks_limit ({limit})"
            )
            print(f"\n⛔ מגבלת המערכת: לא ניתן להוסיף יותר מ-{limit} משימות (הוגדר ב-config.json).")
            return False
        task = self.build_task(name, priority, self._engine.next_id())
        self._engine.append(task)
        _logger.info(f"TaskService: new task added — name='{name}' priority={priority}")
        self.record_audit_event("TASK_CREATED", task)
        return True

    def get_sorted(self) -> list:
        # המיון מתבצע בשכבת הלוגיקה — לא ב-UI ולא במנוע הנתונים
        _t0 = time.perf_counter()
        result = sorted(self._engine.get_all(), key=lambda t: t["priority"], reverse=True)
        elapsed_ms = (time.perf_counter() - _t0) * 1000
        if self._engine._is_profiling():
            print(f"  ⚡ [Enterprise] get_sorted ({len(result)} tasks): {elapsed_ms:.3f}ms")
        return result

    def get_for_selection(self) -> list:
        # מחזיר בסדר הקלט המקורי כדי שהאינדקס יתאים לעמדה ב-Engine
        return self._engine.get_all()

    def mark_completed(self, index: int):
        task = self._engine.get_all()[index]
        self._engine.set_status(index, "Completed")
        _logger.info(f"TaskService: task marked completed — name='{task['name']}'")
        completed_task = {**task, "status": "Completed"}
        self.record_audit_event("TASK_COMPLETED", completed_task)

    def delete(self, index: int):
        task = self._engine.get_all()[index]
        self._engine.remove_at(index)
        _logger.info(f"TaskService: task deleted — name='{task['name']}'")
        self.record_audit_event("TASK_DELETED", task)

    def save(self):
        self._engine.save_to_disk()

    def count(self) -> int:
        return self._engine.count()

    def format_line(self, position: int, task: dict) -> str:
        label = self.PRIORITY_LABELS.get(task.get("priority"), "?")
        status = task.get("status", "Pending")
        created = task.get("created_at", "לא ידוע")
        return f"{position}. [{status}] [{label}] {task.get('name', '?')}  |  נוצר: {created}"

    def format_short_line(self, position: int, task: dict) -> str:
        label = self.PRIORITY_LABELS.get(task.get("priority"), "?")
        return f"{position}. [{task.get('status', 'Pending')}] [{label}] {task.get('name', '?')}"


# ─────────────────────────────────────────────
# שכבה 3 — CLIAppShell: ממשק המשתמש
# אחראית אך ורק על: הדפסה, קריאת קלט, ולולאת האירועים הראשית.
# אינה יודעת דבר על מבנה הנתונים הפנימי —
# כל פעולה מתבצעת דרך TaskService בלבד.
# ─────────────────────────────────────────────
class CLIAppShell:

    def __init__(self, service: TaskService):
        # ה-Shell מכיר רק את ה-Service — לא את ה-Engine
        self._svc = service

    def run(self):
        count = self._svc.count()
        if count > 0:
            print(f"ברוך הבא! נטענו בהצלחה {count} משימות מהארכיון.")
        else:
            print("מערכת המשימות ריקה. אין משימות שמורות בארכיון.")
        print("--- מנוע המשימות האינטראקטיבי הופעל ---")

        edition = self._svc._engine.config.get("edition", "Community")
        limit   = self._svc._engine.config.get("max_tasks_limit")
        print(f"[ {edition} Edition | מגבלת משימות: {limit} ]")
        _logger.info(f"CLIAppShell: event loop started — edition={edition}")
        # לולאת האירועים — רצה עד שהמשתמש בוחר יציאה
        while True:
            self._show_menu()
            try:
                choice = int(input("בחר פעולה (1-5): "))
            except ValueError:
                _logger.warning("CLIAppShell: invalid menu input — non-integer entered")
                print("⚠ קלט לא חוקי — יש להקיש מספר בין 1 ל-5.")
                continue

            if   choice == 1: self._display()
            elif choice == 2: self._add()
            elif choice == 3: self._complete()
            elif choice == 4: self._delete()
            elif choice == 5: self._exit(); break
            else: print("⚠ בחירה לא חוקית — אנא בחר 1, 2, 3, 4 או 5.")

    # ─── מתודות פרטיות — כל אחת מטפלת באירוע תפריט אחד ────────────────────

    def _show_menu(self):
        print("\n=============================")
        print("   מנהל המשימות — תפריט ראשי")
        print("=============================")
        print("[1] הצגת כל המשימות")
        print("[2] הוספת משימה חדשה")
        print("[3] סימון משימה כבוצעה")
        print("[4] מחיקת משימה מהמערכת")
        print("[5] יציאה מהתוכנית")
        print("=============================")

    def _display(self):
        tasks = self._svc.get_sorted()
        if not tasks:
            print("\nאין משימות להצגה.")
            return
        print("\n--- רשימת המשימות הממוינת ---")
        for i, task in enumerate(tasks, 1):
            print(self._svc.format_line(i, task))
        input("\nלחץ Enter כדי לחזור לתפריט הראשי...")

    def _add(self):
        name = input("\nהכנס שם משימה: ").strip()
        if not name:
            print("⚠ שם המשימה לא יכול להיות ריק.")
            return
        while True:
            try:
                priority = self._svc.validate_priority(
                    input("הכנס רמת עדיפות (1 - דחוף, 2 - בינוני, 3 - נמוך): ")
                )
                break
            except ValueError:
                print("⚠ קלט לא חוקי — יש להזין 1, 2 או 3 בלבד.")
        if self._svc.add(name, priority):
            print(f"✔ המשימה '{name}' נקלטה במערכת.")

    def _complete(self):
        tasks = self._svc.get_for_selection()
        if not tasks:
            print("\nאין משימות לסימון.")
            return
        print("\n--- בחר משימה לסימון כבוצעה ---")
        for i, task in enumerate(tasks, 1):
            print(self._svc.format_short_line(i, task))
        try:
            choice = int(input("\nהקש את מספר המשימה: "))
            if 1 <= choice <= len(tasks):
                self._svc.mark_completed(choice - 1)
                print(f"✔ המשימה '{tasks[choice - 1]['name']}' סומנה כבוצעה.")
            else:
                print(f"⚠ מספר {choice} אינו קיים — יש לבחור בין 1 ל-{len(tasks)}.")
        except ValueError:
            print("⚠ קלט לא חוקי — יש להקיש מספר משימה.")

    def _delete(self):
        tasks = self._svc.get_for_selection()
        if not tasks:
            print("\nאין משימות למחיקה.")
            return
        print("\n--- בחר משימה למחיקה ---")
        for i, task in enumerate(tasks, 1):
            print(self._svc.format_short_line(i, task))
        try:
            choice = int(input("\nהקש את מספר המשימה למחיקה: "))
            if not (1 <= choice <= len(tasks)):
                print(f"⚠ מספר {choice} אינו קיים — יש לבחור בין 1 ל-{len(tasks)}.")
                return
            name = tasks[choice - 1]["name"]
            confirm = input(f"האם אתה בטוח שברצונך למחוק את '{name}'? (y/n): ").strip().lower()
            if confirm == "y":
                self._svc.delete(choice - 1)
                print(f"✔ המשימה '{name}' נמחקה מהמערכת.")
            else:
                print("המחיקה בוטלה.")
        except ValueError:
            print("⚠ קלט לא חוקי — יש להקיש מספר משימה.")

    def _exit(self):
        self._svc.save()
        _logger.info(f"CLIAppShell: application shutdown — {self._svc.count()} tasks saved")
        print(f"✔ {self._svc.count()} משימות נשמרו בהצלחה לקובץ {FILE_NAME}")
        print("להתראות!")


# ─── נקודת כניסה — מחווט את שלוש השכבות יחד ───────────────────────────────
if __name__ == "__main__":
    engine = TaskEngine()
    service = TaskService(engine)
    app = CLIAppShell(service)
    app.run()
