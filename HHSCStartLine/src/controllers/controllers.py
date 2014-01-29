'''
Created on 23 Jan 2014

@author: MBradley
'''
from screenui.raceview import StartLineFrame,AddRaceDialog
from model.race import RaceManager
from screenui.audio import AudioManager
from lightsui.hardware import LIGHT_OFF, LIGHT_ON, EasyDaqUSBRelay
import logging
import sys
import getopt
import datetime
import tkMessageBox

RACES_LIST = ['Large handicap','Small handicap','Toppers','Large and small handicap','Terras','Oppies']


#
# LightsController uses the EasyDaqUSBRelay to control the hardware lights. It refreshes the lights every
# 500 milliseconds until all races have started. 
#
class LightsController():
    
    def __init__(self, tkRoot,easyDaqRelay,raceManager):
        self.tkRoot = tkRoot
        self.easyDaqRelay = easyDaqRelay
        self.raceManager = raceManager
        # we start assuming that our lights are off
        self.currentLights = [LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF]
        self.wireController()
        
    def wireController(self):
        
        
        self.raceManager.changed.connect("generalRecall",self.handleGeneralRecall)
        self.raceManager.changed.connect("sequenceStartedWithWarning",self.handleSequenceStarted)
        self.raceManager.changed.connect("sequenceStartedWithoutWarning",self.handleSequenceStarted)
        
    
    def handleGeneralRecall(self,race):
        self.updateLights()
    
    def handleSequenceStarted(self):
        self.updateLights()
    
    def calculateLightsDisplay(self):
        #
        # out default is no lights
        lights = [LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF]
        
        # ask for the next race to start
        nextRaceToStart = self.raceManager.nextRaceToStart()
        
        # if we have a race to start
        if nextRaceToStart:
            secondsToStart = -1 * nextRaceToStart.deltaToStartTime().total_seconds()
            
            if secondsToStart <= self.raceManager.adjustedStartSeconds(300) and secondsToStart > self.raceManager.adjustedStartSeconds(240):
                lights = [LIGHT_ON, LIGHT_ON, LIGHT_ON, LIGHT_ON, LIGHT_ON]
            elif secondsToStart <= self.raceManager.adjustedStartSeconds(240) and secondsToStart > self.raceManager.adjustedStartSeconds(180):
                lights = [LIGHT_ON, LIGHT_ON, LIGHT_ON, LIGHT_ON, LIGHT_OFF]
            elif secondsToStart <= self.raceManager.adjustedStartSeconds(180) and secondsToStart > self.raceManager.adjustedStartSeconds(120): 
                lights = [LIGHT_ON, LIGHT_ON, LIGHT_ON, LIGHT_OFF, LIGHT_OFF]
            elif secondsToStart <= self.raceManager.adjustedStartSeconds(120) and secondsToStart > self.raceManager.adjustedStartSeconds(60): 
                lights = [LIGHT_ON, LIGHT_ON, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF]
            elif secondsToStart <= self.raceManager.adjustedStartSeconds(60) and secondsToStart > self.raceManager.adjustedStartSeconds(30): 
                lights = [LIGHT_ON, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF]
            elif secondsToStart <= self.raceManager.adjustedStartSeconds(30) and (secondsToStart % 2 == 0):
                lights = [LIGHT_ON, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF]
            else:
                lights = [LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF]
            
        return lights
    
    def updateLights(self):
        newLights = self.calculateLightsDisplay()
        
        if newLights != self.currentLights:
            self.easyDaqRelay.sendRelayCommand(newLights)
            self.currentLights = newLights
        
        # check that we still have a race to start, if so,
        # use the Tk event timer to call ourselves again
        if self.raceManager.nextRaceToStart():
            self.tkRoot.after(500, self.updateLights)
           
        
    def start(self):
        self.easyDaqRelay.connect()     
                
    
    
        
    
    

