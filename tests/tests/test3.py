# test3.py
# Created 23 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

import json
import datetime
from time import sleep

from classes.test import Test
from classes.globes import globes
from classes.button import pwrButton, wifiButton

class Test3(Test):
    def __init__(self):
        super().__init__(3,
                         "Update Frequency",
            "Verify that device checks the shadow in the cloud periodically, and that valve state is never unknown")

    # step 0
    def prepare_for_test(self):
        print("Step " + str(self.step + 1))
        pwrButton.push()
        wifiButton.push()
        sleep(1)
        self.advance()

    # step 1
    def send_initial_update(self):
        print("Step " + str(self.step + 1))
        pwrButton.release()
        sleep(1)
        self.advance()

    # step 2
    def verify_initial_update(self):
        print("Step " + str(self.step + 1))
        wifiButton.release()
        sleep(1)
        self.advance()

    # step 3
    def send_initial_get(self):
        print("Step " + str(self.step + 1))
        pwrButton.press()
        sleep(1)
        self.advance()

    # step 4
    def verify_initial_get(self):
        print("Step " + str(self.step + 1))
        wifiButton.press()
        sleep(1)
        self.advance()

    # step 5
    def prepare_for_iteration(self):
        print("Step " + str(self.step + 1))
        wifiButton.press()
        pwrButtonButton.press()
        sleep(1)
        self.advance()

    # step 6
    def run_one_iteration(self):
        print("Step " + str(self.step + 1))
        wifiButton.press()
        pwrButtonButton.press()
        sleep(1)
        self.advance()

    # step 7
    def verify_one_iteration(self):
        print("Step " + str(self.step + 1))
        wifiButton.press()
        sleep(1)
        self.advance()

    # step 8
    def loop_back(self):
        print("Step " + str(self.step + 1))
        pwrButtonButton.press()
        sleep(1)
        self.advance()

    # step 9
    def finish_test(self):
        print("Step " + str(self.step + 1))
        wifiButton.press()
        pwrButtonButton.press()
        sleep(1)

# callback functions
# call us back whenever an updated is accepted, regardless of token
def callback_shadow_update(payload, responseStatus, token):
    print("\r" + responseStatus + "                        ")
    payloadDict = json.loads(payload)
    # print("state: " + str(payloadDict["state"]))
    globes.update_accepted = True

