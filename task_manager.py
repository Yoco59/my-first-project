tasks = [
    {"name": "Fix critical production bug",  "priority": 1},
    {"name": "Write unit tests",             "priority": 3},
    {"name": "Deploy security patch",        "priority": 1},
    {"name": "Update documentation",         "priority": 3},
    {"name": "Code review for new feature",  "priority": 2},
    {"name": "סגירת בנק הדואר",              "priority": 1},
    {"name": "ספורט",                         "priority": 3},
]

PRIORITY_LABELS = {1: "Urgent", 2: "Medium", 3: "Low"}

def sort_tasks(task_list):
    return sorted(task_list, key=lambda task: task["priority"])

def print_work_plan(sorted_tasks):
    print("=" * 40)
    print("       WORK PLAN — BY PRIORITY")
    print("=" * 40)
    for step, task in enumerate(sorted_tasks, start=1):
        label = PRIORITY_LABELS[task["priority"]]
        print(f"Step {step}: [{label}] {task['name']}")
    print("=" * 40)

sorted_tasks = sort_tasks(tasks)
print_work_plan(sorted_tasks)
