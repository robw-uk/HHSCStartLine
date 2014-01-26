'''
Created on 23 Jan 2014

@author: MBradley
'''
from raceview import StartLineFrame
from model.race import RaceManager
from audio import AudioManager
import logging
import sys
import getopt

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
        # we use abs to turn this into a positive.
        secondsToStart = abs(aRace.deltaToStartTime().total_seconds())
        
        secondsToGun = secondsToStart - secondsBefore
        self.scheduleGun(secondsToGun * 1000)
        
         
        
    
                            
    #
    # For a sequence start, we fire the gun then schedule our other guns. We ask the race manager to
    # adjust our start seconds to reflect if we have speedup the start for testing purposes.
    #
    def handleSequenceStartedWithWarning(self):
        # fire a gun straight away
        self.fireGun()
        
        self.scheduleGunForRace(self.raceManager.races[0],
                self.raceManager.adjustedStartSeconds(300))
        
    
    def handleSequenceStartedWithoutWarning(self):
        # fire a gun straight away
        self.fireGun()
        
        self.scheduleGunsForFutureRaces()
    
    def handleGeneralRecall(self):
        self.fireGun()
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

    def __init__(self,startLineFrame,raceManager,audioManager):
        self.startLineFrame = startLineFrame
        self.raceManager = raceManager
        self.audioManager = audioManager
        self.createRaceManager()
        self.buildRaceManagerView()
        
        self.wireController()
        
    def createRaceManager(self):
        
        self.raceManager.changed.connect("raceAdded",self.handleRaceAdded)
        self.raceManager.changed.connect("raceRemoved",self.handleRaceRemoved)
        self.raceManager.changed.connect("raceChanged",self.handleRaceChanged)
        

    def wireController(self):
        self.startLineFrame.addRaceButton.config(command=self.addRaceClicked)
        self.startLineFrame.removeRaceButton.config(command=self.removeRaceClicked)
        self.startLineFrame.racesTreeView.bind("<<TreeviewSelect>>",self.raceSelectionChanged)
        self.startLineFrame.startRaceSequenceWithWarningButton.config(command=self.startRaceSequenceWithWarningClicked)
        self.startLineFrame.startRaceSequenceWithoutWarningButton.config(command=self.startRaceSequenceWithoutWarningClicked)
        self.startLineFrame.generalRecallButton.config(command=self.generalRecallClicked)
        self.startLineFrame.gunButton.config(command=self.gunClicked)
        
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
            
    def addRaceClicked(self):
        self.raceManager.createRace()
        
    def removeRaceClicked(self):#
        # check we have a selected race
        if self.selectedRace:
            self.raceManager.removeRace(self.selectedRace)
            
    def startRaceSequenceWithWarningClicked(self):
        self.raceManager.startRaceSequenceWithWarning()
    
    def startRaceSequenceWithoutWarningClicked(self):
        self.raceManager.startRaceSequenceWithoutWarning()
        
    def generalRecallClicked(self):
        self.raceManager.generalRecall()
        
    def gunClicked(self):
        self.audioManager.queueWav()
    
        
    def raceSelectionChanged(self,event):
        item = self.startLineFrame.racesTreeView.selection()[0]
        
        self.selectedRace = self.raceManager.raceWithId(item)
        
        print self.selectedRace
    
    def handleRaceAdded(self,aRace):
        self.appendRaceToTreeView(aRace)
    
    def handleRaceRemoved(self,aRace):
        self.startLineFrame.racesTreeView.delete(aRace.raceId)
    
    def handleRaceChanged(self,aRace):
        pass
    
    
    def renderDeltaToStartTime(self, aRace):
        if aRace.hasStartTime():
            return str(int(aRace.deltaToStartTime().total_seconds()))
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
    # start the controller. Every 500 milliseconds we refresh the start time and the status
    # of the race manager 
    #
    def start(self):
        self.startLineFrame.after(500, self.refreshRacesView)
        
        
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
audioManager = AudioManager("c:/Users/mbradley/workspace/HHSCStartLine/media/AirHorn.wav",app)  
screenController = ScreenController(app,raceManager,audioManager)
gunController = GunController(app, audioManager, raceManager)             
screenController.start() 
app.master.title('HHSC Race Lights')    
app.mainloop()  