#
# GunController uses the AudioManager to play a Wav file as the race "gun".
# It does this in response to events from the race manager when races change
# during the start sequence or when boats finish. It uses the Tk root
# to provide an event scheduler. 
#
class GunController():
    
    def __init__(self, tkRoot, audioManager, raceManager):
        self.tkRoot = tkRoot
        self.audioManager = audioManager
        self.raceManager = raceManager
        self.scheduledGuns = []
        self.wireController()
        
    #
    # We wire the controller by registering with the race manager
    # for the events we are interested in
    #   
    def wireController(self):
        self.raceManager.changed.connect("sequenceStartedWithWarning",self.handleSequenceStartedWithWarning)
        self.raceManager.changed.connect("sequenceStartedWithoutWarning",self.handleSequenceStartedWithoutWarning)
        self.raceManager.changed.connect("generalRecall",self.handleGeneralRecall)
        
        
    def fireGun(self):
        self.audioManager.queueWav()
        
        
    def scheduleGun(self,millis):
        logging.log(logging.DEBUG,"Scheduling gun for %d " % millis)
        scheduleId = self.tkRoot.after(millis, self.fireGun)
        
        self.addSchedule(scheduleId)
        
    def addSchedule(self,scheduleId):
        self.scheduledGuns.append(scheduleId)
        
    def cancelSchedules(self):
        for aSchedule in self.scheduledGuns:
            self.tkRoot.after_cancel(aSchedule)
        self.scheduledGuns = []
        
    def scheduleGunForRace(self,aRace, secondsBefore):
        # calculate seconds to start of race
        # convert negative seconds to start to positive 
        secondsToStart = aRace.deltaToStartTime().total_seconds()  * -1
        
        
        # check that the race is still in the future (for example if we are debugging)
        if secondsToStart > 0:
            
            
            secondsToGun = secondsToStart - secondsBefore
            logging.log(logging.DEBUG,"Seconds to start: %d, seconds to gun: %d" % (secondsToStart,secondsToGun))
            self.scheduleGun(int(1000*secondsToGun ))
            
         
        
    
                            
    #
    # For a sequence start, we fire the gun then schedule our other guns. We ask the race manager to
    # adjust our start seconds to reflect if we have speedup the start for testing purposes.
    #
    def handleSequenceStartedWithWarning(self):
        # fire a gun straight away
        self.fireGun()
        
        
        self.scheduleGunForRace(self.raceManager.races[0],
                self.raceManager.adjustedStartSeconds(300))
        
        self.scheduleGunsForFutureRaces()
        
    
    def handleSequenceStartedWithoutWarning(self):
        # fire a gun straight away
        self.fireGun()
        
        self.scheduleGunsForFutureRaces()
    
    def handleGeneralRecall(self,aRace):
        self.fireGun()
        self.fireGun()
        self.cancelSchedules()
        self.scheduleGunsForFutureRaces()
    
    
    def scheduleGunsForFutureRaces(self):
        #
        # iterate over all of the races. If the race is not started, schedule the guns
        #
        for aRace in self.raceManager.races:
            if not aRace.isStarted() :
                self.scheduleGunForRace(aRace,
                                        self.raceManager.adjustedStartSeconds(240))
                self.scheduleGunForRace(aRace,
                                        self.raceManager.adjustedStartSeconds(60))
                self.scheduleGunForRace(aRace,
                                        self.raceManager.adjustedStartSeconds(0))
                
       
    
            
        
