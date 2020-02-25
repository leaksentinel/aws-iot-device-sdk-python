# test2.py
# Created 25 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

import json
import datetime

from tests.classes.shadow import shadow_items
from tests.classes.globals import globals
from tests. classes.test import Test
from tests.classes.test import callback_my_shadow_update
from tests.classes.test import callback_any_shadow_update

test_params = [
    shadow_items.requestedValveStateCounter,
    shadow_items.requestedValveStateReq
]

class Test4(Test):
    def __init__(self):
        super().__init__(4,
                         "Open and Close Valve",
                         "Verify that the device responds to requests to open and close the valve")
    # steps 0-9
    # see test.py

    # step 10
    def run_one_iteration(self):
        super().run_one_iteration()

        # register to receive all update messages
        self.shadow_handler.shadowRegisterUpdateCallback(callback_any_shadow_update)

        # get current value of params we're interested in
        globals.outgoing_dict = {}
        for item in test_params:
            if item.get_reported_value_from_json_dict():

                # if this is counter, bump it
                if item == shadow_items.requestedValveStateCounter:
                    icount = int(item.reported_value)
                    item.desired_value = str(icount + 1)
                    print("\rChanging " + item.key + " from " + item.reported_value\
                          + " to " + item.desired_value + ", iteration " + str(self.iteration + 1))


                # if this is valve state, get opposite state
                if item == shadow_items.requestedValveStateReq:
                    if item.val1 == item.reported_value:
                        item.desired_value = item.val2
                    else:
                        item.desired_value = item.val1
                    if item.desired_value == "1":
                        print("\rAttempting to open the valve")
                    else:
                        print("\rAttempting to close the valve")

                # attempt to update values
                item.set_desired_value_to_json_dict()

        json_str = json.dumps(globals.outgoing_dict)
        self.shadow_handler.shadowUpdate(json_str, callback_my_shadow_update, 5)

        # wait for reply
        self.advance()

    # step 7
    def verify_one_iteration(self):
        if globals.update_accepted:
            globals.update_accepted = False
            self.check_valve_params()
            duration = datetime.datetime.now() - self.iteration_start
            # print("\rUpdate request was accepted by Shadow (" + self.format_time(duration) + ")")
            matches = 0
            for item in test_params:
                if item.get_reported_value_from_json_dict():
                    if item.desired_value == item.reported_value:
                        matches += 1
                        duration = datetime.datetime.now() - self.cycle_start
                        # print("\r" + item.key + " is now reported as " + item.reported_value
                        #       + " (" + self.format_time(duration) + ")")
            if matches == len(test_params):
                print("\rValve state was successfully changed"\
                      + " (" + self.format_time(duration) + ")")
                print(globals.separator)
                self.advance()

        elif self.step == 7:
            # display timer while we wait
            if self.cycle_start != None:
                self.display_cycle_timer()

    # step 12-13
    # see test.py
