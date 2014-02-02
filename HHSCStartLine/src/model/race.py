#
# racing.model
#


#
# This module contains the classes for running races to the requirements of
# Hill Head Sailing Club, Fareham, Hampshire www.hillheadsc.org.uk
#

#
# The over-riding design principle of the model is KISS (Keep It Simple, Stupid).
#
# To this end, despite the real time nature of running a race, the state of the
# objects in the model do not change in real time. A race has a startTime. This
# is a clock time, e.g. 1115. The countdown to or elapsed time from are calculated
# from the clock time. Races are managed by a RaceManager, which is similarly
# static.
#
# The model uses wx.lib.pubsub for the model to send events to listeners. The
# UIs can subscribe to
# events on Races and also the RaceManager. See
# http://wxpython.org/docs/api/wx.lib.pubsub-module.html
#
#

from datetime import datetime,timedelta
import logging

# As per ISAF rules, start minutes is 5
# START_SECONDS = 300
# WARNING_SECONDS=300
# But we can reduce this for testing
START_SECONDS=300
WARNING_SECONDS=300

class RaceException(Exception):
    def __init__(self, fleet, message):
        self.fleet = fleet
        self.message = message
    def __str__(self):
        return repr(self.fleet)+ self.message

#
# Our event handling mechanism,
# from http://codereview.stackexchange.com/questions/20938/the-observer-design-pattern-in-python-in-a-more-pythonic-way-plus-unit-testing
#
class Signal(object):
    def __init__(self):
        self._handlers = {}

    def connect(self, event,handler):
        if event in self._handlers:
            # do nothing, we've got a list of handlers for this event
            pass
        else:
            self._handlers[event] = []
         
        self._handlers[event].append(handler)

    def fire(self, event, *args):
        if event in self._handlers:
            for handler in self._handlers[event]:
                handler(*args)

#
# A fleet represents a fleet of boats in a race. You should not change
# the state of a race (its name or start time); do this through
# the race manager.
#
class Fleet:
    
    nextFleetId = 1
    
    @classmethod
    def incrementNextFleetId(self):
        Fleet.nextFleetId = Fleet.nextFleetId + 1
    
    def __init__(self, name=None, startTime=None):
        self.changed = Signal()
        self.fleetId = str(Fleet.nextFleetId)
        if name is None:
            name = "Fleet " + str(self.fleetId)
      
        self.name = name
        self.startTime = startTime
        
        # we use a string for the fleetId as this is what tk likes to see :)
        
        Fleet.incrementNextFleetId()

    #
    # Does this fleet have a start time?
    #
    def hasStartTime(self):
        return self.startTime != None

    #
    # Is this fleet running? This is synonymous with the fleet having
    # a start time
    #
    def isRunning(self):
        return self.hasStartTime()

    #
    # Has this fleet started? This means, did the fleet start in the past?
    #
    def isStarted(self):
        if self.hasStartTime():
            return datetime.now() > self.startTime
            
        else:
            return False


    def adjustedDeltaSecondsToStartTime(self):
        return self._deltaToStartTime().total_seconds() * RaceManager.testSpeedRatio
        
    #
    # This is the real seconds to start time.
    # 
    def deltaSecondsToStartTime(self):
        return self._deltaToStartTime().total_seconds()

    #
    # What's the delta to the start time of this fleet - negative
    # for yet to start, positive for already started. if no start time,
    # raises a RaceException.
    #
    def _deltaToStartTime(self):
        if self.hasStartTime():
            return datetime.now() - self.startTime
        else:
            raise RaceException(self, "Fleet has no start time")

    # we are starting if our start time is in 5 mins or less
    def isStarting(self):
        # we can only be starting if we have a start time
        if self.hasStartTime():
            if (START_SECONDS * -1) <= self.adjustedDeltaSecondsToStartTime() < 0:
                return True
            else:
                return False
        else:
            return False
        
    def isWaitingToStart(self):
        return self.hasStartTime() and not self.isStarted()

    #
    # Provide a string representation of the status of the fleet
    #
    def status(self):
        if not self.hasStartTime():
            # note sure about this description - ask Luke
            return "Pending"
        if self.isStarting():
            return "Starting"
        if self.isStarted():
            return "Started"
        if not self.isStarted():
            return "Waiting to start"
            

    def __str__(self):
        return self.name + " status: " + self.status()
        
