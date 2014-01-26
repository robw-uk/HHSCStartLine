'''
Created on 19 Jan 2014

Add some notes here about the choice of UI architecture, in particular ttk.TreeView


@author: MBradley
'''
import Tkinter as tk
import ttk

 

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
        self.racesTreeView.grid(row=0,column=0,columnspan=2)
        ysb.grid(row=0, column=2, sticky='ns')
        xsb.grid(row=1, column=0, columnspan=2,sticky='ew')
        
        # add race button
        self.addRaceButton = ttk.Button(self,
                                        text="Add race")
        self.addRaceButton.grid(row=2,column=0)
        
        
        # remove race button
        self.removeRaceButton = ttk.Button(self,
                                        text="Remove race")
        self.removeRaceButton.grid(row=2,column=1)
        
        # start race sequence with warning
        self.startRaceSequenceWithWarningButton = ttk.Button(self,
                                        text="F Flag Start")
        self.startRaceSequenceWithWarningButton.grid(row=0,column=3)
        
        # start race sequence without warning
        self.startRaceSequenceWithoutWarningButton = ttk.Button(self,
                                        text="Class Flag Start")
        self.startRaceSequenceWithoutWarningButton.grid(row=1,column=3)
        
        # general recall button
        self.generalRecallButton = ttk.Button(self,
                                        text="General recall")
        self.generalRecallButton.grid(row=2,column=3)
        
        #
        # gun button
        #
        self.gunButton = ttk.Button(self,
                                    text="Gun")
        self.gunButton.grid(row=3,column=3)
        
        
        # tell the frame to lay itself out
        
        self.grid()
        
        
