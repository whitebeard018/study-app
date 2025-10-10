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