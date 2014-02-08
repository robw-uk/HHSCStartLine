'''
Created on 23 Jan 2014

@author: MBradley
'''
from screenui.raceview import StartLineFrame,AddFleetDialog
from model.race import RaceManager
from screenui.audio import AudioManager

import logging
import sys
import getopt
import datetime
import tkMessageBox
import Tkinter

RACES_LIST = ['Large handicap','Small handicap','Toppers','Large and small handicap','Teras','Oppies']


#
# LightsController uses the EasyDaqUSBRelay to control the hardware lights. It refreshes the lights every
# 500 milliseconds until all fleets have started. 
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
        self.raceManager.changed.connect("startSequenceAbandoned",self.handleStartSequenceAbandoned)
        
        
        
    
    def handleGeneralRecall(self,fleet):
        self.updateLights()
    
    def handleSequenceStarted(self):
        self.updateLights()
        
    def handleStartSequenceAbandoned(self):
        self.updateLights()
    
    def calculateLightsDisplay(self):
        #
        # out default is no lights
        lights = [LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF]
        
        # ask for the next fleet to start
        nextFleetToStart = self.raceManager.nextFleetToStart()
        
        # if we have a fleet to start
        if nextFleetToStart:
            secondsToStart = -1 * nextFleetToStart.adjustedDeltaSecondsToStartTime()
            
            if secondsToStart <=300 and secondsToStart > 240:
                lights = [LIGHT_ON, LIGHT_ON, LIGHT_ON, LIGHT_ON, LIGHT_ON]
            elif secondsToStart <= 240 and secondsToStart > 180:
                lights = [LIGHT_ON, LIGHT_ON, LIGHT_ON, LIGHT_ON, LIGHT_OFF]
            elif secondsToStart <= 180 and secondsToStart > 120: 
                lights = [LIGHT_ON, LIGHT_ON, LIGHT_ON, LIGHT_OFF, LIGHT_OFF]
            elif secondsToStart <= 120and secondsToStart > 60: 
                lights = [LIGHT_ON, LIGHT_ON, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF]
            elif secondsToStart <= 60 and secondsToStart > 30: 
                lights = [LIGHT_ON, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF]
            elif secondsToStart <= 30 and (secondsToStart % 2 == 0):
                lights = [LIGHT_ON, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF]
            else:
                lights = [LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF, LIGHT_OFF]
            
        return lights
    
    def updateLights(self):
        newLights = self.calculateLightsDisplay()
        
        if newLights != self.currentLights:
            self.easyDaqRelay.sendRelayCommand(newLights)
            self.currentLights = newLights
        
        # check that we still have a fleet to start, if so,
        # use the Tk event timer to call ourselves again
        if self.raceManager.nextFleetToStart():
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
        self.raceManager.changed.connect("startSequenceAbandoned",self.handleStartSequenceAbandoned)
        self.raceManager.changed.connect("finishAdded", self.handleFinishAdded)
        
        
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
        
    def scheduleGunForFleetStart(self,aFleet, secondsBefore):
        # calculate seconds to start of fleet
        # convert negative seconds to start to positive 
        secondsToStart = aFleet.deltaSecondsToStartTime()  * -1
        
        
        # check that the fleet is still in the future (for example if we are debugging)
        if secondsToStart > 0:
            
            #
            # to calculate the seconds to gun, we take the seconds to start 
            # and subtract the requested seconds before divided by the test speed ratio.
            #
            # For example, with a test speed ratio of 5, the seconds to start for the
            # first race with an F flag start will be 600  / 5 = 120 seconds.
            #
            # For the five minute (300 seconds) gun, the calculation is:
            # 120 - (300/5) = 60 seconds.
            #
            # For the four minute gun (240 seconds) gun, the calculation is:
            # 120 - (240/5) = 72 seconds
            #
            secondsToGun = secondsToStart - secondsBefore / RaceManager.testSpeedRatio
            logging.info("Seconds to start: %d, scheduling gun for %d seconds" % (secondsToStart,secondsToGun))
            self.scheduleGun(int(1000*secondsToGun ))
            
         
        
    
                            
    #
    # For a sequence start, we fire the gun then schedule our other guns. We ask the race manager to
    # adjust our start seconds to reflect if we have speedup the start for testing purposes.
    #
    def handleSequenceStartedWithWarning(self):
        # fire a gun straight away
        self.fireGun()
        
        
        self.scheduleGunForFleetStart(self.raceManager.fleets[0],300)
        
        self.scheduleGunsForFutureFleetStarts()
        
    def handleFinishAdded(self,aFinish):
        self.fireGun()
    
    def handleSequenceStartedWithoutWarning(self):
        # fire a gun straight away
        self.fireGun()
        
        self.scheduleGunsForFutureFleetStarts()
    
    def handleGeneralRecall(self,aFleet):
        self.fireGun()
        self.fireGun()
        self.cancelSchedules()
        self.scheduleGunsForFutureFleetStarts()
        
    def handleStartSequenceAbandoned(self):
        self.cancelSchedules()
    
    
    def scheduleGunsForFutureFleetStarts(self):
        #
        # iterate over all of the fleet. If the fleet is not started, schedule the guns
        #
        for aFleet in self.raceManager.fleets:
            if not aFleet.isStarted() :
                self.scheduleGunForFleetStart(aFleet,240)
                self.scheduleGunForFleetStart(aFleet,60)
                self.scheduleGunForFleetStart(aFleet,0)
                
       
    
            
        