class ScreenController():
    pass

    def __init__(self,startLineFrame,raceManager,audioManager,easyDaqRelay):
        self.startLineFrame = startLineFrame
        self.raceManager = raceManager
        self.audioManager = audioManager
        self.easyDaqRelay = easyDaqRelay
        
        self.buildRaceManagerView()
        
        self.wireController()
        self.disableButtons()
        
   
    def disableButtons(self):
        self.startLineFrame.disableRemoveRaceButton()
        self.startLineFrame.disableAbandonStartRaceSequenceButton()

    def wireController(self):
        self.raceManager.changed.connect("raceAdded",self.handleRaceAdded)
        self.raceManager.changed.connect("raceRemoved",self.handleRaceRemoved)
        self.raceManager.changed.connect("raceChanged",self.handleRaceChanged)
        self.easyDaqRelay.changed.connect("connectionStateChanged",self.handleConnectionStateChanged)
        self.startLineFrame.addRaceButton.config(command=self.addRaceClicked)
        self.startLineFrame.removeRaceButton.config(command=self.removeRaceClicked)
        self.startLineFrame.racesTreeView.bind("<<TreeviewSelect>>",self.raceSelectionChanged)
        self.startLineFrame.startRaceSequenceWithWarningButton.config(command=self.startRaceSequenceWithWarningClicked)
        self.startLineFrame.startRaceSequenceWithoutWarningButton.config(command=self.startRaceSequenceWithoutWarningClicked)
        self.startLineFrame.generalRecallButton.config(command=self.generalRecallClicked)
        self.startLineFrame.gunButton.config(command=self.gunClicked)
        self.startLineFrame.abandonStartRaceSequenceButton.config(command=self.abandonStartRaceSequenceClicked)
        
    def buildRaceManagerView(self):
        # we build our tree
           
        for race in self.raceManager.races:
            self.appendRaceToTreeView(race)
    
    
    def appendRaceToTreeView(self,aRace):
        self.startLineFrame.racesTreeView.insert(
             parent="",
             index="end",
             iid = aRace.raceId,
             text = aRace.name,
             values=(self.renderDeltaToStartTime(aRace),aRace.status()))  
            
    def showAddRaceDialog(self):
        dlg = AddRaceDialog(self.startLineFrame,RACES_LIST)
        # ... build the window ...
        
        ## Set the focus on dialog window (needed on Windows)
        dlg.top.focus_set()
        ## Make sure events only go to our dialog
        dlg.top.grab_set()
        ## Make sure dialog stays on top of its parent window (if needed)
        dlg.top.transient(self.startLineFrame)
        # set the position to be relative to the parent
        dlg.top.geometry("+%d+%d" % (self.startLineFrame.winfo_rootx()+50,
                                  self.startLineFrame.winfo_rooty()+50))
        ## Display the window and wait for it to close
        dlg.top.wait_window()
        return dlg.raceName
    
    def addRaceClicked(self):
        raceName = self.showAddRaceDialog()
        
        if raceName:
            self.raceManager.createRace(raceName)
        
    def removeRaceClicked(self):#
        # check we have a selected race
        if self.selectedRace:
            self.raceManager.removeRace(self.selectedRace)
            
    def startRaceSequenceWithWarningClicked(self):
        self.raceManager.startRaceSequenceWithWarning()
        self.startLineFrame.disableAddRaceButton()
        self.startLineFrame.disableRemoveRaceButton()
        self.startLineFrame.disableStartRaceSequenceWithWarningButton()
        self.startLineFrame.disableStartRaceSequenceWithoutWarningButton()
        self.startLineFrame.enableAbandonStartRaceSequenceButton()
    
    def startRaceSequenceWithoutWarningClicked(self):
        self.raceManager.startRaceSequenceWithoutWarning()
        self.startLineFrame.disableAddRaceButton()
        self.startLineFrame.disableRemoveRaceButton()
        self.startLineFrame.disableStartRaceSequenceWithWarningButton()
        self.startLineFrame.disableStartRaceSequenceWithoutWarningButton()
        self.startLineFrame.enableAbandonStartRaceSequenceButton()
        
    def generalRecallClicked(self):
        result = tkMessageBox.askquestion("General Recall","Are you sure?", icon="warning")
        if result == 'yes':
            self.raceManager.generalRecall()
        
    def gunClicked(self):
        self.audioManager.queueWav()


    def abandonStartRaceSequenceClicked(self):
        result = tkMessageBox.askquestion("Abandon race sequence","Are you sure?", icon="warning")
        if result == 'yes':
            self.raceManager.abandonStartSequence()
            self.startLineFrame.disableGeneralRecallButton()
            self.startLineFrame.disableAbandonStartRaceSequenceButton()
            self.startLineFrame.enableAddRaceButton()
            self.startLineFrame.enableRemoveRaceButton()
            self.startLineFrame.enableStartRaceSequenceWithoutWarningButton()
            self.startLineFrame.enableStartRaceSequenceWithWarningButton()
            
        
    def raceSelectionChanged(self,event):
        item = self.startLineFrame.racesTreeView.selection()[0]
        
        self.selectedRace = self.raceManager.raceWithId(item)
        
        print self.selectedRace
    
    def handleRaceAdded(self,aRace):
        self.appendRaceToTreeView(aRace)
        self.startLineFrame.enableRemoveRaceButton()
        self.startLineFrame.enableStartRaceSequenceWithoutWarningButton()
        self.startLineFrame.enableStartRaceSequenceWithWarningButton()
    
    def handleRaceRemoved(self,aRace):
        self.startLineFrame.racesTreeView.delete(aRace.raceId)
        if not self.raceManager.isEmpty():
            self.startLineFrame.disableStartRaceSequenceWithoutWarningButton()
            self.startLineFrame.disableStartRaceSequenceWithWarningButton()
    
    def handleRaceChanged(self,aRace):
        pass
    
    #
    # event handler for the connection state of the easyDaqRelay changing
    #
    def handleConnectionStateChanged(self,state):
        # update the Tk string variable with the session state description
        # from the EasyDaq relay object
        self.startLineFrame.connectionStatus.set(self.easyDaqRelay.sessionStateDescription())
    
    
    def renderDeltaToStartTime(self, aRace):
        if aRace.hasStartTime():
            deltaToStartTimeSeconds = int(aRace.deltaToStartTime().total_seconds())
            
            hmsString = str(datetime.timedelta(seconds=(abs(deltaToStartTimeSeconds))))
            
            if deltaToStartTimeSeconds < 0:
                return "-" +  hmsString 
            else:
                return hmsString
        
        else:
            return "-"
        
    
    def refreshRacesView(self):
        #
        # iterate over all of our races. Read the start time delta and
        # and status, and update the racesTreeView with their values
        #
        
        for aRace in self.raceManager.races:
            
            self.startLineFrame.racesTreeView.item(
                        aRace.raceId,
                        
                        values=[self.renderDeltaToStartTime(aRace), aRace.status()])
        
        self.startLineFrame.after(200, self.refreshRacesView)
        
        #
        # Ask our race manager if we have a started race
        #
        if self.raceManager.hasStartedRace():
            self.startLineFrame.enableGeneralRecallButton()
        else:
            self.startLineFrame.disableGeneralRecallButton()
            
    
    
    
    
    #
    # start the controller. Every 500 milliseconds we refresh the start time and the status
    # of the race manager 
    #
    def start(self):
        self.startLineFrame.after(500, self.refreshRacesView)
        
logging.basicConfig(level=logging.DEBUG,
    format = "%(levelname)s:%(asctime)-15s %(message)s")
        
logging.debug(sys.argv)
myopts, args = getopt.getopt(sys.argv[1:],"p:t:",["port=","testSpeedRatio="])        

for o, a in myopts:
    logging.debug("Option %s value %s" % (o,a))
    if o in ('-p','--port'):
        comPort=a
    elif o in ('-t','--testSpeedRatio'):
        testSpeedRatio=int(a)
    else:
        print("Usage: %s -p [serial port to connect to] -t [default 1, set to more than 1 to run faster]" % sys.argv[0])
        
app = StartLineFrame()  
raceManager = RaceManager()     
easyDaqRelay = EasyDaqUSBRelay(comPort, app)
audioManager = AudioManager("c:/Users/mbradley/workspace/HHSCStartLine/media/beep.wav",app)  
screenController = ScreenController(app,raceManager,audioManager,easyDaqRelay)
gunController = GunController(app, audioManager, raceManager)
lightsController = LightsController(app, easyDaqRelay, raceManager)             
screenController.start() 
lightsController.start()
app.master.title('HHSC Race Lights')    
app.mainloop()  