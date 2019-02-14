import ugfx, splash, virtualtimers
from event_schedule import event_schedule

task_active = False

def init():
    event_schedule.schedule.init()

def draw(position):
    event_schedule.schedule.showhomescreen(position)

def refreshMe():
	splash.gui_redraw = True
	return 10*60*1000

def focus(in_focus):
	global task_active, seconds
	if in_focus:
		if not task_active:
			virtualtimers.new(0, refreshMe, False)
			task_active = True
	else:
		if task_active:
			virtualtimers.delete(refreshMe)
			task_active = False

