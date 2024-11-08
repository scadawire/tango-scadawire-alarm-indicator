import time
from tango import AttrQuality, AttrWriteType, DispLevel, DevState, Attr, CmdArgType, UserDefaultAttrProp, DeviceProxy
from tango.server import Device, attribute, command, DeviceMeta
from tango.server import class_property, device_property
from tango.server import run
import os
import json
from json import JSONDecodeError
import random

class AlarmIndicator(Device, metaclass=DeviceMeta):
    pass

    target_device = device_property(dtype=str, default_value="")
    target_attributes_alarm = device_property(dtype=str, default_value="")
    target_attributes_warning = device_property(dtype=str, default_value="")
    target_attributes_valid = device_property(dtype=str, default_value="")
    target_attribute_on_value = device_property(dtype=str, default_value="1")
    target_attribute_off_value = device_property(dtype=str, default_value="0")
    
    device = 0
    targetAttributes = {}
    alarmLookup = {}
    
    @command()
    def demo_valid(self):
        self.alarmLookup["demo"] = "valid"
        self.handleAlarmState()
    
    @command()
    def demo_warning(self):
        self.alarmLookup["demo"] = "warning"
        self.handleAlarmState()
    
    @command()
    def demo_alarm(self):
        self.alarmLookup["demo"] = "alarm"
        self.handleAlarmState()
    
    #@command()
    #def disco(self):
    #    for _ in range(60):
    #        self.alarmLookup["demo"] = random.choice(["alarm", "warning", "valid"])
    #        self.handleAlarmState()
    #        time.sleep(1)
    
    @command()
    def test(self):
        for _ in range(60):
            qualities = ["valid", "warning", "alarm", "valid"]
            for i in states:
                self.alarmLookup["demo"] = qualities[i]
                self.handleAlarmState()
                time.sleep(5)
        
    @command(dtype_in=[str])
    def handle_alarm_change(self, payload):
        print("handling alarm change")
        print("received payload:")
        print(payload)
        alarmId = payload[0]
        quality = payload[1]
        previous_quality = payload[2]
        attribute_id = payload[3]
        attribute_name = payload[4]
        device_id = payload[5]
        device_name = payload[6]
        alarmLookup[attribute_id] = quality
        print("new alarmLookup:")
        print(alarmLookup)
        self.handleAlarmState()
        
    def mostCriticalQuality(self):
        mostCriticalQuality = "valid"
        for key in self.alarmLookup:
            quality = self.alarmLookup[key]
            if(quality == "warning" and mostCriticalQuality == "valid"):
                mostCriticalQuality = "warning"
            if(quality == "alarm" or quality == "changing" or quality == "invalid"):
                mostCriticalQuality = "alarm"
        return mostCriticalQuality
    
    def handleAlarmState(self):
        quality = self.mostCriticalQuality()
        qualityTargetValue = {}
        qualityTargetValue["always"] = self.target_attribute_on_value
        qualityTargetValue["alarm"] = self.target_attribute_off_value
        if(quality == "alarm"): qualityTargetValue["alarm"] = self.target_attribute_on_value
        qualityTargetValue["warning"] = self.target_attribute_off_value
        if(quality == "warning"): qualityTargetValue["warning"] = self.target_attribute_on_value
        qualityTargetValue["valid"] = self.target_attribute_off_value
        if(quality == "valid"): qualityTargetValue["valid"] = self.target_attribute_on_value
        for(quality in qualityTargetValue):
            targetAttributes = self.targetAttributes[quality]
            for(attributeName in targetAttributes):
                self.device.write_attribute(attributeName, qualityTargetValue[quality])
        
    def init_device(self):
        self.set_state(DevState.INIT)
        self.get_device_properties(self.get_device_class())
        self.device = DeviceProxy(self.target_device)
        self.targetAttributes["alarm"] = self.target_attributes_alarm.split(";")
        self.targetAttributes["warning"] = self.target_attributes_warning.split(";")
        self.targetAttributes["valid"] = self.target_attributes_valid.split(";")
        self.targetAttributes["always"] = self.target_attributes_always.split(";")
        self.set_state(DevState.ON)
        self.handleAlarmState()

if __name__ == "__main__":
    deviceServerName = os.getenv("DEVICE_SERVER_NAME")
    run({deviceServerName: AlarmIndicator})