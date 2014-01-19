import unittest
import datetime
import sys

from race import Race, RaceManager, RaceException, START_SECONDS, WARNING_SECONDS

class TestRace(unittest.TestCase):

    def testEmptyRace(self):
        race = Race()
        self.assertEqual(race.name,None)
        self.assertEqual(race.startTime,None)
        

    def testPopulatedRace(self):
        # create a race that starts in ten minutes
        race = Race(name='Brass Monkey Race 2 Large Handicap',
                    startTime = datetime.datetime.now() + datetime.timedelta(minutes = 10) )
        
        self.assertTrue(race.name =='Brass Monkey Race 2 Large Handicap')
        self.assertTrue(race.startTime > datetime.datetime.now())

    def testRaceStartingInFuture(self):
        # create a race
        race = Race(name='Brass Monkey Race 2 Large Handicap')
        # set it's start time to be in ten minute
        race.startTime = datetime.datetime.now() + datetime.timedelta(seconds = START_SECONDS +1) 
        # check that it's running but not started
        self.assertTrue(race.isRunning())
        self.assertFalse(race.isStarted())
        # check its status
        self.assertEqual(race.status(),"Waiting to start")
        
    def testRaceStartingInPast(self):
        # create a race
        race = Race(name='Brass Monkey Race 2 Large Handicap')
        # set it's start time to be in ten minutes
        race.startTime = datetime.datetime.now() + datetime.timedelta(seconds = -1*(START_SECONDS+1)) 
        # check that it's running but not started
        self.assertTrue(race.isRunning())
        self.assertTrue(race.isStarted())
        # check its status
        self.assertEqual(race.status(),"Started")

    def testRaceStartingNow(self):
        # create a race
        race = Race(name='Brass Monkey Race 2 Large Handicap')
        # set it's start time to be in three minutes
        race.startTime = datetime.datetime.now() + datetime.timedelta(seconds = START_SECONDS-1) 
        # check that it's running but not started
        self.assertTrue(race.isRunning())
        self.assertFalse(race.isStarted())
        # check its status
        self.assertEqual(race.status(),"Starting")

        

    def testDeltaToStartTimeException(self):
        
        # create a race
        race = Race(name='Brass Monkey Race 2 Large Handicap')
        # check that we get an exception if we ask for a start time
        try:
            delta = race.deltaToStartTime()
        except RaceException:
            pass
        except:
            e = sys.exc_info()[0]
            self.fail('Unexpected exception thrown:',e)
        else:
            self.fail('RaceException not thrown')

    def testDeltaToStartTime(self):
        
        # create a race
        race = Race(name='Brass Monkey Race 2 Large Handicap')

        # set it's start time to be in ten minutes
        race.startTime = datetime.datetime.now() + datetime.timedelta(minutes = -10)

        # test that the delta is ten minutes
        # note this may fail if the clock moves on during execution
        self.assertEqual(race.deltaToStartTime(), datetime.datetime.now() - race.startTime)
        
        

