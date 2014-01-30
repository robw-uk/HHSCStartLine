'''
Created on 26 Jan 2014

@author: MBradley
'''
import logging

import datetime

import serial

# constants for lights state
LIGHT_OFF = 0
LIGHT_ON = 1

# constants for serial port session state
DISCONNECTED = 0
RECONNECTING = 1
CONNECTED = 2

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


'''
EasyDayUSBRelay wraps an EasyDaq USB relay board. It currently uses the tkinter 
event loop for managing events.

If we experience issues with the stability of the tkinter user interface,
we could wrap this object in a separate process and use python Queue objects
to pass changes in the lights.
  
'''
class EasyDaqUSBRelay:

    def __init__(self, serialPortName,tkRoot):
        # capture the name of the serial port. On windows, this will be COM3, COM4 etc. The COM port is set
        # when the relay card is first plugged into the PC. You can change it subsequently through the control panel.
        self.serialPortName = serialPortName
        
        #
        # We use the Tkinter event mechanism to schedule activity. You must therefore pass the root object of your Tkinter application
        #
        self.tkRoot = tkRoot
        
        #
        # we use a signal pattern to notify events
        #
        self.changed = Signal()
        
        #
        # we create our serial port connection now. We don't open the connection until we are asked to connect
        #
        # timeout is set to 0.5 second for reads. 
        self.serialConnection = serial.Serial(timeout=0.5)
        
        # and tell the serial connection which serial port to connect
        self.serialConnection.port = self.serialPortName      
        
        # the baud rate is always 9600
        self.serialConnection.baudrate = 9600
        
        #
        # track whether or not we are enabled. If we are enabled, then we continue to check that have an active connection
        # and if not, we try to open the serial port. We start with not being enabled. As soon as we asked to connect,
        # we are enabled.
        #
        self.isEnabled = False
        
        
        #
        # track the time of the last command. We default to now as the startup time
        #
        self.lastPacketTime = datetime.datetime.now()
        
        #
        # trace the previous relay command. This enables us to resend in the event of a disconnect
        #
        self.currentRelayCommand = None
        self.previousRelayCommand = None
        
        #
        # We track our session status through constants DISCONNECTED,RECONNECTING,CONNECTED
        #
        self.sessionState = DISCONNECTED
            
    def setSessionState(self,state):
        self.sessionState = state
        logging.info("Session state is %s" % self.sessionStateDescription())
        self.changed.fire("connectionStateChanged",state)
        
    def beConnected(self):
        self.setSessionState(CONNECTED)
        
    def beNotConnected(self):
        self.setSessionState(DISCONNECTED)
        
    def beReconnecting(self):
        self.setSessionState(RECONNECTING)
        
        
    def sessionStateDescription(self):
        if self.sessionState == CONNECTED:
            return "CONNECTED"
        elif self.sessionState == DISCONNECTED:
            return "Warning: DISCONNECTED"
        elif self.sessionState == RECONNECTING:
            return "Warning: DISCONNECTED ATTEMPTING TO RECONNECT"
        
    def isConnected(self):
        return self.sessionState == CONNECTED
        
    def isDisconnected(self):
        return self.sessionState == DISCONNECTED
        
    def isReconnecting(self):
        return self.sessionState == RECONNECTING
            
    def processedCommand(self):
        '''
        We've processed a command. Capture the current date time.
        '''
        self.lastCommandProcessedTime = datetime.datetime.now()
        
    def maintainSession(self):
        # check the number of milliseconds since the last command.
        # If it is more than 5000 milliseconds
        if self.isConnected():
            logging.debug("Maintaining session")
            
            if (self.timeSinceLastPacket() > 5000):
                try:
                    
                    # create a relay packet that requests the EasyDaq to output its status
                    self.currentRelayPacket = 'A' + chr(0)
                    # and queue a request
                    self.queuePacketToEasyDaq()
                    # schedule a read for 500 milliseconds
                    self.tkRoot.after(500,self.readSession)
                    # and schedule to do this again in 5000 milli
                    self.tkRoot.after(5000,self.maintainSession)
                except (serial.SerialException):
                    logging.exception("Exception writing read request to session")
                    self.beNotConnected()
                    self.reconnect()
            # otherwise maintain session when 5000 millis has elapsed
            else:
                self.tkRoot.after(5000-self.timeSinceLastPacket(),self.maintainSession)
                
        
    def readSession(self):
        logging.debug("Reading from session")
        try:
            # read a single byte. This should be our current status but at the moment we don't check for that
            x = self.serialConnection.read()
            logging.debug("Read from session")
            
        except (serial.SerialException, ValueError) as e:
            logging.error("I/O error: {0}".format(e))
            self.serialConnection.close()
            self.beReconnecting()
            self.reconnect()
    
    
    def establishSession(self):
        logging.debug("Establishing session in state: %s" % self.sessionStateDescription() )
        self.sendRelayConfiguration([0,0,0,0,0])
        
        previousState = self.sessionState
        
        # and be connected
        self.beConnected()
        
        if previousState == RECONNECTING:
                
            if self.currentRelayCommand:
                logging.info("Recovering ... sending current relay command: %s" % self.printableCommand(self.currentRelayCommand))
                self.currentRelayPacket = self.currentRelayCommand
                self.queuePacketToEasyDaq()
            elif self.previousRelayCommand:
                logging.info("Recovering ... sending previous relay command: %s" % self.printableCommand(self.previousRelayCommand))
                self.currentRelayPacket = self.previousRelayCommand
                self.queuePacketToEasyDaq()
        self.tkRoot.after(5000,self.maintainSession)
    
    def connect(self):
        # we are sometimes trying to connect when we are already
        # connected
        if not self.isConnected():
            logging.debug("Connecting to serial port")
            self.enabled = True
            try:
                # try to open the serial port
                if self.serialConnection.isOpen():
                    logging.debug("Request to open serial port when already open")
                else:
                    self.serialConnection.open()
                    logging.debug("Connected to serial port")
                # wait for a second and establish the session
                self.tkRoot.after(2000,self.establishSession)
            
            except (serial.SerialException,ValueError) as e:           
                logging.error("I/O error: {0}".format(e))
                self.serialConnection.close()
                self.beReconnecting()
                self.reconnect()
        else:
            logging.debug("Request for connect when already connected")
            
    
    def reconnect(self):
        logging.info("Reconnecting to serial port")
        self.tkRoot.after(5000,self.connect)
        
        
    
    def disconnect(self):
        self.enabled = False
        if self.isConnected:
            self.serialConnection.close()
            self.beNotConnected()
        
    def timeSinceLastPacket(self):
        '''
        calculate the time since the last command
        '''
        deltaSinceLastPacket = datetime.datetime.now() - self.lastPacketTime
        
        return int((deltaSinceLastPacket.microseconds/1000) + deltaSinceLastPacket.seconds*1000)
    
    
    def writePacketToEasyDaq(self):
        # if we are connected, we write our packet
        try:
            logging.debug("Writing to serial port: %s" % self.printableCommand(self.currentRelayPacket))
            self.serialConnection.write(self.currentRelayPacket)
            
            #
            # Not the most elegant, but we check to see if this packet is a command by looking for a C as the first byte of the packet
            #
            if self.currentRelayPacket[0] =='C':
                
                self.previousRelayCommand = self.currentRelayCommand
                self.currentRelayCommand = None

            
            self.lastPacketTime = datetime.datetime.now()
        except (serial.SerialException,ValueError) as e:
            logging.error("I/O error: {0}".format(e))
            self.serialConnection.close()
            self.beReconnecting()
            
            self.reconnect()
    
    def printableCommand(self,relayCommand):
        return relayCommand[0] + "," + str(ord(relayCommand[1]))
    
    def queuePacketToEasyDaq(self):
        '''
        Write a command to EasyDaq. If we have written a command within the last 100 milliseconds,
        then delay by 100 milliseconds, otherwise write the command now.
        '''
        # easy scenario is that we can write the command immediately
        
        
        # if time delta is at least 100 milliseconds
        
        if (self.timeSinceLastPacket() > 100):
            # we can write the command now.
            self.writePacketToEasyDaq()
                
        else:
            # and queue to be written in 100 milliseconds
            logging.debug("Queuing writing packet to easyDaq")
            self.tkRoot.after(100-self.timeSinceLastPacket(), self.writePacketToEasyDaq)

    def sendRelayCommand(self,relayArray):
        # turn the values in the list into a byte where the bit in the byte reflects the position in the list.
        
        commandValue = 0
        
        for i in range(len(relayArray)):
                bitValue = (relayArray[i] *  pow(2,i))
                commandValue = commandValue + bitValue
        
        logging.info("Sending C + %i" % commandValue)
        relayCommand = 'C' + chr(commandValue)
        self.currentRelayCommand = relayCommand
        
        self.currentRelayPacket = relayCommand
        # if we are connected, we queue the packet. If we are not connected,
        # the session recovery will play in the relay packet
        if self.isConnected():
            self.queuePacketToEasyDaq()


        
    def sendRelayConfiguration(self,relayArray):
        # turn the values in the list into a byte where the bit in the byte reflects the position in the list.
        
        commandValue = 0
        
        for i in range(len(relayArray)):
                bitValue = (relayArray[i] *  pow(2,i))
                commandValue = commandValue + bitValue
        
        logging.info("Sending B + %i" % commandValue)        
        self.currentRelayPacket = 'B' + chr(commandValue)
        
        self.queuePacketToEasyDaq()
