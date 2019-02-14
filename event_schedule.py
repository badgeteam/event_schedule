import ugfx, badge, wifi, json, time, utime, deepsleep
import urequests as requests
from event_schedule import event_alarm
import os

callback = lambda: print("NO CALLBACK?!?!?!")

class EventGUI():

    def splitlines(self,txt,width):
        smallletters=['ijl !1t():\'.,']
        halfletters=['IJT[]']
        words=txt.split(" ")
        sentencelen=0
        sentence=""
        lines=[]
        for word in words:
            wordlen=2
            for letter in word:
                if letter in smallletters:
                    wordlen+=2
                elif letter in halfletters:
                    wordlen+=4
                else:
                    wordlen+=6
            if sentencelen+wordlen<width:
                sentencelen+=wordlen
                sentence=sentence+" "+word if len(sentence) else word
            else:
                lines+=[sentence]
                sentencelen=wordlen
                sentence=word
        lines+=[sentence]
        return lines


    def errormsg(self,title,errormsg):
        print("ERROR: %s",errormsg)
        ugfx.clear(ugfx.WHITE)
        ugfx.string(0, 0, title, "PermanentMarker22", ugfx.BLACK)
        ugfx.string(0, 25, errormsg, "Roboto_Regular12", ugfx.BLACK)
        ugfx.flush()

    def listdates(self):
        ugfx.clear(ugfx.WHITE)
        ugfx.string(0, 0, "Select Date", "Roboto_Regular12", ugfx.BLACK)
        options = ugfx.List(0,15,ugfx.width(),ugfx.height()-15*4)
        for day in sorted(self.schedule_data["days"]):
            options.add_item("%s" % self.schedule_data["days"][day])
        options.selected_index(self.dayselect)
        ugfx.string(0, ugfx.height()-45, "Right: Select   A: Alarms", "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, ugfx.height()-30, "Left: Refresh   B: Exit", "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, ugfx.height()-15, self.schedule_data['version'], "Roboto_Regular12", ugfx.BLACK)
        ugfx.flush()

    def listrooms(self):
        ugfx.clear(ugfx.WHITE)
        ugfx.string(0, 0, "Select Room", "Roboto_Regular12", ugfx.BLACK)
        options = ugfx.List(0,15,ugfx.width(),ugfx.height()-15*4)
        for room in self.rooms:
            options.add_item("%s" % room)
        options.selected_index(self.roomselect)
        ugfx.string(0, ugfx.height()-45, "Right: Select", "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, ugfx.height()-30, "Left: Days", "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, ugfx.height()-15, self.schedule_data['version'], "Roboto_Regular12", ugfx.BLACK)
        ugfx.flush()

    def showhomescreen(self,position):
        if len(sorted(self.later.keys())) and sorted(self.later.keys())[0]['timestamp'] < time.time():
            self.get_later()
        ugfx.string(5, position, "Upcoming", "Roboto_Regular18", ugfx.BLACK)
        if not len(sorted(self.later.keys())):
            ugfx.string(5, position+24, "Nothing", "Roboto_Regular18", ugfx.BLACK)
            ugfx.string(5, position+48, "Today", "Roboto_Regular18", ugfx.BLACK)
            return
        i=0
        height = 45
        for idx in sorted(self.later.keys())[0:4]:
            talk=self.later[idx]
            window= ugfx.Container(0,position+24+i*height,ugfx.width(),height)
            window.show()
            if ugfx.orientation() in [0,180]:
                window.text(3,0,talk['day']+" "+talk['start']+": "+talk['title'],ugfx.BLACK)
            else:
                window.text(3,0,talk['day']+" "+talk['start']+("    @@" if event_alarm.alarm_exists(talk['guid']) else "") ,ugfx.BLACK)
                lines = self.splitlines(talk['title'],ugfx.width()-4)
                for j in range(0,2):
                    if len(lines) > j:
                        window.text(3,12+12*j,lines[j],ugfx.BLACK)
            i+=1

    def listtalks(self):
        ugfx.clear(ugfx.WHITE)
        ugfx.string(0, 0, "Select Talk: "+self.room, "Roboto_Regular12", ugfx.BLACK)
        ugfx.set_default_font('pixelade13')
        height = int((ugfx.height()-2*30)/4)
        stringlen = int(ugfx.width() / 6)
        for i in range(0,4):
            skip=(self.talkselect - 2 if self.talkselect<len(self.talks)-2 else len(self.talks)-4) if self.talkselect > 2 else 0
            if len(self.talks)> i+skip:
                window= ugfx.Container(0,15+i*height,ugfx.width(),height)
                window.show()
                if i+skip==self.talkselect:
                    ugfx.area(0,15+i*height,ugfx.width(),height,ugfx.BLACK)
                if ugfx.orientation() in [0,180]:
                    window.text(3,0,self.schedule_data["days"][self.day]+" "+self.talks[i+skip]['start']+": "+self.talks[i+skip]['title'],ugfx.BLACK if i+skip!=self.talkselect else ugfx.WHITE)
                else:
                    window.text(3,0,self.schedule_data["days"][self.day]+" "+self.talks[i+skip]['start']+("    @@" if event_alarm.alarm_exists(self.talks[i+skip]['guid']) else ""),ugfx.BLACK if i+skip!=self.talkselect else ugfx.WHITE)
                    lines = self.splitlines(self.talks[i+skip]['title'],ugfx.width()-4)
                    for j in range(0,3):
                        if len(lines) > j:
                            window.text(3,12+12*j,lines[j],ugfx.BLACK if i+skip!=self.talkselect else ugfx.WHITE)
        ugfx.string(0, ugfx.height()-45, "Right: Select", "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, ugfx.height()-30, "Left: Rooms", "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, ugfx.height()-15, self.schedule_data['version'], "Roboto_Regular12", ugfx.BLACK)
        ugfx.flush()

    def listalarms(self):
        ugfx.clear(ugfx.WHITE)
        ugfx.string(0, 0, "Talks with alarm:", "Roboto_Regular12", ugfx.BLACK)
        ugfx.set_default_font('pixelade13')
        height = int((ugfx.height()-2*30)/4)
        stringlen = int(ugfx.width() / 6)
        for i in range(0,4):
            skip=(self.talkselect - 2 if self.talkselect<len(self.talks)-2 else len(self.talks)-4) if self.talkselect > 2 else 0
            if len(self.talks)> i+skip:
                window= ugfx.Container(0,15+i*height,ugfx.width(),height)
                window.show()
                if i+skip==self.talkselect:
                    ugfx.area(0,15+i*height,ugfx.width(),height,ugfx.BLACK)
                if ugfx.orientation() in [0,180]:
                    window.text(3,0,self.talks[i+skip]['day']+" "+self.talks[i+skip]['start']+": "+self.talks[i+skip]['title'],ugfx.BLACK if i+skip!=self.talkselect else ugfx.WHITE)
                else:
                    window.text(3,0,self.talks[i+skip]['day']+" "+self.talks[i+skip]['start']+("    @@" if event_alarm.alarm_exists(self.talks[i+skip]['guid']) else "") ,ugfx.BLACK if i+skip!=self.talkselect else ugfx.WHITE)
                    lines = self.splitlines(self.talks[i+skip]['title'],ugfx.width()-4)
                    for j in range(0,3):
                        if len(lines) > j:
                            window.text(3,12+12*j,lines[j],ugfx.BLACK if i+skip!=self.talkselect else ugfx.WHITE)
        ugfx.string(0, ugfx.height()-45, "Right: Select", "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, ugfx.height()-30, "Left: Main", "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, ugfx.height()-15, self.schedule_data['version'], "Roboto_Regular12", ugfx.BLACK)
        ugfx.flush()

    def talkdetails(self):
        ugfx.orientation(self.orientation)
        ugfx.clear(ugfx.WHITE)
        ugfx.set_default_font('pixelade13')
        height = int((ugfx.height()-2*30)/4)
        stringlen = int(ugfx.width() / 5)
        ugfx.string(0, 0, "Room: "+self.talk['room'], "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, 15, self.talk['day']+" "+self.talk['start'], "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, 30, "Duration: "+self.talk['duration'], "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, 45, "Speaker:", "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, 60,"  "+", ".join(self.details['persons']), "Roboto_Regular12", ugfx.BLACK)
        ugfx.box(0,75,ugfx.width(),ugfx.height()-75-45,ugfx.BLACK)
        for i in range(0,self.maxlines):
            if len(self.lines)>self.lineselect+i:
                ugfx.string(2, 75+i*15,self.lines[self.lineselect+i], "Roboto_Regular12", ugfx.BLACK)

        ugfx.string(0, ugfx.height()-45, "A: Remove Alarm" if event_alarm.alarm_exists(self.talk['guid']) else "A: Set Alarm", "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, ugfx.height()-30, "Left: Talks", "Roboto_Regular12", ugfx.BLACK)
        ugfx.string(0, ugfx.height()-15, self.schedule_data['version'], "Roboto_Regular12", ugfx.BLACK)

        ugfx.flush()


class EventSchedule(EventGUI):
    selected       = 0
    offset         = 500

    selected = None
    oldscreen = ""
    screen = "main"


    days = {}
    rooms = {}
    talks = {}
    
    dayselect = None
    talkselect = None
    roomselect = None
    lineselect = None

    schedule_data  = {}
    day_data = {}
    # as python does NOT sort dicts (don't trust it!) use:
    #   showindex = sorted(event_schedule.schedule.now)[0:4]
    #      ...
    #   showindex = sorted(event_schedule.schedule.later)[0:4]
    #      ...
    now = {}
    later = {}
    def get_later(self):
        self.get_now()
    def get_now(self):
        self.now = {}
        self.later = {}
        for day in self.schedule_data["days"]:
            self.day_data[day] = self.download("day/"+day+".json")
            realday=self.days[day]
            if realday == time.strftime("%Y-%m-%d"):
                roomnum=0
                timestamp=time.time()
                for room in self.day_data[day]["rooms"]:
                    roomnum +=1
                    for event in self.day_data[day]["rooms"][room]:
                        event['day']=realday
                        event['room']=room
                        if event['timestamp'] < timestamp and event['end'] > timestamp and event['type']=='lecture':
                            self.now[event['timestamp']*1000+roomnum]=event
                        elif event['timestamp'] > timestamp and event['type']=='lecture':
                            self.later[event['timestamp']*1000+roomnum]=event


    def init(self,force=False):
        if self.schedule_data != {}  and not force: return
        try:
            os.mkdir("/lib/event_schedule/event")
        except:
            pass
        try:
            os.mkdir("/lib/event_schedule/day")
        except:
            pass
        # Fuck no directories.
        try:
           os.rename('/lib/event_schedule/0.json','/lib/event_schedule/day/0.json')
        except:
            pass
        try:
           os.rename('/lib/event_schedule/1.json','/lib/event_schedule/day/1.json')
        except:
            pass
        try:
           os.rename('/lib/event_schedule/2.json','/lib/event_schedule/day/2.json')
        except:
            pass


        self.schedule_data = self.download("schedule.json")
        self.days = self.schedule_data["days"]
        self.get_now()

    def refreshschedule(self,filename):
        self.errormsg("Loading...", "WiFi: starting radio...")
        wifi.connect()
        if not wifi.wait(30,True):
            self.exitapp()
        self.errormsg("Loading...", "Downloading file...")
        try:
            data = requests.get(self.url+"schedule.json")
        except:
            self.errormsg("Error", "Could not download JSON!")
            utime.sleep(5)
            self.screen="main"
        try:
            jsondata = data.json()
        except:
            data.close()
            self.errormsg("Error", "Could not decode JSON!")
            utime.sleep(5)
            self.screen="main"
        if jsondata['version']!=self.schedule_data['version']:
            try:
                f = open("/lib/event_schedule/schedule.json","w")
                f.write(json.dumps(jsondata))
                f.close()
                self.schedule_data=jsondata
                for bestand in os.listdir('/lib/event_schedule/event'):
                    os.remove('/lib/event_schedule/event'+bestand)
                for bestand in os.listdir('/lib/event_schedule/day'):
                    os.remove('/lib/event_schedule/event'+bestand)
            except:
                pass

    def download(self,filename):
        try:
            f=open("/lib/event_schedule/"+filename,"r")
            data=f.read()
            f.close()
            return json.loads(data)
        except:
            self.errormsg("Loading...", "WiFi: starting radio...")
            wifi.connect()
            if not wifi.wait(30,True):
                self.exitapp()
            self.errormsg("Loading...", "Downloading file...")
            try:
                data = requests.get(self.url+filename)
            except:
                self.errormsg("Error", "Could not download JSON!")
                utime.sleep(5)
                self.screen="main"
            try:
                jsondata = data.json()
            except:
                data.close()
                self.errormsg("Error", "Could not decode JSON!")
                utime.sleep(5)
                self.screen="main"
            try:
                f = open("/lib/event_schedule/"+filename,"w")
                f.write(json.dumps(jsondata))
                f.close()
            except:
                pass

        data.close()
        return jsondata

    def initscreen_main(self):
        self.dayselect = 0 if self.dayselect == None else self.dayselect
    def initscreen_day(self):
        self.day = sorted(self.schedule_data['days'])[ self.dayselect ]
        self.rooms = [ room for room in self.day_data[self.day]['rooms'] ] 
        self.rooms.sort()
        self.roomselect = 0 if self.roomselect == None or self.oldscreen!="room" else self.roomselect
    def initscreen_room(self):
        self.room = self.rooms[ self.roomselect ]
        self.talks = sorted(self.day_data[self.day]['rooms'][self.room], key=lambda kv: kv['start'])
        self.talkselect = 0 if self.talkselect == None or self.oldscreen!="talk" else self.talkselect
    def initscreen_alarm(self):
        self.talks = []
        for alarm in event_alarm.alarms:
            guid=alarm['guid']
            room=alarm['room']
            for day in self.schedule_data['days'].keys():
                if room in self.day_data[day]['rooms']:
                    for talk in self.day_data[day]['rooms'][room]:
                        if talk['guid']==guid:
                            talk['day']=self.schedule_data['days'][day]
                            talk['room']=room
                            self.talks.append(talk)
        self.talkselect = 0 if self.talkselect == None or self.oldscreen!="talk" else self.talkselect

    def initscreen_talk(self):
        self.talk = self.talks[self.talkselect]
        self.talk['room'] = self.room if self.oldscreen=='room' else self.talk['room']
        self.talk['day'] = self.day if self.oldscreen=='room' else self.talk['day']
        self.details = self.download("event/"+self.talk['guid'])
        self.lineselect = 0 
        stringlen = int(ugfx.width() / 6)
        self.lines = self.splitlines(self.details['description'],ugfx.width()-4)
        self.maxlines = int((ugfx.height()-75-45)/15)

    def drawscreen(self):
        if self.oldscreen!=self.screen:
            ugfx.clear(ugfx.BLACK)
            ugfx.flush()
            getattr(self,"initscreen_"+self.screen)()
            self.previousscreen=self.oldscreen
            self.oldscreen=self.screen
        if self.screen=="main": self.listdates()
        if self.screen=="day": self.listrooms()
        if self.screen=="room": self.listtalks()
        if self.screen=="talk": self.talkdetails()
        if self.screen=="alarm": self.listalarms()
             

    def knopje(self,selected,active):
        if active:
            getattr(self,"knopje_"+self.screen)(selected)
            self.drawscreen()
    
    def setscreen(self,screen):
        self.screen=screen

    def knopje_main(self,selected):
        def up():
            self.dayselect = self.dayselect - 1 if self.dayselect > 0 else 0
        def down():
            self.dayselect = self.dayselect + 1 if self.dayselect < len(self.days)-2 else len(self.days)-1
        actions = {
                ugfx.JOY_DOWN   : lambda: down()
              , ugfx.JOY_UP     : lambda: up()
              , ugfx.JOY_LEFT   : lambda: self.refreshschedule()
              , ugfx.JOY_RIGHT  : lambda: self.setscreen("day")
              , ugfx.BTN_B      : lambda: self.exitapp()
              , ugfx.BTN_A      : lambda: self.setscreen("alarm")
        }
        if selected in actions: 
            actions[selected]()

    def knopje_day(self,selected):
        def up():
            self.roomselect = self.roomselect - 1 if self.roomselect > 0 else 0
        def down():
            self.roomselect = self.roomselect + 1 if self.roomselect < len(self.rooms)-2 else len(self.rooms)-1
        actions = {
                ugfx.JOY_DOWN   : lambda: down()
              , ugfx.JOY_UP     : lambda: up()
              , ugfx.JOY_LEFT   : lambda: self.setscreen("main")
              , ugfx.JOY_RIGHT  : lambda: self.setscreen("room")
              , ugfx.BTN_B      : lambda: self.exitapp()
        }
        if selected in actions: 
            actions[selected]()

    def knopje_room(self,selected):
        def up():
            self.talkselect = self.talkselect - 1 if self.talkselect > 0 else 0
        def down():
            self.talkselect = self.talkselect + 1 if self.talkselect < len(self.talks)-2 else len(self.talks)-1
        actions = {
                ugfx.JOY_DOWN   : lambda: down()
              , ugfx.JOY_UP     : lambda: up()
              , ugfx.JOY_LEFT   : lambda: self.setscreen("day")
              , ugfx.JOY_RIGHT  : lambda: self.setscreen("talk")
              , ugfx.BTN_B      : lambda: self.exitapp()
        }
        if selected in actions: 
            actions[selected]()

    def knopje_alarm(self,selected):
        def up():
            self.talkselect = self.talkselect - 1 if self.talkselect > 0 else 0
        def down():
            self.talkselect = self.talkselect + 1 if self.talkselect < len(self.talks)-2 else len(self.talks)-1
        actions = {
                ugfx.JOY_DOWN   : lambda: down()
              , ugfx.JOY_UP     : lambda: up()
              , ugfx.JOY_LEFT   : lambda: self.setscreen("main")
              , ugfx.JOY_RIGHT  : lambda: self.setscreen("talk")
              , ugfx.BTN_B      : lambda: self.exitapp()
        }
        if selected in actions: 
            actions[selected]()

    def knopje_talk(self,selected):
        def up():
            self.lineselect = self.lineselect - 1 if self.lineselect > 0 else 0
        def down():
            self.lineselect = self.lineselect + 1 if self.lineselect < len(self.lines)-self.maxlines else len(self.lines)-self.maxlines if len(self.lines)-self.maxlines > 0 else 0

        actions = {
                ugfx.JOY_DOWN   : lambda: down()
              , ugfx.JOY_UP     : lambda: up()
              , ugfx.JOY_LEFT   : lambda: self.setscreen( self.previousscreen)
              , ugfx.BTN_A      : lambda: event_alarm.alarms_remove(self.talk) if event_alarm.alarm_exists(self.talk['guid']) else event_alarm.alarms_add(self.talk)
              , ugfx.BTN_B      : lambda: self.exitapp()
        }
        if selected in actions: 
            actions[selected]()


    def exitapp(self):
        deepsleep.start_sleeping(1)

    def run(self):
        global callback
        event_alarm.alarms_read()
        self.callback=callback
        ugfx.init()
        ugfx.flush()
        ugfx.orientation(self.orientation)
        ugfx.flush()
        ugfx.input_attach(ugfx.JOY_RIGHT,  lambda x: self.knopje(ugfx.JOY_RIGHT ,x))
        ugfx.input_attach(ugfx.JOY_LEFT,   lambda x: self.knopje(ugfx.JOY_LEFT  ,x))
        ugfx.input_attach(ugfx.JOY_UP,     lambda x: self.knopje(ugfx.JOY_UP    ,x))
        ugfx.input_attach(ugfx.JOY_DOWN,   lambda x: self.knopje(ugfx.JOY_DOWN  ,x))
        ugfx.input_attach(ugfx.BTN_A,      lambda x: self.knopje(ugfx.BTN_A     ,x))
        ugfx.input_attach(ugfx.BTN_B,      lambda x: self.knopje(ugfx.BTN_B     ,x))
        ugfx.input_attach(ugfx.BTN_START,  lambda x: self.knopje(ugfx.BTN_START ,x))
        ugfx.input_attach(ugfx.BTN_SELECT, lambda x: self.knopje(ugfx.BTN_SELECT,x))
        self.drawscreen()



class HackerHotelSchedule(EventSchedule):
    url="https://badge.team/schedule/"
    orientation = 90


schedule=HackerHotelSchedule()
schedule.init()
schedule.run()
