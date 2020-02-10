# test1.py
# Created 23 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

import json
import datetime
from tests.classes.test import callback_any_shadow_update
from tests.classes.test import Test
from tests.classes.globals import globals


class Test1(Test):
    def __init__(self):
        super().__init__(1,
                         "Update Frequency",
            "Verify that device checks the shadow in the cloud periodically, and that valve state is never unknown")

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
        print("\rWaiting for device to update the shadow, iteration " + str(self.iteration + 1))
        self.advance()

    # step 7
    def verify_one_iteration(self):
        super().verify_one_iteration()

        if globals.update_accepted:
            globals.update_accepted = False
            duration = datetime.datetime.now() - self.iteration_start
            print("\rShadow update received (" + self.format_time(duration) + ")")
            print(globals.separator)
            self.check_valve_params()
            self.advance()

    # step 8
    def loop_back(self):
        super().loop_back()

    # step 9
    def finish_test(self):
        super().finish_test()

