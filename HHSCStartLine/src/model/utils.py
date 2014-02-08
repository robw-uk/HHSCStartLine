'''
Created on 8 Feb 2014

@author: MBradley
'''
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
