'''
Created on 20 Jan 2014

The audio manager plays a WAV file asynchronously. As per http://joyrex.spc.uchicago.edu/bookshelves/python/cookbook/pythoncook-CHP-9-SECT-7.html
Tk should be insulated from any external IO.

See http://people.csail.mit.edu/hubert/pyaudio/ for details of PyAudio

You will need to download PyAudio, see http://people.csail.mit.edu/hubert/pyaudio/#downloads

@author: MBradley
'''
import pyaudio
import wave
import Queue
import time
import logging

from StringIO import StringIO

CHUNK=1024

class AudioManager:
    
    def __init__(self, wavFilename):
        
        self.portAudio = pyaudio.PyAudio()
        self.wavFilename = wavFilename
        self.readFileToMemory()
        self.wavDuration = self.calculateDuration()
        self.commandQueue = Queue.Queue()
        self.isPlaying = False
        
        
    def readFileToMemory(self):
        # see http://stackoverflow.com/questions/8195544/how-to-play-wav-data-right-from-memory
        fileOnDisk = open(self.wavFilename,'rb')
        self.fileInMemory = StringIO(fileOnDisk.read())
        fileOnDisk.close()
    
    def openWav(self):
        self.fileInMemory.seek(0)
        self.wav = wave.open(self.fileInMemory)
        pass
        
    
    def calculateDuration(self):
        self.openWav()
        numberFrames = self.wav.getnframes()
        rate = self.wav.getframerate()
        duration = int(1000 * (numberFrames / float(rate)))
        return duration
        


    def playWav(self):
        self.isPlaying = True
        logging.debug("Playing wav")
        self.openWav()
        stream = self.portAudio.open(format=self.portAudio.get_format_from_width(self.wav.getsampwidth()),
                channels=self.wav.getnchannels(),
                rate=self.wav.getframerate(),
                output=True)
        data = self.wav.readframes(CHUNK)
        while data != '':
            stream.write(data)
            data = self.wav.readframes(CHUNK)
        stream.stop_stream() 
        stream.close()
        
            
    #
    # The audio manager is designed to run synchronously in its own thread, using a Queue.Queue
    # to queue requests to play audio files using a command pattern.    #
    def run(self):
        self.isRunning = True
        while self.isRunning:
            try:
                logging.debug("Waiting on audio manager command queue")
                command = self.commandQueue.get(block=True)
                command.executeOn(self)
                
            except Queue.Empty:
                # we do nothing if the queue is empty. This should never happen, because we are
                # blocking for ever.
                pass
        self.portAudio.terminate()
            
    #
    # This method is called from within the Tkinter event thread.
    #
    def queueWav(self):
        self.commandQueue.put(AudioManagerPlayWav())
        
    
    def stop(self):
        self.commandQueue.put(AudioManagerStop())
    
    #
    # if you want to know how many queued, check for the queue length
    #
    def queueLength(self):
        return self.commandQueue.qsize()
        

class AudioManagerCommand:
    def executeOn(self, anAudioManager):
        pass
    
class AudioManagerPlayWav(AudioManagerCommand):
    def executeOn(self, anAudioManager):
        anAudioManager.playWav()
        
class AudioManagerStop(AudioManagerCommand):
    def executeOn(self, anAudioManager):
        anAudioManager.isRunning = False
        
        

