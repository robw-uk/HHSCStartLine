'''
Created on 20 Apr 2014

@author: MBradley
'''
import unittest

import model.race
import datetime

class BoatTest(unittest.TestCase):
    
    
    def setUp(self):
        self.seedTime = datetime.datetime.now()
        self.raceManager = model.race.RaceManager()
        self.fleet1 = self.raceManager.createFleet("small handicap")
        self.fleet1.startTime = self.seedTime - datetime.timedelta(minutes=15)
        
        

    def testCreateBoat(self):
        boat = model.race.Boat("31618","topper")
        self.assertEqual(boat.sailNumber, "31618")
        self.assertEqual(boat.boatClass, "topper")
        
    def testFinishBoat(self):
        boat = model.race.Boat("31618","topper")
        boat.py = 1322
        
        finish1 = self.raceManager.createFinish(fleet=self.fleet1, finishTime = (self.seedTime + datetime.timedelta(minutes=30)))
        boat.finish = finish1
        self.assertAlmostEqual(boat.calculatePyAdjustedSeconds(),2700 * 1000 / 1322,0) 
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'BoatTest.testCreateBoadt']
    unittest.main()