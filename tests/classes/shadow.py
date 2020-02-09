# shadow.py
# Created 25 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

from enum import Enum
import json

class ShadowCategory(Enum):
    DEVICE = "device"
    SHADOW = "shadow"
    VALVE = "valve"
    ADC = "adc"
    BATTERY = "battery"
    DSP = "dsp"
    MOTOR = "motor"
    WIFI = "wifi"
    ACTION = "action"
    REQUESTED = "requested"
    NONE = "none"

class ShadowItemType(Enum):
    INT = 1
    STRING = 2
    BOOL = 3
    DOUBLE = 4
    ENUM = 5

class ShadowItem:
    def __init__(self, category:ShadowCategory, key:str, type:ShadowItemType,
                 label:str, val1:str = None, val2:str = None):
        self.category:ShadowCategory = category
        self.key = key
        self.type:ShadowItemType = type
        self.label = label
        self.val1 = val1
        self.val2 = val2
        self.desired_value = None
        self.reported_value = None

    # parse a JSON dictionary, locate our shadow item
    # if found, store its value in self.reported_value as a string
    def get_reported_value_from_json_dict(self, dict):
        category = self.category.value
        key = self.key
        if "state" in dict:
            state_dict = dict["state"]
            if "reported" in state_dict:
                reported_dict = state_dict["reported"]
                if self.category == ShadowCategory.NONE:
                    if key in reported_dict:
                        self.reported_value = reported_dict[key]
                        return True
                else:
                    if category in reported_dict:
                        category_dict = reported_dict[category]
                        if key in category_dict:
                            self.reported_value = category_dict[key]
                            return True
        return False

    # use self.desired_value to create a JSON string
    def set_desired_value_to_json_str(self):
        # get desired value from ShadowItem and turn it into JSON
        category = self.category.value
        value = self.desired_value
        key = self.key
        item_dict = {key: value}
        if self.category == ShadowCategory.NONE:
            desired_dict = {'desired': item_dict}
            state_dict = {'state': desired_dict}
            json_str = json.dumps(state_dict)
            return json_str
        else:
            category_dict = {category: item_dict}
            desired_dict = {'desired': category_dict}
            state_dict = {'state': desired_dict}
            json_str = json.dumps(state_dict)
            return json_str

    # use self.desired_value to create a JSON string from two shadow items in the same category
    def set_desired_values_to_json_str(self, item2):
        category = self.category.value
        value1 = self.desired_value
        key1 = self.key
        value2 = item2.desired_value
        key2 = item2.key
        item_dict = {key1: value1, key2: value2}
        if self.category == ShadowCategory.NONE:
            desired_dict = {'desired': item_dict}
            state_dict = {'state': desired_dict}
            json_str = json.dumps(state_dict)
            return json_str
        else:
            category_dict = {category: item_dict}
            desired_dict = {'desired': category_dict}
            state_dict = {'state': desired_dict}
            json_str = json.dumps(state_dict)
            return json_str

