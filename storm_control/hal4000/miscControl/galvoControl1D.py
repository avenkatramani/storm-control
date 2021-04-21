#!/usr/bin/python
"""
HAL module for Galvo control.
Aditya Venkatramani 04/21
"""

from PyQt5 import QtCore
import numpy
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.sc_library.halExceptions as halExceptions

import storm_control.sc_hardware.baseClasses.daqModule as daqModule
import storm_control.sc_hardware.baseClasses.amplitudeModule as amplitudeModule
import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class GalvoFunctionality(amplitudeModule.AmplitudeFunctionalityBuffered):

    galvoVoltage = QtCore.pyqtSignal(float)
    controlMessage = QtCore.pyqtSignal(object)

    def __init__(self, ao_fn = None, galvoVoltage= 0.0, maximum = 1.0, minimum = 0.0, scan = "None", **kwds):
        super().__init__(**kwds)
        self.ao_fn = ao_fn
        self.film_volt = None
        self.maximum = maximum
        self.minimum = minimum
        self.volt = 0
        self.scan = scan
        self.waveform = None

        self.ao_fn.filming.connect(self.handleFilming)

    
    def getDaqWaveform(self):
        waveform = numpy.array(list(map(float, self.scan.split(",")))) 
        self.scan_max = len(waveform)
        return waveform
        #return daqModule.DaqWaveform(source = self.ao_fn.getSource(),
        #                             waveform = waveform)
    
    def goAbsolute(self, volt):
        if self.ao_fn.amFilming():
            return
        self.volt = volt
        self.ao_fn.output(volt/1000.0)
        self.galvoVoltage.emit(self.volt)

    def goRelative(self, dv):
        volt = self.volt + dv
        self.goAbsolute(volt)
        
    def zero(self):
        self.goAbsolute(0.0)
        

    def handleFilming(self, filming):

        # Record current z position at the start of the film.
        if filming:
            self.film_volt = self.volt

        # Return to the current z position at the end of the film.
        else:
            self.goAbsolute(self.film_volt)

    def setTimingFunctionality(self, functionality):
        self.timing_functionality = functionality.getCameraFunctionality()
        self.timing_functionality.newFrame.connect(self.handleNewFrame)

    def startFilm(self, film_settings):
        self.scan_counter = 0
        if self.scan != "None":
            self.waveform = self.getDaqWaveform()
            #self.controlMessage.emit(halMessage.HalMessage(m_type = "daq waveforms",
            #                                                   data = {"waveforms" : [waveform]}))
        
    def handleNewFrame(self, frame):
        if self.waveform is not None:
            if (self.scan_counter < self.scan_max):
                self.goAbsolute(self.waveform[self.scan_counter])
                self.scan_counter += 1
        
    
class galvoModule(amplitudeModule.AmplitudeModule):
    """
    This is a 1D galvo using analog control
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        
        self.configuration = module_params.get("configuration")
        self.galvo_functionality = None
        self.maximum = self.configuration.get("maximum")
        self.minimum = self.configuration.get("minimum")
        self.scan = self.configuration.get("scan")

        

    def cleanUp(self, qt_settings):
        if self.galvo_functionality is not None:
            self.galvo_functionality.goAbsolute(0.0)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.galvo_functionality = GalvoFunctionality(
                  device_mutex = self.device_mutex,
                  ao_fn = response.getData()["functionality"],
                  maximum = self.minimum,
                  minimum = self.maximum,
                  scan = self.scan)

    def processMessage(self, message):

        if message.isType("configuration"):
            if message.sourceIs("timing"):
                self.galvo_functionality.setTimingFunctionality(message.getData()["properties"]["functionality"])
                
        elif message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(
               m_type = "get functionality",
               data = {"name" : self.configuration.get("ao_fn_name")}))

        elif message.isType("get functionality"):
            if (message.getData()["name"] == self.module_name):
                if self.galvo_functionality is not None:
                    message.addResponse(
                        halMessage.HalMessageResponse(source = self.module_name,
                        data = {"functionality" : self.galvo_functionality}))

        elif message.isType("start film"):
            self.galvo_functionality.startFilm(message.getData()["film settings"])