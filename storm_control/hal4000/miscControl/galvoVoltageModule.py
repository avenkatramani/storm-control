#!/usr/bin/env python
"""
Voltage controlled Z stage functionality.

Hazen 05/17
George 02/18 
Aditya Venkatramani 04/21

Adapted from voltageZModule
"""

from PyQt5 import QtCore
import numpy as np

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.daqModule as daqModule
import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.baseClasses.lockModule as lockModule


class GalvoVoltageFunctionality(hardwareModule.HardwareFunctionality):
    
    voltage = QtCore.pyqtSignal(float)

    def __init__(self, ao_fn = None, **kwds):
        super().__init__(**kwds)
        self.ao_fn = ao_fn
        self.film_volt = None
        self.maximum = self.getParameter("maximum")
        self.minimum = self.getParameter("minimum")
        
        self.ao_fn.filming.connect(self.handleFilming)

    def getDaqWaveform(self, waveform):
        return daqModule.DaqWaveform(source = self.ao_fn.getSource(),
                                     waveform = waveform)
            
    def goAbsolute(self, volt):
        if self.ao_fn.amFilming():
            return
        self.volt = volt
        self.ao_fn.output(volt)
        self.voltage.emit(self.volt)
        
    def goRelative(self, dv):
        volt = self.volt + dv
        self.goAbsolute(volt)

    def handleFilming(self, filming):
        
        # Record current z position at the start of the film.
        if filming:
            self.film_z = self.z_position

        # Return to the current z position at the end of the film.
        else:
            self.goAbsolute(self.film_z)

    def haveHardwareTiming(self):
        return True


class VoltageZ(hardwareModule.HardwareModule):
    """
    This is a Z-piezo stage in analog control mode.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")
        self.z_stage_functionality = None

    def cleanUp(self, qt_settings):
        if self.z_stage_functionality is not None:
            self.z_stage_functionality.goAbsolute(
                    self.z_stage_functionality.getMinimum())
        
    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.z_stage_functionality = VoltageZFunctionality(
                  ao_fn = response.getData()["functionality"],
                  parameters = self.configuration.get("parameters"),
                  microns_to_volts = self.configuration.get("microns_to_volts"))

    def processMessage(self, message):

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(
               m_type = "get functionality",
               data = {"name" : self.configuration.get("ao_fn_name")}))
        
        elif message.isType("get functionality"):
            if (message.getData()["name"] == self.module_name):
                if self.z_stage_functionality is not None:
                    message.addResponse(
                        halMessage.HalMessageResponse(source = self.module_name,
                        data = {"functionality" : self.z_stage_functionality}))

