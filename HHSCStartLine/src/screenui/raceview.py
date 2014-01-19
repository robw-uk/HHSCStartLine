'''
Created on 19 Jan 2014

Uses tkintertable version 1.1.2 to render the table of races. 
see https://code.google.com/p/tkintertable/

Download from https://code.google.com/p/tkintertable/downloads/list

If using Eclipse as an IDE, remember to "Force restore internal info" for the
PYTHONPATH of the project to pick up the new modules of the library.

tkintertable 1.1.2 also requires pmw, see
https://code.google.com/p/tkintertable/issues/detail?id=3

PMW 1.3.3 from http://sourceforge.net/projects/pmw/files/Pmw/Pmw.1.3.3/Pmw_1_3_3b.tar.gz/download

Use 7zip to extract the PMW folder from the gzipped tar. Then run
python setup.py install


@author: MBradley
'''
import Tkinter as tk
import ttk
from tkintertable.Tables import TableCanvas
from tkintertable.TableModels import TableModel
 
import logging
import sys
import getopt
from model.race import RaceManager

class StartLineFrame(tk.Frame):
    '''
    classdocs
    '''


    def __init__(self,master=None):
        '''
        Constructor
        '''
        tk.Frame.__init__(self, master)
        self.createWidgets()
        
    def createWidgets(self):
        
        self.racesTreeView = ttk.Treeview(self,columns=["startTime","status"])
        ysb = ttk.Scrollbar(self, orient='vertical', command=self.racesTreeView.yview)
        xsb = ttk.Scrollbar(self, orient='horizontal', command=self.racesTreeView.xview)
        self.racesTreeView.heading("#0"  , text='Race', anchor=tk.W)
        self.racesTreeView.heading("startTime",text='Start time', anchor=tk.W)
        self.racesTreeView.heading("status",text='Status', anchor=tk.W)
        self.racesTreeView.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.racesTreeView.grid(row=0,column=0)
        ysb.grid(row=0, column=1, sticky='ns')
        xsb.grid(row=1, column=0, sticky='ew')
        
        self.addRaceButton = ttk.Button(self,
                                        text="Add race")
        self.addRaceButton.grid(row=2,column=0)
        
        self.removeRaceButton = ttk.Button(self,
                                        text="Remove race")
        self.removeRaceButton.grid(row=2,column=1)
        self.grid()
        
        


       
    
            
        
class StartLineController():
    pass

    def __init__(self,startLineFrame):
        self.startLineFrame = startLineFrame
        self.createRaceManager()
        self.buildRaceManagerView()
        self.wireController()
        
    def createRaceManager(self):
        self.raceManager = RaceManager()
        self.raceManager.changed.connect("raceAdded",self.handleRaceAdded)
        self.raceManager.changed.connect("raceRemoved",self.handleRaceRemoved)
        self.raceManager.changed.connect("raceChanged",self.handleRaceChanged)
        

    def wireController(self):
        self.startLineFrame.addRaceButton.config(command=self.addRaceClicked)
        self.startLineFrame.removeRaceButton.config(command=self.removeRaceClicked)
        self.startLineFrame.racesTreeView.bind("<<TreeviewSelect>>",self.raceSelectionChanged)
        
    def buildRaceManagerView(self):
        # we build our tree
           
        for race in self.raceManager.races:
            self.appendRaceToTreeView(race)
    
    
    def appendRaceToTreeView(self,aRace):
        if aRace.hasStartTime():
            startTime = aRace.deltaToStartTime()
        else:
            startTime = "-"
        self.startLineFrame.racesTreeView.insert(
             parent="",
             index="end",
             iid = aRace.raceId,
             text = aRace.name,
             values=(startTime,aRace.status()))  
            
    def addRaceClicked(self):
        self.raceManager.createRace()
        
    def removeRaceClicked(self):#
        # check we have a selected race
        if self.selectedRace:
            self.raceManager.removeRace(self.selectedRace)
        
    def raceSelectionChanged(self,event):
        item = self.startLineFrame.racesTreeView.selection()[0]
        
        self.selectedRace = self.raceManager.raceWithId(item)
        
        print self.selectedRace
    
    def handleRaceAdded(self,aRace):
        self.appendRaceToTreeView(aRace)
    
    def handleRaceRemoved(self,aRace):
        self.startLineFrame.racesTreeView.delete(aRace.raceId)
    
    def handleRaceChanged(self):
        pass
        
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
controller = StartLineController(app)              
app.master.title('HHSC Race Lights')    
app.mainloop()  