class ShadowItems:
    def __init__(self):
        self.deviceMacAddr =             ShadowItem(ShadowCategory.DEVICE, "mac_addr", ShadowItemType.STRING, "MAC Addr")
        self.deviceFwVersion =           ShadowItem(ShadowCategory.DEVICE, "fw_version", ShadowItemType.STRING, "Firmware Version")
        self.deviceProvisioned =         ShadowItem(ShadowCategory.DEVICE, "dev_provisioned", ShadowItemType.BOOL, "Provisioned")
        self.deviceInstalled =           ShadowItem(ShadowCategory.DEVICE, "dev_installed", ShadowItemType.BOOL, "Installed")
        self.deviceTested =              ShadowItem(ShadowCategory.DEVICE, "dev_tested", ShadowItemType.BOOL, "Tested")

        self.valveType =                 ShadowItem(ShadowCategory.VALVE, "valve_type", ShadowItemType.ENUM, "Valve Type", "1", "2")
        self.valveState =                ShadowItem(ShadowCategory.VALVE, "valve_state", ShadowItemType.ENUM, "Valve State", "1", "2")

        self.batteryBatteryState =       ShadowItem(ShadowCategory.BATTERY, "battery_state", ShadowItemType.ENUM, "Battery State")
        self.batterySourceState =        ShadowItem(ShadowCategory.BATTERY, "source_state", ShadowItemType.ENUM, "Source State")
        self.batteryBatteryVoltage =     ShadowItem(ShadowCategory.BATTERY, "battery_voltage", ShadowItemType.INT, "Battery Voltage")
        self.batteryBusVoltage =         ShadowItem(ShadowCategory.BATTERY, "bus_voltage", ShadowItemType.INT, "Bus Voltage")
        self.batteryBusCurrent =         ShadowItem(ShadowCategory.BATTERY, "bus_current", ShadowItemType.INT, "Bus Current")
        self.batteryBatteryCurrent =     ShadowItem(ShadowCategory.BATTERY, "battery_current", ShadowItemType.INT, "Battery Current")
        self.batterySysVoltage =         ShadowItem(ShadowCategory.BATTERY, "sys_voltage", ShadowItemType.INT, "Sys Voltage")
        self.batteryTsTemperatureate =   ShadowItem(ShadowCategory.BATTERY, "ts_temperature", ShadowItemType.INT, "TS Temperature")
        self.batteryDieTemperature =     ShadowItem(ShadowCategory.BATTERY, "die_temperature", ShadowItemType.INT, "Die Temperature")
        self.batteryChargeVoltage =      ShadowItem(ShadowCategory.BATTERY, "charge_voltage", ShadowItemType.INT, "Charge Voltage")
        self.batteryChargeCurrent =      ShadowItem(ShadowCategory.BATTERY, "charge_current", ShadowItemType.INT, "Charge Current")

        self.adcAdcNumsamples =          ShadowItem(ShadowCategory.ADC, "adc_numsamples", ShadowItemType.INT, "ADC Num Samples", "32", "24")

        self.motorMotorState =           ShadowItem(ShadowCategory.MOTOR, "motor_state", ShadowItemType.ENUM, "Motor State")
        self.motorDelayT =               ShadowItem(ShadowCategory.MOTOR, "delayT", ShadowItemType.INT, "Delay T", "250", "251")
        self.motorRunTime =              ShadowItem(ShadowCategory.MOTOR, "runTime", ShadowItemType.INT, "Run Time")

        self.motorMaxI =             ShadowItem(ShadowCategory.MOTOR, "maxI", ShadowItemType.DOUBLE, "Max I (amp)", "0.60", "0.61")
        self.motorMaxT =             ShadowItem(ShadowCategory.MOTOR, "maxT", ShadowItemType.INT, "Max T (sec)", "14", "15")
        self.motorBackT =            ShadowItem(ShadowCategory.MOTOR, "backT", ShadowItemType.INT, "Back-off Time (ms)", "500", "501")

        self.requestedValveStateReq =    ShadowItem(ShadowCategory.REQUESTED, "valve_state_req", ShadowItemType.ENUM, "Valve State Req", "1", "2")
        self.requestedValveStateCounter = ShadowItem(ShadowCategory.REQUESTED, "valve_state_counter", ShadowItemType.INT, "Valve State Counter")

        self.wifiSsid =                  ShadowItem(ShadowCategory.WIFI, "ssid", ShadowItemType.STRING, "SSID")
        self.wifiRssi =                  ShadowItem(ShadowCategory.WIFI, "rssi", ShadowItemType.INT, "RSSI")
        self.wifiDisconnectTime =        ShadowItem(ShadowCategory.WIFI, "disconnect_time", ShadowItemType.INT, "Disconnect Time")
        self.wifiConnectNotFlowing =     ShadowItem(ShadowCategory.WIFI, "connect_not_flowing", ShadowItemType.INT, "Connect Not Flowing")
        self.wifiConnectSleepMultiplier = ShadowItem(ShadowCategory.WIFI, "connect_sleep_multiplier", ShadowItemType.INT, "Connect Sleep Multiplier")

        self.noneFreeHeap =              ShadowItem(ShadowCategory.NONE, "free_heap", ShadowItemType.INT, "Free Heap")
        self.noneUpTime =                ShadowItem(ShadowCategory.NONE, "uptime", ShadowItemType.INT, "Up Time")
        self.noneOtaChecked =            ShadowItem(ShadowCategory.NONE, "ota_checked", ShadowItemType.INT, "OTA Checked")
        self.noneShadowVer =             ShadowItem(ShadowCategory.NONE, "shadow_ver", ShadowItemType.INT, "Shadow Version")

shadow_items = ShadowItems()