class ScreenController():
    pass

    def __init__(self,startLineFrame,raceManager,audioManager,easyDaqRelay):
        self.startLineFrame = startLineFrame
        self.raceManager = raceManager
        self.audioManager = audioManager
        self.easyDaqRelay = easyDaqRelay
        self.selectedFleet = None    
        
        self.buildFleetManagerView()
        
        
        self.wireController()
        self.disableButtons()
        
   
    def disableButtons(self):
        self.startLineFrame.disableRemoveFleetButton()
        self.startLineFrame.disableAbandonStartRaceSequenceButton()

    def wireController(self):
        self.raceManager.changed.connect("fleetAdded",self.handleFleetAdded)
        self.raceManager.changed.connect("fleetRemoved",self.handleFleetRemoved)
        self.raceManager.changed.connect("fleetChanged",self.handleFleetChanged)
        self.raceManager.changed.connect("finishAdded",self.handleFinishAdded)
        self.easyDaqRelay.changed.connect("connectionStateChanged",self.handleConnectionStateChanged)
        self.audioManager.changed.connect("playRequestQueueChanged",self.handleGunQueueChanged)
        self.startLineFrame.addFleetButton.config(command=self.addFleetClicked)
        self.startLineFrame.removeFleetButton.config(command=self.removeFleetClicked)
        self.startLineFrame.fleetsTreeView.bind("<<TreeviewSelect>>",self.fleetSelectionChanged)
        self.startLineFrame.startRaceSequenceWithWarningButton.config(command=self.startRaceSequenceWithWarningClicked)
        self.startLineFrame.startRaceSequenceWithoutWarningButton.config(command=self.startRaceSequenceWithoutWarningClicked)
        self.startLineFrame.generalRecallButton.config(command=self.generalRecallClicked)
        self.startLineFrame.gunButton.config(command=self.gunClicked)
        self.startLineFrame.gunAndFinishButton.config(command=self.gunAndFinishClicked)
        self.startLineFrame.abandonStartRaceSequenceButton.config(command=self.abandonStartRaceSequenceClicked)
        
        
        
    def buildFleetManagerView(self):
        # we build our tree
           
        for fleet in self.raceManager.fleets:
            self.appendFleetToTreeView(fleet)
    
    
    def appendFleetToTreeView(self,aFleet):
        self.startLineFrame.fleetsTreeView.insert(
             parent="",
             index="end",
             iid = aFleet.fleetId,
             text = aFleet.name,
             values=(self.renderDeltaToStartTime(aFleet),aFleet.status()))  
            
    def showAddFleetDialog(self):
        dlg = AddFleetDialog(self.startLineFrame,RACES_LIST)
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
        return dlg.fleetName
    
    def addFleetClicked(self):
        fleetName = self.showAddFleetDialog()
        
        if fleetName:
            self.raceManager.createFleet(fleetName)
        self.updateButtonStates()
        
    def removeFleetClicked(self):#
        # check we have a selected fleet
        if self.selectedFleet:
            self.raceManager.removeFleet(self.selectedFleet)
        self.updateButtonStates()
            
    def startRaceSequenceWithWarningClicked(self):
        self.raceManager.startRaceSequenceWithWarning()
        self.updateButtonStates()
        
    
    def startRaceSequenceWithoutWarningClicked(self):
        self.raceManager.startRaceSequenceWithoutWarning()
        self.updateButtonStates()
        
        
    def generalRecallClicked(self):
        result = tkMessageBox.askquestion("General Recall","Are you sure?", icon="warning")
        if result == 'yes':
            self.raceManager.generalRecall()
        self.updateButtonStates()
        
    def gunClicked(self):
        self.audioManager.queueWav()


    def abandonStartRaceSequenceClicked(self):
        result = tkMessageBox.askquestion("Abandon race sequence","Are you sure?", icon="warning")
        if result == 'yes':
            self.raceManager.abandonStartSequence()
        self.updateButtonStates()
           
        
    def fleetSelectionChanged(self,event):
        item = self.startLineFrame.fleetsTreeView.selection()[0]
        
        self.selectedFleet = self.raceManager.fleetWithId(item)
        
        logging.debug("User has selected %s" % str(self.selectedFleet))
        self.updateButtonStates()
        
    def gunAndFinishClicked(self):
        self.raceManager.createFinish()
    
    def handleFleetAdded(self,aFleet):
        self.appendFleetToTreeView(aFleet)
        self.updateButtonStates()
        
    
    def handleFleetRemoved(self,aFleet):
        self.startLineFrame.fleetsTreeView.delete(aFleet.fleetId)
        self.selectedFleet=None
        self.updateButtonStates()
    
    
    def handleFleetChanged(self,aFleet):
        pass
    
    def handleFinishAdded(self,aFinish):
        self.appendFinishToFinishTreeView(aFinish)
    
    
    def buildFinishView(self):
        # we build our tree
           
        for finish in self.raceManager.finishes:
            self.appendFinishToFinishTreeView(finish)
    
    #
    
    #
    def appendFinishToFinishTreeView(self,aFinish):
        finishItem = self.startLineFrame.finishTreeView.insert(
             parent="",
             index="end",
             iid = aFinish.finishId,
             text = self.renderFinishTime(aFinish),
             values=(self.renderFinishFleet(aFinish),self.renderFinishElapsedTime(aFinish)))
        logging.info("Asking finish treeView to see "+str(finishItem))
        self.startLineFrame.finishTreeView.see(finishItem)
        
    #
    # Render the fleet of a finish
    #
    def renderFinishFleet(self,aFinish):
        # if our finish has a fleet, return the name of the fleet
        if aFinish.fleet:
            return aFinish.fleet.name
        else:
            return "-"
        
    #
    # Render the finish time. This is the clock time of the finish
    #
    def renderFinishTime(self,finish):
        return finish.finishTime.strftime("%H:%M:%S")
    
    def renderFinishElapsedTime(self,finish):
        # if we have a fleet, calculate the delta from the finish time to the 
        # start time of the fleet.
        if finish.hasFleet():
            return finish.elapsedFinishTime().strftime("%H:%M:%S")
        #
        # if we don't have a fleet, we can't calculate the elapsed time
        #
        else:
        
            return "-"
        
            
    #
    # event handler for the connection state of the easyDaqRelay changing
    #
    def handleConnectionStateChanged(self,state):
        # update the Tk string variable with the session state description
        # from the EasyDaq relay object
        self.startLineFrame.connectionStatus.set(self.easyDaqRelay.sessionStateDescription())
    
    
    def renderDeltaToStartTime(self, aFleet):
        if aFleet.hasStartTime():
            deltaToStartTimeSeconds = int(aFleet.adjustedDeltaSecondsToStartTime())
            
            hmsString = str(datetime.timedelta(seconds=(abs(deltaToStartTimeSeconds))))
            
            if deltaToStartTimeSeconds < 0:
                return "-" +  hmsString 
            else:
                return hmsString
        
        else:
            return "-"
        
    
    def refreshFleetsView(self):
        #
        # iterate over all of our fleets. Read the start time delta and
        # and status, and update the fleetsTreeView with their values
        #
        
        for aFleet in self.raceManager.fleets:
            
            self.startLineFrame.fleetsTreeView.item(
                        aFleet.fleetId,
                        
                        values=[self.renderDeltaToStartTime(aFleet), aFleet.status()])
        
       
        
        #
        # Ask our race manager if we have a started fleet
        #
        if self.raceManager.hasStartedFleet():
            self.startLineFrame.enableGeneralRecallButton()
        else:
            self.startLineFrame.disableGeneralRecallButton()
            
                  
        #
        # Update our clock
        #
        self.startLineFrame.clockStringVar.set(datetime.datetime.now().strftime("%H:%M:%S"))
    
        #
        # Schedule to update this view again in 250 milliseonds
        #
        self.startLineFrame.after(250, self.refreshFleetsView)
    
    
    #
    # This method enables and disables buttons. Call it after handling a button event
    #
    def updateButtonStates(self):
        #
        # Logic for enabling and disabling buttons
        #   
        if self.raceManager.hasSequenceStarted() or self.raceManager.hasStartedFleet(): 
            
            self.startLineFrame.enableAbandonStartRaceSequenceButton()
            self.startLineFrame.disableAddFleetButton()
            self.startLineFrame.disableRemoveFleetButton()
            self.startLineFrame.disableStartRaceSequenceWithoutWarningButton()
            self.startLineFrame.disableStartRaceSequenceWithWarningButton()
        else:
            self.startLineFrame.enableAddFleetButton()
            self.startLineFrame.disableAbandonStartRaceSequenceButton()
            
            
            if self.raceManager.hasFleets():
            
            
                
                self.startLineFrame.enableStartRaceSequenceWithoutWarningButton()
                self.startLineFrame.enableStartRaceSequenceWithWarningButton()
                if self.selectedFleet:
                    self.startLineFrame.enableRemoveFleetButton()
                else:
                    self.startLineFrame.disableRemoveFleetButton()
            else:
                self.startLineFrame.disableRemoveFleetButton()
                self.startLineFrame.disableStartRaceSequenceWithoutWarningButton()
                self.startLineFrame.disableStartRaceSequenceWithWarningButton()
  
    
    #
    # start the controller. Every 500 milliseconds we refresh the start time and the status
    # of the race manager 
    #
    def start(self):
        self.startLineFrame.after(500, self.refreshFleetsView)
        
    #
    # The gun queue has changed. Update the UI to show the length of the gun queue
    #
    def handleGunQueueChanged(self,gunQueueCount):
        self.startLineFrame.gunQueueCount.set("Gun Q: " + str(gunQueueCount))
        
        
