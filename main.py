import sys

from pcr.timer import PCRTimer
from pcr.task import PCRTask

from ui import main_ui as ui

if __name__=="__main__":
    # PCR Task
    pcr_task = PCRTask.instance(ui.window)

    # PCR Task(timer)
    pcr_timer = PCRTimer()
    pcr_timer.start()

    # Start main ui
    ui.app.exec()

    pcr_task.optic.close()

    # Exit process
    sys.exit()
