#!/usr/bin/env python
"""
Motorized or piezo o3 stage functionality 
Aditya 08/21
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.baseClasses.lockModule as lockModule


class o3StageFunctionality(hardwareModule.HardwareFunctionality):
    
    o3StagePosition = QtCore.pyqtSignal(float)

    def __init__(self, o3_stage = None, **kwds):
        super().__init__(**kwds)
        self.o3_stage = o3_stage

    def goAbsolute(self, o3_pos):
        
        self.o3_position = o3_pos
        self.o3_stage.o3MoveTo(self.o3_position)
        self.o3StagePosition.emit(self.o3_position)

    def goRelative(self, o3_delta):
        o3_pos = self.o3_position + o3_delta
        self.goAbsolute(o3_pos)

        
class o3StageFunctionalityBuffered(hardwareModule.BufferedFunctionality):
    
    o3StagePosition = QtCore.pyqtSignal(float)

    def __init__(self, o3_stage = None, **kwds):
        super().__init__(**kwds)
        self.o3_stage = o3_stage

    def goAbsolute(self, o3_pos):
        if (o3_pos != self.o3_position):
            
            self.maybeRun(task = self.o3MoveTo,
                          args = [o3_pos],
                          ret_signal = self.o3StagePosition)

    def goRelative(self, o3_delta):
        o3_pos = self.o3_position + o3_delta
        self.goAbsolute(o3_pos)

    def o3MoveTo(self, o3_pos):
        self.o3_stage.o3MoveTo(o3_pos)
        self.o3_position = o3_pos
        return o3_pos
        

class o3Stage(hardwareModule.HardwareModule):
    
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")
        self.o3_stage_functionality = None
        self.o3_stage = None
                                                            
    def cleanUp(self, qt_settings):
        if self.o3_stage_functionality is not None:
            self.o3_stage.shutDown()

    def processMessage(self, message):
        
        if message.isType("get functionality"):
            if (message.getData()["name"] == self.module_name):
                if self.o3_stage_functionality is not None:
                    message.addResponse(
                        halMessage.HalMessageResponse(source = self.module_name,
                                                      data = {"functionality" : self.o3_stage_functionality}))
