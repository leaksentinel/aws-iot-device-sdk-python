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

    # steps 0-9
    # see test.py

    # step 10
    def run_one_iteration(self):
        super().run_one_iteration()
        # register to receive all update messages
        self.shadow_handler.shadowRegisterUpdateCallback(callback_any_shadow_update)
        print("\rWaiting for device to update the shadow, iteration " + str(self.iteration + 1))
        self.advance()

    # step 11
    def verify_one_iteration(self):
        super().verify_one_iteration()

        if globals.update_accepted:
            globals.update_accepted = False
            duration = datetime.datetime.now() - self.iteration_start
            print("\rShadow update received (" + self.format_time(duration) + ")")
            print(globals.separator)
            self.check_valve_params()
            self.advance()

    # steps 12-13
    # see test.py