import ugfx, badge, wifi, json, time, utime, deepsleep
import urequests as requests
from eventschedule_on_homescreen import event_alarm
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
    #   showindex = sorted(eventschedule_on_homescreen.schedule.now)[0:4]
    #      ...
    #   showindex = sorted(eventschedule_on_homescreen.schedule.later)[0:4]
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
            os.mkdir("/lib/eventschedule_on_homescreen/event")
        except:
            pass
        try:
            os.mkdir("/lib/eventschedule_on_homescreen/day")
        except:
            pass
        # Fuck no directories.
        try:
           os.rename('/lib/eventschedule_on_homescreen/0.json','/lib/eventschedule_on_homescreen/day/0.json')
        except:
            pass
        try:
           os.rename('/lib/eventschedule_on_homescreen/1.json','/lib/eventschedule_on_homescreen/day/1.json')
        except:
            pass
        try:
           os.rename('/lib/eventschedule_on_homescreen/2.json','/lib/eventschedule_on_homescreen/day/2.json')
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
                f = open("/lib/eventschedule_on_homescreen/schedule.json","w")
                f.write(json.dumps(jsondata))
                f.close()
                self.schedule_data=jsondata
                for bestand in os.listdir('/lib/eventschedule_on_homescreen/event'):
                    os.remove('/lib/eventschedule_on_homescreen/event'+bestand)
                for bestand in os.listdir('/lib/eventschedule_on_homescreen/day'):
                    os.remove('/lib/eventschedule_on_homescreen/event'+bestand)
            except:
                pass

    def download(self,filename):
        try:
            f=open("/lib/eventschedule_on_homescreen/"+filename,"r")
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
                f = open("/lib/eventschedule_on_homescreen/"+filename,"w")
                f.write(json.dumps(jsondata))
                f.close()
            except:
                pass

        data.close()
        return jsondata

    def exitapp(self):
        deepsleep.start_sleeping(1)

class HackerHotelSchedule(EventSchedule):
    url="https://badge.team/schedule/"
    orientation = 90


schedule=HackerHotelSchedule()
schedule.init()
