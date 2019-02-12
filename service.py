# Service file for SHA2017 event program app
# Renze Nicolai 2017

# FOR NEW API

import machine, utime, ugfx, appglue, badge, easyrtc, time

# Prepare libs
event_alarm = __import__('lib/event_schedule/event_alarm')

# Global variables
next_event_title = ""
next_event_room = ""
next_event_timestamp = 999999999999

def setup():
    alarm_notify()

def loop():
    return alarm_notify()*1000

def draw(y):
    global next_event_title
    global next_event_timestamp
    global next_event_room
    pixels_used = 0
    if (next_event_timestamp<999999999999):
        next_event_title_short = next_event_title
        
        [eY, eM, eD, ignore, ignore, ignore, ignore, ignore] = time.localtime(next_event_timestamp)
        [nY, nM, nD, ignore, ignore, ignore, ignore, ignore] = machine.RTC().datetime()
        
        showDate = True
        showTime = False
        
        #print("DEBUG: "+str(eY)+"/"+str(nY)+" "+str(eM)+"/"+str(nM)+" "+str(eD)+"/"+str(nD))
        if eY==nY and eM==nM and eD==nD:
            showDate = False
            showTime = True
        
        timestr = easyrtc.string(showDate, showTime, next_event_timestamp)
        
        if showDate:
          timestr = str(eD)+"-"+str(eM) #No year, saves space!
        
        if (len(next_event_title_short)>19):
            next_event_title_short = next_event_title_short[0:16]+"_"
        next_event_room_short = next_event_room
        if (len(next_event_room_short)>12):
            next_event_room_short = next_event_room_short[0:5]+"_"
        text = next_event_title_short+"' in "+next_event_room_short+" | "+timestr
        ypos = y-13
        badge.eink_png(0,ypos,'/lib/event_schedule/icon.png')
        ugfx.string(41, ypos+1, text, "Roboto_Regular12",ugfx.BLACK)
        pixels_used = 14
    return [60*1000, pixels_used] #Draw once per minute

def alarm_notify():
    global event_alarm
    global next_event_timestamp
    global next_event_title
    global next_event_room
            
    event_alarm.alarms_read()
    current_timestamp = utime.time()
        
    amount_of_alarms = len(event_alarm.alarms)
    
    for i in range(0, amount_of_alarms):
        alarm = event_alarm.alarms[i]
        c = int(alarm['timestamp']) - 10*60 #10 minutes before start
        if (c < current_timestamp):
            diff = c - current_timestamp
            print("[EVSCH] Alarm time reached for "+alarm['title']+" ("+str(diff)+")")
            appglue.start_app("event_schedule")
        else:
            countdown = abs(c - current_timestamp)
            print("[EVSCH] Alarm time will be reached in "+str(countdown)+" for "+alarm['title'])
            if next_event_timestamp>alarm['timestamp']:
                next_event_timestamp = alarm['timestamp']
                next_event_title = alarm['title']
                next_event_room = alarm['room']
                print("[EVSCH] Alarm over "+str(countdown)+"s: "+alarm['title']+" in "+alarm['room']+" at "+str(next_event_timestamp))
    wake_in = next_event_timestamp - current_timestamp
    if wake_in < 0:
        wake_in = 0
        
    if not next_event_timestamp == 999999999999:
        if wake_in >= 86400000:
            wake_in = 86400000-1 # Sleep one full day
        
    return wake_in