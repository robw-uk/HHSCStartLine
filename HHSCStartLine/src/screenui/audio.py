'''
Created on 20 Jan 2014

The audio manager plays a WAV file asynchronously. If you ask it to play the file
whilst it is playing a file, it will queue the request and then immediately play
the file again.

It uses the tkRoot after timer to check for further queued request.

See http://people.csail.mit.edu/hubert/pyaudio/ for details of PyAudio

You will need to download PyAudio, see http://people.csail.mit.edu/hubert/pyaudio/#downloads

@author: MBradley
'''
import pyaudio
import wave

from StringIO import StringIO
from model.utils import Signal


class AudioManager:
    
    def __init__(self, wavFilename, tkRoot):
        
        self.portAudio = pyaudio.PyAudio()
        self.tkRoot = tkRoot
        self.wavFilename = wavFilename
        self.readFileToMemory()
        self.wavDuration = self.calculateDuration()
        self.playRequestQueue = 0
        self.isPlaying = False
        self.changed = Signal()
        
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
        

    def callback(self, in_data, frame_count, time_info, status):
        data = self.wav.readframes(frame_count)
        
        return (data, pyaudio.paContinue)

    

    def startStream(self):
        self.stream = self.portAudio.open(format=self.portAudio.get_format_from_width(self.wav.getsampwidth()),
                channels=self.wav.getnchannels(),
                rate=self.wav.getframerate(),
                output=True,
                stream_callback=self.callback)

        self.stream.start_stream()
   
    def playWav(self):
        self.isPlaying = True
        self.openWav()
        self.startStream()
        self.tkRoot.after(self.wavDuration, self.closeWav)
    
    #
    # We scheduled this method to be queued the in the Tk event schedule
    #
    def closeWav(self):
        self.stream.stop_stream()
        self.stream.close()
        self.isPlaying = False
        
        # this method is called in the tkRoot event thread, so we can safely check if we have any play requests
        if self.playRequestQueue :
            self.decrementPlayRequestQueue()
            self.playWav()
        
        
    #
    #
    #
    def incrementPlayRequestQueue(self):
        self.playRequestQueue = self.playRequestQueue + 1
        self.changed.fire("playRequestQueueChanged",self.playRequestQueue)
    
    def decrementPlayRequestQueue(self):
        self.playRequestQueue = self.playRequestQueue - 1
        self.changed.fire("playRequestQueueChanged",self.playRequestQueue)
    
    #
    # This method is called from within the Tkinter event thread.
    #
    def queueWav(self):
        if not self.isPlaying:
            self.playWav()
        else:
            self.incrementPlayRequestQueue()
        

