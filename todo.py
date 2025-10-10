import datetime
import json

def load_tasks(filename = "tasks.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    

def save_tasks(tasks, filename="tasks.json"):
    with open(filename, "w") as f:
        json.dump(tasks, f)

def add_task(tasks, title):
    tasks.append({"title": title, "done": False})

session_stats = {
    "session_id": 1,
    "start_time": None,
    "end_time": None,
    "tasks_completed": [],
    "total_tasks_completed": 0
}

def start_session(session_id):
    return {
        "session_id": session_id,
        "start_time": datetime.datetime.now().isoformat(),
        "end_time": None,
        "tasks_completed": [],
        "total_tasks_completed": 0
    }

def complete_task(tasks, idx, session_stats):
    tasks[idx]["done"] = True
    tasks[idx]["completed_at"] = datetime.datetime.now().isoformat()
    session_stats["tasks_completed"].append(tasks[idx]["title"])
    session_stats["total_tasks_completed"] += 1

def end_session(session_stats):
    session_stats["end_time"] = datetime.datetime.now().isoformat()

def save_session_stats(session_stats, filename="sessions.json"):
    try:
        with open(filename, "r") as f:
            all_sessions = json.load(f)
    except FileNotFoundError:
        all_sessions = []
    all_sessions.append(session_stats)
    with open(filename, "w") as f:
        json.dump(all_sessions, f)

def load_sessions(filename="sessions.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def display_session_stats():
    sessions = load_sessions()
    for sess in sessions:
        print(f"Session {sess['session_id']}:")
        print(f" Start: {sess['start_time']}")
        print(f" End: {sess['end_time']}")
        print(f" Tasks Completed: {sess['tasks_completed']}")
        print(f" Total Completed: {sess['total_tasks_completed']}\n")
