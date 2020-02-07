# test2.py
# Created 25 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

import json
import datetime

from classes.shadow import shadow_items
from classes.globals import globals
from classes.test import Test

test_params = [
    shadow_items.adcAdcNumsamples,
    shadow_items.motorDelayT,

    # ball valve
    shadow_items.valveType,
    shadow_items.motorMaxI,
    shadow_items.motorMaxT,
    shadow_items.motorBackT,

    # gate valve
    shadow_items.valveType,
    shadow_items.motorMaxI,
    shadow_items.motorMaxT,
    shadow_items.motorBackT
]

class Test2(Test):
    def __init__(self):
        super().__init__(2,
                         "Change Single Parameter",
                         "Verify that the device responds to requests to change a single parameter")

    # step 0
    def prepare_for_test(self):
        super().prepare_for_test()

    # step 1
    def send_initial_update(self):
        super().send_initial_update()

        # send "connect_not_flowing" and "sleep_multiplier" values to shadow
        dict = {'connect_not_flowing': str(self.args.connect_not_flowing),
                'sleep_multiplier': str(self.args.sleep_multiplier)}
        wifi_dict = {'wifi': dict}
        desired_dict = {'desired': wifi_dict}
        state_dict = {'state': desired_dict}
        json_str = json.dumps(state_dict)
        globals.update_accepted = False
        print("Sending connect_not_flowing and sleep_multiplier to shadow")
        self.shadow_handler.shadowUpdate(json_str, callback_set_initial_shadow_values, 5)
        self.advance()

    # step 2
    def verify_initial_update(self):
        if globals.update_accepted:
            globals.update_accepted = False
            self.advance()

        else:
            # check for time out
            super().verify_initial_update()


    # step 3
    def prepare_for_iteration(self):
        super().prepare_for_iteration()

        # get current shadow values
        print("\rFetching shadow value, iteration " + str(self.iteration + 1))
        self.shadow_handler.shadowGet(callback_shadow_get, 5)
        self.advance()

    # step 4
    def run_one_iteration(self):
        super().run_one_iteration()

        if globals.get_accepted:
            globals.get_accepted = False

            # get current value of param we're interested in
            item: ShadowItem = self.get_current_item()
            if item.set_reported_value_from_json(globals.payload_dict):

                # get desired val of same param
                if item.val1 == item.reported_value:
                    item.desired_value = item.val2
                else:
                    item.desired_value = item.val1

                # attempt to update value
                print("Changing " + item.key + " from " + item.reported_value + " to " + item.desired_value)
                json_str = item.set_desired_value_to_json()
                self.shadow_handler.shadowUpdate(json_str, callback_my_shadow_update, 5)

                # register to receive all update messages
                self.shadow_handler.shadowRegisterUpdateCallback(callback_any_shadow_update)

                # wait for reply
                self.advance()

    # step 5
    def verify_one_iteration(self):
        super().verify_one_iteration()

        if globals.update_accepted:
            globals.update_accepted = False
            duration = datetime.datetime.now() - self.iteration_start
            # print("\rUpdate request was accepted by Shadow (" + self.format_time(duration) + ")")
            item = self.get_current_item()
            if item.set_reported_value_from_json(globals.payload_dict):
                if item.desired_value == item.reported_value:
                    duration = datetime.datetime.now() - self.cycle_start
                    print("\r" + item.key + " is now reported as " + item.reported_value
                          + " (" + self.format_time(duration) + ")")
                    print(globals.separator)
                    self.advance()

        elif self.step == 5:
            # display timer while we wait
            if self.cycle_start != None:
                duration = datetime.datetime.now() - self.cycle_start
                print("\rWaiting for response (" + self.format_time(duration) + ")", end='')

    # step 6
    def loop_back(self):
        super().loop_back()

    # step 7
    def finish_test(self):
        super().finish_test()

    def get_current_item(self):
        index = self.iteration % len(test_params)
        return test_params[index]

# callback functions
def callback_set_initial_shadow_values(payload, responseStatus, token):
    # print("callback_set_initial_shadow_values")
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
        globals.abort_flag = True
        globals.abort_reason = "Initial Shadow update request timed out"
        return
    if responseStatus == "accepted":
        globals.update_accepted = True
        print("Shadow update request was accepted")
        print(globals.separator)
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")
        globals.abort_flag = True
        globals.abort_reason = "Error - shadow rejected our initial update request"

# call us back when our get request is handled
def callback_shadow_get(payload, responseStatus, token):
    # print("callback_shadow_get")
    # print("\r" + responseStatus + "                        ")
    globals.payload_dict = json.loads(payload)
    # print("state: " + str(payloadDict["state"]))
    globals.get_accepted = True

# call us back when our request to update a parameter value is accepted
def callback_my_shadow_update(payload, responseStatus, token):
    # print("callback_my_shadow_update")
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
        globals.abort_flag = True
        globals.abort_reason = "Shadow update request timed out"
        return
    if responseStatus == "accepted":
        globals.update_accepted = False  # this is our own update, need to wait for one from device
        print("Shadow update request was accepted")
        print(globals.separator)
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")
        globals.abort_flag = True
        globals.abort_reason = "Error - shadow rejected our initial update request"

# call us back whenever an updated message is generated, regardless of token
def callback_any_shadow_update(payload, responseStatus, token):
    # print("callback_any_shadow_update")
    # print("\r" + responseStatus + "                        ")
    globals.payload_dict = json.loads(payload)
    # print("state: " + str(payloadDict["state"]))
    globals.update_accepted = True