logging.basicConfig(level=logging.INFO,
    format = "%(levelname)s:%(asctime)-15s %(message)s")
        
logging.debug(sys.argv)
myopts, args = getopt.getopt(sys.argv[1:],"p:t:w:",["port=","testSpeedRatio=","wavFile="])        
# default COM port is to not have one
comPort = None
# default test speed ratio is 1
testSpeedRatio = 1
for o, a in myopts:
    logging.info("Option %s value %s" % (o,a))
    if o in ('-p','--port'):
        comPort=a
    elif o in ('-t','--testSpeedRatio'):
        testSpeedRatio=int(a)
    elif o in ('-w','--wavFile'):
        wavFileName=a
    else:
        print("Usage: %s -p [serial port to connect to] -w [wav file name for horn] -t [default 1, set to more than 1 to run faster]" % sys.argv[0])
        
app = StartLineFrame()  
raceManager = RaceManager()
if testSpeedRatio:
    RaceManager.testSpeedRatio = testSpeedRatio
logging.info("Setting test speed ratio to %d" % testSpeedRatio)
easyDaqRelay = None
if comPort:     
    from lightsui.hardware import LIGHT_OFF, LIGHT_ON, EasyDaqUSBRelay
    easyDaqRelay = EasyDaqUSBRelay(comPort, app)
audioManager = AudioManager(wavFileName,app)  
screenController = ScreenController(app,raceManager,audioManager,easyDaqRelay)
gunController = GunController(app, audioManager, raceManager)
lightsController = LightsController(app, easyDaqRelay, raceManager)             
screenController.start() 
lightsController.start()
app.master.title('Startline')    
app.mainloop()  