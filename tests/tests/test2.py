# test2.py
# Created 25 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

import json
import datetime

from tests.classes.shadow import shadow_items
from tests.classes.shadow import ShadowItem
from tests.classes.globals import globals
from tests.classes.test import Test
from tests.classes.test import callback_my_shadow_update
from tests.classes.test import callback_any_shadow_update

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
        super(). send_initial_update()

    # step 2
    def verify_initial_update(self):
        super().verify_initial_update()

    # step 3
    def send_initial_get(self):
        super().send_initial_get()

    # step 4
    def verify_initial_get(self):
        super().verify_initial_get()

    # step 5
    def delay_before_iteration(self):
        super().delay_before_iteration()

    # step 6
    def run_one_iteration(self):
        super().run_one_iteration()

        # register to receive all update messages
        self.shadow_handler.shadowRegisterUpdateCallback(callback_any_shadow_update)

        # get current value of param we're interested in
        item: ShadowItem = self.get_current_item()
        if item.get_reported_value_from_json_dict():

            # get desired val of same param
            if item.val1 == item.reported_value:
                item.desired_value = item.val2
            else:
                item.desired_value = item.val1

            # announce which param we are changing
            print("\rChanging " + item.key + " from " + item.reported_value\
                  + " to " + item.desired_value + ", iteration " + str(self.
                                                                       iteration + 1))

            # attempt to update value
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
            item = self.get_current_item()
            if item.get_reported_value_from_json_dict():
                if item.desired_value == item.reported_value:
                    duration = datetime.datetime.now() - self.cycle_start
                    print("\r" + item.key + " is now reported as " + item.reported_value
                          + " (" + self.format_time(duration) + ")")
                    print(globals.separator)
                    self.advance()

        elif self.step == 7:
            # display timer while we wait
            if self.cycle_start != None:
                self.display_cycle_timer()

    # step 8
    def loop_back(self):
        super().loop_back()

    # step 9
    def finish_test(self):
        super().finish_test()

    def get_current_item(self):
        index = self.iteration % len(test_params)
        return test_params[index]

