import time 
from plyer import notification

WORK_TIME = 25 * 60   # 25 minutes
BREAK_TIME = 5 * 60   # 5 minutes

class PomodoroTimer:
    def __init__(self):
        self.session_count = 0

    def start_work_session(self):
        print("Work session started.")
        time.sleep(WORK_TIME)
        self.session_count += 1
        notification.notify(title="Time's up!", message="Take a break!")

    def start_break(self):
        print("Break started.")
        time.sleep(BREAK_TIME)
        notification.notify(title="Break over!", message="Get back to work!")

    def __init__(self, work_duration=25*60, break_duration=5*60):
        self.work_duration = work_duration
        self.break_duration = break_duration
        self.session_count = 0
    

if __name__ == "__main__":
    timer = PomodoroTimer()
    while True:
        timer.start_work_session()
        timer.start_break()
