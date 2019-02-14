import ugfx, splash, virtualtimers
from eventschedule_on_homescreen import eventschedule_on_homescreen

task_active = False

def init():
    eventschedule_on_homescreen.schedule.init()

def draw(position):
    eventschedule_on_homescreen.schedule.homescreen(position)

def focus(in_focus):
	global task_active, seconds
	print("Focus changed to", in_focus)
	if in_focus:
		if not task_active:
			virtualtimers.new(0, refreshMe, False)
			task_active = True
	else:
		if task_active:
			virtualtimers.delete(refeshMe)
			task_active = False

def refreshMe():
	splash.gui_redraw = True
	return 10*60*1000
