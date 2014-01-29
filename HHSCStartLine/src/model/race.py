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
from wx.lib.pubsub import setupkwargs
from wx.lib.pubsub import  pub
import logging

# As per ISAF rules, start minutes is 5
# START_SECONDS = 300
# WARNING_SECONDS=300
# But we can reduce this for testing
START_SECONDS=30
WARNING_SECONDS=30

class RaceException(Exception):
    def __init__(self, race, message):
        self.race = race
        self.message = message
    def __str__(self):
         return repr(self.race)+ self.message

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
# A Race represents a sailing race. You should not change
# the state of a race (its name or start time); do this through
# the race manager.
#
class Race:
    
    nextRaceId = 1
    
    @classmethod
    def incrementNextRaceId(self):
        Race.nextRaceId = Race.nextRaceId + 1
    
    def __init__(self, name=None, startTime=None):
        self.changed = Signal()
        self.raceId = str(Race.nextRaceId)
        if name is None:
            name = "Race " + str(self.raceId)
      
        self.name = name
        self.startTime = startTime
        
        # we use a string for the raceId as this is what tk likes to see :)
        
        Race.incrementNextRaceId()

    #
    # Does this race have a start time?
    #
    def hasStartTime(self):
        return self.startTime != None

    #
    # Is this race running? This is synonymous with the race having
    # a start time
    #
    def isRunning(self):
        return self.hasStartTime()

    #
    # Has this race started? This means, is the race in the past?
    #
    def isStarted(self):
        if self.hasStartTime():
            return datetime.now() > self.startTime
            
        else:
            return False


    #
    # What's the delta to the start time of this race - negative
    # for yet to start, positive for already started. if no start time,
    # raises a RaceException.
    #
    def deltaToStartTime(self):
        if self.hasStartTime():
            return datetime.now() - self.startTime
        else:
            raise RaceException(self, "Race has no start time")

    # we are starting if our start time is in 5 mins or less
    def isStarting(self):
        # we can only be starting if we have a start time
        if self.hasStartTime():
            if (START_SECONDS * -1) <= self.deltaToStartTime().total_seconds() < 0:
                return True
            else:
                return False
        else:
            return False
        
    def isWaitingToStart(self):
        return self.hasStartTime() and not self.isStarted()

    #
    # Provide a string representation of the status of the race
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
# The race manager manages races, including creating new races,
# setting the start time for a race, running a race and performing
# a general recall.
#
# The race manager has a list of races. These are always sorted in
# the order that they will start.
#
class RaceManager:
    def __init__(self):
        self.races = []
        self.racesById = {}
        self.changed = Signal()
        
    #
    # Return seconds adjusted for our total START_SECONDS. In normal running, the return value
    # is the same as the parameter. If we're speeding up the sequence for testing, the return value
    # will be less. 
    #
    def adjustedStartSeconds(self, unadjustedSeconds):
        ratio = float(START_SECONDS)/300
        adjustedSeconds = unadjustedSeconds * ratio
        
        
        return adjustedSeconds
    
    #
    # Create a race, add to our races and return the race. If the name is not specified,
    # we create a name as 'Race N' where N is the number of races.
    #
    def createRace(self, name=None):
        aRace = Race(name=name)
        self.addRace(aRace)
        return aRace
    
    def raceWithId(self,id):
        if id in self.racesById:
            return self.racesById[id]
        

    def addRace(self, aRace):
        self.races.append(aRace)
        self.racesById[aRace.raceId] = aRace
        self.changed.fire("raceAdded",aRace)
        

    def removeRace(self, aRace):
        if aRace in self.races:
            positionInList = self.races.index(aRace)
            self.races.remove(aRace)
            del self.racesById[aRace.raceId]
            self.changed.fire("raceRemoved",aRace)
            
        else:
            raise RaceException("Race not found",aRace)
            

    def numberRaces(self):
        return len(self.races)

    #
    # Start our race sequence with a five minute warning before the first
    # race, i.e. 10 minutes to the first race
    #
    def startRaceSequenceWithWarning(self):
        
        raceNumber = 0
        now = datetime.now()
        for race in self.races:
            raceNumber = raceNumber + 1
            
            startTime = now + timedelta(
                seconds = (WARNING_SECONDS + (START_SECONDS * raceNumber)))

            self.updateRaceStartTime(race,startTime)
        self.changed.fire("sequenceStartedWithWarning")


    #
    # Start our race sequence without a warning (i.e. class start)
    #
    def startRaceSequenceWithoutWarning(self):
        raceNumber = 0
        now = datetime.now()
        for race in self.races:
            raceNumber = raceNumber + 1
            
            startTime = now + timedelta(
                seconds = (START_SECONDS * raceNumber))

            self.updateRaceStartTime(race,startTime)
        self.changed.fire("sequenceStartedWithoutWarning")
    #
    # Update the startTime for a race. Do this through the race manager
    # so that the race manager can signal the event change
    #
    def updateRaceStartTime(self, aRace, startTime):
        aRace.startTime = startTime
        # signal that the race start time has changed
        self.changed.fire("raceChanged",aRace)
        
            

    #
    # Find the last race started. This is a reverse search
    # of the races list for a started race.
    # Returns None if not found
    #
    def lastRaceStarted(self):
        for race in reversed(self.races):
            if race.isStarted():
                return race
        return None
    
    #
    # Fine the next race to start. If we don't have a race starting,
    # return None.
    #
    def nextRaceToStart(self):
        for race in self.races:
            if race.isStarting() or race.isWaitingToStart():
                return race
        return None


    def hasStartedRace(self):
        return self.lastRaceStarted()


    #
    # Perform a general recall. This is always for the race that
    # has most recently started
    #
    def generalRecall(self):
        raceToRecall = self.lastRaceStarted()

        # if this is not the last race, kick the race to the back
        # of the queue and set its start time to be five minutes
        # after the last race.
        
        # if this is the last race, set its start time to be five
        # minutes from now
        if raceToRecall == self.races[-1]:
            print "General recall last race"
            self.updateRaceStartTime(raceToRecall,datetime.now()
                                 + timedelta(seconds=START_SECONDS))

        # otherwise kick the race to be the back of the queue,
        # with a start time five minutes after the last race
        else:
            
            self.removeRace(raceToRecall)
            lastRace = self.races[-1]
            self.updateRaceStartTime(raceToRecall,
                    lastRace.startTime + timedelta(seconds=START_SECONDS))
            self.addRace(raceToRecall)
            logging.log(logging.INFO, "General recall not last race. Moving to back of queue. Delta to start time now %d seconds",
                        raceToRecall.deltaToStartTime().total_seconds())
            
        self.changed.fire("generalRecall", raceToRecall)

        
        
