# test5.py
# Created 25 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

import json
import datetime
import urllib.request
import urllib.error

from tests.classes.shadow import shadow_items
from tests.classes.globals import globals
from tests.classes.test import Test
from tests.classes.test import callback_my_shadow_update
from tests.classes.test import callback_any_shadow_update

test_params = [
    shadow_items.requestedValveStateCounter,
    shadow_items.requestedValveStateReq
]

class Test5(Test):
    def __init__(self):
        super().__init__(5,
                         "Button-Shadow Open-Close",
                         "Verify all permutations of opening and closing valve, using buttons and shadow commands")

        self.button_is_pressed = False
        self.button_start_time = None

        self.BUTTON = 1
        self.SHADOW = 2
        self.OPEN = 1
        self.CLOSE = 2

        self.test_matrix = [
            {'method': self.SHADOW, 'direction': self.OPEN},
            {'method': self.SHADOW, 'direction': self.CLOSE},
            {'method': self.BUTTON, 'direction': self.OPEN},
            {'method': self.SHADOW, 'direction': self.CLOSE},
            {'method': self.SHADOW, 'direction': self.OPEN},
            {'method': self.BUTTON, 'direction': self.CLOSE},
            {'method': self.BUTTON, 'direction': self.OPEN},
            {'method': self.BUTTON, 'direction': self.CLOSE},
        ]

        self.matrix_index = 0
        self.matrix_count = 0

    def access_url(self,req):
        try:
            x = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            if e.code in (..., 403, ...):
                return

    def pwr_button_push(self):
        print("pwr_button_push")
        self.access_url("https://o1.prota.space/mib/do/push?_id=cd8aeed89601117383ac7411d8e9f4d5")

    def pwr_button_release(self):
        print("pwr_button_release")
        self.access_url("https://o1.prota.space/mib/do/release?_id=cd8aeed89601117383ac7411d8e9f4d5")

    def wifi_button_push(self):
        print("wifi_button_push")
        self.access_url("https://o1.prota.space/mib/do/push?_id=69ce2a6ade53c6aae168fa1785d1b450")

    def wifi_button_release(self):
        print("wifi_button_release")
        self.access_url("https://o1.prota.space/mib/do/release?_id=69ce2a6ade53c6aae168fa1785d1b450")

    # step 0
    def prepare_for_test(self):
        super().prepare_for_test()
        self.matrix_index = 0
        self.matrix_count = 0

    # steps 1-3
    # see test.py

    # step 4
    def verify_first_get(self):
        super().verify_first_get()

        # if first 'get' completed ok, see what the current state of the valve is
        if self.step == 5:
            if self.valve_type == 1:
                print("Testing gate valve")
            else:
                print("Tasting ball valve")
                
            # if valve is currently open, start our test with entry 1 (not 0) and wrap around test_matrix
            item = shadow_items.valveState
            if item.reported_value == "1":
                print("Valve is open to start this test")
                self.matrix_index = 1  # start our test from second entry
            elif item.reported_value == "2":
                print("Valve is closed to start this test")
                self.matrix_index = 0
            else:
                print("Valve is neither open nor closed?!?")
                exit(4)

    # step 5-9
    # see test.py

    # step 10
    def run_one_iteration(self):
        super().run_one_iteration()

        # register to receive all update messages
        self.shadow_handler.shadowRegisterUpdateCallback(callback_any_shadow_update)

        # get test matrix entry for this index
        entry = self.test_matrix[self.matrix_index]

        # tell them what we are about to do
        if entry['method']== self.BUTTON:
            method_str = "button"
        else:
            method_str = "shadow"
        if entry['direction'] == self.OPEN:
            direction_str = "Opening"
        else:
            direction_str = "Closing"
        print("\r" + direction_str + " valve using " + method_str)

        # if this matrix entry is a button press...
        if entry['method'] == self.BUTTON:

            # press the appropriate button
            if entry['direction'] == self.OPEN:
                self.pwr_button_push()
            else:
                self.wifi_button_push()

            # remember press time so we can unpress at the right time
            self.button_is_pressed = True
            self.button_start_time = datetime.datetime.now()

        # if this is a shadow command...
        else:
            # no button press this time
            self.button_is_pressed = False

            # get the current counter value and bump it
            item = shadow_items.requestedValveStateCounter
            item.get_reported_value_from_json_dict()
            icount = int(item.reported_value)
            item.desired_value = str(icount + 1)

            # send that out as part of json dictionary
            globals.outgoing_dict = {}
            item.set_desired_value_to_json_dict()

            # set the desired valve state
            item = shadow_items.requestedValveStateReq
            if entry['direction'] == self.OPEN:
                item.desired_value = "1"
            else:
                item.desired_value = "2"
            item.set_desired_value_to_json_dict()

            json_str = json.dumps(globals.outgoing_dict)
            self.shadow_handler.shadowUpdate(json_str, callback_my_shadow_update, 5)

        # wait for shadow to update
        self.advance()

    # step 11
    def verify_one_iteration(self):
        # get test matrix entry for this index
        entry = self.test_matrix[self.matrix_index]

        # if this matrix entry is a button press...
        if entry['method'] == self.BUTTON and self.button_is_pressed:

            # have we held it down for long enough?
            duration = (datetime.datetime.now() - self.button_start_time).total_seconds()
            if duration >= 8:
                # yes, unpress it
                if entry['direction'] == self.OPEN:
                    self.pwr_button_release()
                else:
                    self.wifi_button_release()
                self.button_is_pressed = False
            else:
                return  # no, wait some more

        # see if valve state has resolved
        if globals.update_accepted:
            globals.update_accepted = False
            self.check_valve_params()

            item = shadow_items.valveState
            item.get_reported_value_from_json_dict()

            if entry['direction'] == int(item.reported_value):
                if entry['direction'] == self.OPEN:
                    dir_str = "OPEN"
                else:
                    dir_str = "CLOSED"
                duration = datetime.datetime.now() - self.cycle_start
                print("\rValve state was reported as " + dir_str \
                      + " (" + self.format_time(duration) + ")")
                print(globals.separator)
                self.advance()

        else:
            super().verify_one_iteration()

    # step 12
    def loop_back(self):
        self.matrix_index += 1
        if self.matrix_index >= len(self.test_matrix):
            self.matrix_index = 0
        self.matrix_count += 1
        if self.matrix_count >= len(self.test_matrix):
            # finished one iteration of this test
            super().loop_back()
        else:
            self.step = 9

    # step 13
    # see test.py