#
# The race manager manages fleets, including creating new fleets,
# setting the start time for a fleet, running a race and performing
# a general recall.
#
# The race manager has a list of fleets. These are always sorted in
# the order that they will start.
#
class RaceManager:
    
    testSpeedRatio = 1
    
    def __init__(self):
        self.fleets = []
        self.fleetsById = {}
        self.changed = Signal()
        

    def adjustedSeconds(self,unadjustedSeconds):
        return unadjustedSeconds * RaceManager.testSpeedRatio
    
    #
    # Create a fleet, add to our fleets and return the fleet. If the name is not specified,
    # we create a name as 'Fleet N' where N is the number of fleets.
    #
    def createFleet(self, name=None):
        aFleet = Fleet(name=name)
        self.addFleet(aFleet)
        return aFleet
    
    def fleetWithId(self,fleetId):
        if fleetId in self.fleetsById:
            return self.fleetsById[fleetId]
        

    def addFleet(self, aFleet):
        self.fleets.append(aFleet)
        self.fleetsById[aFleet.fleetId] = aFleet
        self.changed.fire("fleetAdded",aFleet)
        

    def removeFleet(self, aFleet):
        if aFleet in self.fleets:
            positionInList = self.fleets.index(aFleet)
            self.fleets.remove(aFleet)
            del self.fleetsById[aFleet.fleetId]
            self.changed.fire("fleetRemoved",aFleet)
            
        else:
            raise RaceException("Fleet not found",aFleet)
            

    def numberFleets(self):
        return len(self.fleets)
    
    def hasFleets(self):
        return self.numberFleets() > 0

    #
    # Start our race sequence with a five minute warning before the first
    # fleet, i.e. 10 minutes to the first fleet start. This is F flag start
    #
    def startRaceSequenceWithWarning(self):
        logging.info("Start sequence with warning (F flag start)")
        fleetNumber = 0
        now = datetime.now()
        for fleet in self.fleets:
            fleetNumber = fleetNumber + 1
            
            startTime = now + timedelta(
                seconds = (WARNING_SECONDS/RaceManager.testSpeedRatio + 
                        (START_SECONDS * fleetNumber)/RaceManager.testSpeedRatio))

            self.updateFleetStartTime(fleet,startTime)
        self.changed.fire("sequenceStartedWithWarning")


    #
    # Start our race sequence without a warning (i.e. class start)
    #
    def startRaceSequenceWithoutWarning(self):
        logging.info("Start sequence without warning (class flag start)")
        fleetNumber = 0
        now = datetime.now()
        for fleet in self.fleets:
            fleetNumber = fleetNumber + 1
            
            startTime = now + timedelta(
                seconds = (START_SECONDS * fleetNumber)/RaceManager.testSpeedRatio)

            self.updateFleetStartTime(fleet,startTime)
        self.changed.fire("sequenceStartedWithoutWarning")
    #
    # Update the startTime for a fleet. Do this through the race manager
    # so that the race manager can signal the event change
    #
    def updateFleetStartTime(self, aFleet, startTime):
        aFleet.startTime = startTime
        # signal that the fleet start time has changed
        self.changed.fire("fleetChanged",aFleet)
        
            

    #
    # Find the last fleet started. This is a reverse search
    # of the fleets list for a started fleet.
    # Returns None if not found
    #
    def lastFleetStarted(self):
        for fleet in reversed(self.fleets):
            if fleet.isStarted():
                return fleet
        return None
    
    #
    # Fine the next fleet to start. If we don't have a fleet starting,
    # return None.
    #
    def nextFleetToStart(self):
        for fleet in self.fleets:
            if fleet.isStarting() or fleet.isWaitingToStart():
                return fleet
        return None


    def hasStartedFleet(self):
        return self.lastFleetStarted()
    
    
    def hasSequenceStarted(self):
        if self.nextFleetToStart():
            return True
        else:
            return False
    
    
    #
    # Abandon start sequence - set all fleets to no start time, and fire a signal
    #
    def abandonStartSequence(self):
        for fleet in self.fleets:
            fleet.startTime = None
        self.changed.fire("startSequenceAbandoned")


    #
    # Perform a general recall. This is always for the fleet that
    # has most recently started
    #
    def generalRecall(self):
        logging.info("General recall")
        fleetToRecall = self.lastFleetStarted()

        # if this is not the last fleet, kick the fleet to the back
        # of the queue and set its start time to be five minutes
        # after the last fleet.
        
        # if this is the last fleet, set its start time to be five
        # minutes from now
        if fleetToRecall == self.fleets[-1]:
            logging.info("General recall last fleet")
            self.updateFleetStartTime(fleetToRecall,datetime.now()
                                 + timedelta(seconds=START_SECONDS/RaceManager.testSpeedRatio))

        # otherwise kick the fleet to be the back of the queue,
        # with a start time five minutes after the last fleet
        else:
            
            self.removeFleet(fleetToRecall)
            lastFleet = self.fleets[-1]
            self.updateFleetStartTime(fleetToRecall,
                    lastFleet.startTime + timedelta(seconds=START_SECONDS/RaceManager.testSpeedRatio))
            self.addFleet(fleetToRecall)
            logging.log(logging.INFO, "General recall not last fleet. Moving to back of queue. Delta to start time now %d seconds",
                        fleetToRecall.adjustedDeltaSecondsToStartTime())
            
        self.changed.fire("generalRecall", fleetToRecall)

        
        