class TestRaceManager(unittest.TestCase):
    def createDateTimeFromNow(self,seconds):
        return datetime.datetime.now() + datetime.timedelta(seconds = seconds)
    
    def testEmptyRaceManager(self):
        raceManager = RaceManager()
        self.assertEqual(raceManager.numberRaces(),0)

    def testCreateUnnamedRace(self):
        raceManager = RaceManager()
        aRace = raceManager.createRace()
        self.assertEqual(raceManager.numberRaces(),1)
        self.assertEqual(aRace.name,"Race 1")

    def testCreateNamedRace(self):
        raceManager = RaceManager()
        aRace = raceManager.createRace("Brass Monkey")
        self.assertEqual(raceManager.numberRaces(),1)
        self.assertEqual(aRace.name, "Brass Monkey")

    def testCreateThreeRaces(self):
        raceManager = RaceManager()
        for i in range(3):
            raceManager.createRace()
            
        self.assertEqual(raceManager.numberRaces(),3)

    def testStartRaceManagerSequence(self):
        # create three races
        raceManager = RaceManager()
        for i in range(3):
            raceManager.createRace()
            
        # start the race sequence with a five minute warning
        raceManager.startRaceSequenceWithWarning()

        # check that the time deltas for the three races are correct
        self.assertEqual(raceManager.races[0].startTime, self.createDateTimeFromNow(
            WARNING_SECONDS + START_SECONDS))
        self.assertEqual(raceManager.races[1].startTime, self.createDateTimeFromNow(
            WARNING_SECONDS + START_SECONDS * 2))
        self.assertEqual(raceManager.races[2].startTime, self.createDateTimeFromNow(
            WARNING_SECONDS + START_SECONDS * 3))


    def testGeneralRecallFirstRace(self):
        # create three races
        # create three races
        raceManager = RaceManager()
        for i in range(3):
            raceManager.createRace()

        # start the race sequence with a five minute warning
        raceManager.startRaceSequenceWithWarning()


        #
        # we want to achieve the affect of moving forward so that the first
        # race has just started. This is 
        # WARNING_SECONDS + START_SECONDS + 1

        
        # decrement the times of the each race to be WARNING_SECONDS + START_SECONDS + 1
        # this puts us into the position of 1 second past the first race
        
        for race in raceManager.races:
            
            race.startTime = race.startTime - \
                datetime.timedelta(seconds = WARNING_SECONDS + START_SECONDS + 1)

        self.assertEqual(raceManager.races[0].status(), "Started")
        self.assertEqual(raceManager.races[1].status(), "Starting")
        self.assertEqual(raceManager.races[2].status(), "Waiting to start")

        raceToRecall = raceManager.races[0]
        #
        # now do a general recall
        #
        raceManager.generalRecall()

        # we should still have 3 races
        self.assertEqual(raceManager.numberRaces(),3)
        # the recalled race should be at the back
        self.assertEqual(raceManager.races[-1],raceToRecall)
        # and its start time should be START_SECONDS more than the second race
        self.assertEqual(
            raceToRecall.startTime,
            raceManager.races[1].startTime + datetime.timedelta(seconds = START_SECONDS))
        #
        self.assertEqual(raceManager.races[0].status(), "Starting")
        self.assertEqual(raceManager.races[1].status(), "Waiting to start")
        self.assertEqual(raceManager.races[2].status(), "Waiting to start")

    

    def testGeneralRecallMiddleRace(self):
        # create three races
        # create three races
        raceManager = RaceManager()
        for i in range(3):
            raceManager.createRace()

        # start the race sequence with a five minute warning
        raceManager.startRaceSequenceWithWarning()


        #
        # we want to achieve the affect of moving forward so that the seconds
        # race has just started. This is 
        # WARNING_SECONDS + START_SECONDS * 2 + 1

        
        
        # this puts us into the position of 1 second past the second race
        
        for race in raceManager.races:
            
            race.startTime = race.startTime - \
                datetime.timedelta(seconds = WARNING_SECONDS + (START_SECONDS * 2) + 1)

        self.assertEqual(raceManager.races[0].status(), "Started")
        self.assertEqual(raceManager.races[1].status(), "Started")
        self.assertEqual(raceManager.races[2].status(), "Starting")

        raceToRecall = raceManager.races[1]
        #
        # now do a general recall
        #
        raceManager.generalRecall()

        # we should still have 3 races
        self.assertEqual(raceManager.numberRaces(),3)
        # the recalled race should be at the back
        self.assertEqual(raceManager.races[-1],raceToRecall)
        # and its start time should be START_SECONDS more than the second race
        self.assertEqual(
            raceToRecall.startTime,
            raceManager.races[1].startTime + datetime.timedelta(seconds = START_SECONDS))
        self.assertEqual(raceManager.races[0].status(), "Started")
        self.assertEqual(raceManager.races[1].status(), "Starting")
        self.assertEqual(raceManager.races[2].status(), "Waiting to start")
        

    def testGeneralRecallLastRace(self):
        # create three races
        # create three races
        raceManager = RaceManager()
        for i in range(3):
            raceManager.createRace()

        # start the race sequence with a five minute warning
        raceManager.startRaceSequenceWithWarning()


        #
        # we want to achieve the affect of moving forward so that the seconds
        # race has just started. This is 
        # WARNING_SECONDS + START_SECONDS * 3 + 1

        
        # this puts us into the position of 1 second past the third race
        
        for race in raceManager.races:
            
            race.startTime = race.startTime - \
                datetime.timedelta(seconds = WARNING_SECONDS + (START_SECONDS * 3) + 1)

        self.assertEqual(raceManager.races[0].status(), "Started")
        self.assertEqual(raceManager.races[1].status(), "Started")
        self.assertEqual(raceManager.races[2].status(), "Started")

        raceToRecall = raceManager.races[2]
        #
        # now do a general recall
        #
        raceManager.generalRecall()

        # we should still have 3 races
        self.assertEqual(raceManager.numberRaces(),3)
        # the recalled race should be at the back
        self.assertEqual(raceManager.races[-1],raceToRecall)
        # and its start time should be START_SECONDS more than the current time
        self.assertEqual(
            raceToRecall.startTime,
            datetime.datetime.now() + datetime.timedelta(seconds = START_SECONDS))

        self.assertEqual(raceManager.races[0].status(), "Started")
        self.assertEqual(raceManager.races[1].status(), "Started")
        self.assertEqual(raceManager.races[2].status(), "Starting")
    
        
        

    

if __name__ == '__main__':
    # workaround for running tests from IDLE, see
    #http://stackoverflow.com/questions/79754/unittest-causing-sys-exit
    unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestRace))
    unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestRaceManager))

