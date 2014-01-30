'''
Created on 19 Jan 2014

Add some notes here about the choice of UI architecture, in particular TreeView


@author: MBradley
'''
from Tkinter import *
from ttk import *
 

from model.race import RaceManager

class StartLineFrame(Frame):
    '''
    classdocs
    '''


    def __init__(self,master=None):
        '''
        Constructor
        '''
        Frame.__init__(self, master)
        self.createWidgets()

        
    def createWidgets(self):
        
        style = Style()
        style.configure('.', font=('Helvetica',16))
        style.configure('Treeview',rowheight=30)
        
    
        
        self.racesTreeView = Treeview(self,
                                      columns=["startTime","status"],
                                      style='Treeview',
                                      selectmode="browse")
        
        ysb = Scrollbar(self, orient='vertical', command=self.racesTreeView.yview)
        xsb = Scrollbar(self, orient='horizontal', command=self.racesTreeView.xview)
        self.racesTreeView.heading("#0"  , text='Race', anchor=W)
        self.racesTreeView.column("#0", width=350)
        self.racesTreeView.heading("startTime",text='Start time', anchor=W)
        self.racesTreeView.heading("status",text='Status', anchor=W)
        self.racesTreeView.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.racesTreeView.grid(row=0,column=0,columnspan=2)
        ysb.grid(row=0, column=2, sticky='ns')
        xsb.grid(row=1, column=0, columnspan=2,sticky='ew')
        
        self.finishTreeView = Treeview(self,columns=["finishTime"],style="Treeview")
        ysb = Scrollbar(self, orient='vertical', command=self.racesTreeView.yview)
        xsb = Scrollbar(self, orient='horizontal', command=self.racesTreeView.xview)
        # NB need to make this auto scroll
        self.racesTreeView.heading("#0",text='Race',anchor=W)
        
        # add race button
        self.addRaceButton = Button(self,
                                    text="Add race")
        self.addRaceButton.grid(row=2,
                                column=0,
                                sticky=W+E+N+S,
                                   ipady=20)
        
        
        # remove race button
        self.removeRaceButton = Button(self,
                                        text="Remove race",state=DISABLED)
        self.removeRaceButton.grid(row=3,
                                   column=0, 
                                   sticky=W+E+N+S,
                                   ipady=20)
        
        # start race sequence with warning
        self.startRaceSequenceWithWarningButton = Button(self,
                                        text="F Flag Start",state=DISABLED)
        self.startRaceSequenceWithWarningButton.grid(row=2,
                                                     column=1,
                                                     sticky=W+E+N+S,
                                                     ipady=20)
        
        # start race sequence without warning
        self.startRaceSequenceWithoutWarningButton = Button(self,
                                        text="Class Flag Start",state=DISABLED)
        self.startRaceSequenceWithoutWarningButton.grid(row=3,
                                                        column=1,
                                                        sticky=W+E+N+S,
                                                        ipady=20)
        
        # general recall button
        self.generalRecallButton = Button(self,
                                        text="General recall",state=DISABLED)
        self.generalRecallButton.grid(row=4,
                                      column=1,
                                      sticky=W+E+N+S,
                                      ipady=20)
        
        # abandon sequence button
        self.abandonStartRaceSequenceButton = Button(self,
                                          text="Abandon start",state=DISABLED)
        self.abandonStartRaceSequenceButton.grid(row=4,
                                      column=0,
                                      sticky=W+E+N+S,
                                      ipady=20)
        
        #
        # gun button
        #
        self.gunButton = Button(self,
                                    text="Gun")
        self.gunButton.grid(row=0,column=3,sticky=W+E+N+S)
        
        #
        # clock
        #
        self.clockStringVar = StringVar(self,value="00:00:00")
        clockLabel = Label(self,textvariable=self.clockStringVar)
        clockLabel.grid(row=5,column=3)
        
        #
        # EasyDaqRelay connection status label
        #
        self.connectionStatus = StringVar(self,value="Connecting")
        connectionStatusLabel = Label(self,textvariable=self.connectionStatus)
        connectionStatusLabel.grid(row=5,column=0)
        
        # tell the frame to lay itself out
        
        self.grid()
        
        
    def enableGeneralRecallButton(self):
        self.generalRecallButton['state']=NORMAL
    
    def disableGeneralRecallButton(self):
        self.generalRecallButton['state']=DISABLED
        
    def enableAddRaceButton(self):
        self.addRaceButton['state']=NORMAL
        
    def disableAddRaceButton(self):
        self.addRaceButton['state']=DISABLED
        
    
    def enableRemoveRaceButton(self):
        self.removeRaceButton['state']=NORMAL
        
    def disableRemoveRaceButton(self):
        self.removeRaceButton['state']=DISABLED
        
    def disableStartRaceSequenceWithWarningButton(self):
        self.startRaceSequenceWithWarningButton['state'] = DISABLED
        
    def disableStartRaceSequenceWithoutWarningButton(self):
        self.startRaceSequenceWithoutWarningButton['state'] = DISABLED
        
    def enableStartRaceSequenceWithWarningButton(self):
        self.startRaceSequenceWithWarningButton['state'] = NORMAL
        
    def enableStartRaceSequenceWithoutWarningButton(self):
        self.startRaceSequenceWithoutWarningButton['state'] = NORMAL
        
    def disableAbandonStartRaceSequenceButton(self):
        self.abandonStartRaceSequenceButton['state'] = DISABLED
        
    def enableAbandonStartRaceSequenceButton(self):
        self.abandonStartRaceSequenceButton['state'] = NORMAL
        
