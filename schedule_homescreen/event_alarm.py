import machine, ujson, utime, ugfx, badge

#Globals
alarms = []

# Management

def alarms_add(ev):
    global alarms
    
    timestamp = ev['timestamp']
    guid = ev['guid']
    title = ev['title']
    room = ev['room']
    
    alarm = {"timestamp":timestamp, "guid":guid, "title":title, "room":room}
    print("Alarm added ("+title+" in room "+room+")")
    alarms.append(alarm)
    alarms_write()
    
def alarm_exists(guid):
    global alarms
    for alarm in alarms:
        if (alarm['guid']==guid):
            return True
    return False
    
def alarms_remove(ev):
    global alarms
    alarmid=-1
    for k in range(0,len(alarms)):
        if alarms[k]['guid']==ev['guid']:
            alarmid=k
    if alarmid!=-1:
        alarms.pop(alarmid)
    
def alarms_read():
    global alarms
    try:
        f = open('event_alarms.json', 'r')
        data = f.read()
        f.close()
    except:
        data = ""
    try:
        alarms = ujson.loads(data)
    except:
        alarms = []
    
def alarms_write():
    global alarms
    data = ujson.dumps(alarms)
    f = open('event_alarms.json', 'w')
    f.write(data)
    f.close()