class AddRaceDialog:
    def __init__(self, parent, raceNamesList):
        self.top = Toplevel(parent)
        self.frame = Frame(self.top)
        self.frame.pack(fill=BOTH,expand=True)
        
        self.raceNamesList = raceNamesList
        self.raceName = None
        self.createWidgets()
        
        
        
        
    def createWidgets(self):
        style = Style()
        style.configure('.', font=('Helvetica',16))
        style.configure('Treeview',rowheight=30)
        
        label = Label(self.frame, text='Choose from the list:')
        label.pack()
        
        self.raceNamesListBox = Treeview(self.frame,
                                         selectmode="browse")
        self.raceNamesListBox.column("#0", width=400)
        
        self.raceNamesListBox.pack(fill=BOTH,expand=True)
        
        # we use the name of the race as the list id. Should be fine so long as there are no duplicates
        for raceName in self.raceNamesList:
            self.raceNamesListBox.insert(parent="",index="end",text=raceName,iid=raceName)
            
        self.raceNamesListBox.bind('<<TreeviewSelect>>',self.raceNameListItemSelected)
        self.raceNamesListBox.bind("<Double-1>", self.raceNameDoubleClicked)
    
        label = Label(self.frame, text='or type in your own', anchor=W)
        label.pack()
        
        
        self.raceNameVariable = StringVar()
        self.raceNameLabel = Entry(self.frame,textvariable = self.raceNameVariable)
        self.raceNameLabel.pack(fill=BOTH,expand=True)
        
        
        
        self.cancelButton = Button(self.frame,text="Cancel",command=self.cancelClicked)
        self.cancelButton.pack()
        self.okButton = Button(self.frame,text="OK",command=self.okClicked)
        self.okButton.pack()
        
    def raceNameListItemSelected(self,event):
        
        
        # note that we set the iid of each item in the list to be the name. Very simple.
        selectedRaceName = self.raceNamesListBox.selection()[0]
        self.raceNameVariable.set(selectedRaceName)
    
    def raceNameDoubleClicked(self,event):
        selectedRaceName = self.raceNamesListBox.selection()[0]
        self.raceNameVariable.set(selectedRaceName)
        self.raceName=self.raceNameVariable.get()
        self.top.destroy()
        
    
    def okClicked(self):
        self.raceName=self.raceNameVariable.get()
        self.top.destroy()
        
    def cancelClicked(self):
        self.raceName=None
        self.top.destroy()
    
    def show(self):
        self.focus_set()
        self.grab_set()
        self.transient(self.parent)
        self.wait_window(self)
    