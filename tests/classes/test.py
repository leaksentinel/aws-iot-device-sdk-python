# test.py
# Created 23 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

from time import sleep
from enum import Enum
import datetime
import json
import random
from tests.classes.globals import globals
from tests.classes.shadow import shadow_items
from termcolor import colored

class TestStatus(Enum):
    IDLE = 1
    RUNNING = 2
    COMPLETE = 3
    ABORTED = 4

# base class for all tests
class Test:
    def __init__(self, number, name, details):

        # these values identify the test
        self.number = number                    # number of this test, starting with 1 (for command line)
        self.name = name                        # name of this test
        self.details = details                  # description of this test

        # helper objects set when the test is run
        self.args = None                        # arguments from the command line
        self.shadow_handler = None              # aws iot shadow handler object

        # these values are set from parsing the command line
        self.run_all = False                    # run all tests
        self.connect_not_flowing = 30           # shadow value written to shadow at start of first test
        self.sleep_multiplier = 4               # shadow value written to shadow at start of first test
        self.battery = False                    # the device is not plugged in, i.e. running on batteries
        self.delay = 0.0                        # how many seconds to wait until start of next iteration
        self.offset = 0.0                       # how many seconds to add to delay for each iteration
        self.iterations = 0                     # total number of iterations in test
        self.cycles = 0                         # total number of sleep/wake cycles before test times out

        # these values deal with running a test
        self.step = 0                           # which step of resume() we're on
        self.failures = 0                       # number of failures for this test during all iterations
        self.status = TestStatus.IDLE           # the status of the currently running test
        self.abort_reason = ""                  # reason the test aborted
        self.skip_first_update = False          # flag says don't do initial update if we did it already

        self.test_start = None                  # start time of entire test
        self.test_end = None                    # end time of entire test
        self.iteration = 0                      # which iteration we're currently doing
        self.iteration_start = None             # iteration start time
        self.iteration_end = None               # iteration end time

        self.cycle = 0                          # which sleep/wake cycle we're currently doing
        self.cycle_duration = 0.0               # how many seconds in one sleep/wake cycle
        self.cycle_start = None                 # cycle start time
        self.cycle_end = None                   # cycle end time
        self.cycle_timed_out = False            # true if we ran out of time

        self.current_delay = 0.0                # seconds to wait before starting the next iteration
        self.delay_start = None                 # delay start time
        self.delaying = False                   # true if we are doing the pre-iteration delay

        self.poll_start = None                  # time that the 'get' polling timer started
        self.poll_seconds = 5                   # number of seconds to wait before attempting the next 'get'

    def set_test_characteristics(self):
        # copy values from command line arguments
        self.run_all = self.args
        self.iterations = self.args.iterations
        self.cycles = self.args.cycles
        self.connect_not_flowing = self.args.connect_not_flowing
        self.sleep_multiplier = self.args.sleep_multiplier
        self.delay = self.args.delay
        self.offset = self.args.offset
        self.random = self.args.random
        self.battery = self.args.battery

        # force reasonable defaults
        if self.iterations < 1 or self.iterations > 9999:
            self.iterations = 10
        if self.cycles < 1 or self.cycles > 99:
            self.cycles = 2
        if not self.args.battery:
            self.cycle_duration = 61.0
        else:
            self.cycle_duration = self.cycles * (self.connectNotFlowing * self.sleepMultiplier + 60)

    def print_test_characteristics(self):
        print("Battery powered: " + str(self.args.battery) +\
              ", connect_not_flowing: " + str(self.connect_not_flowing) +\
              ", sleep_multiplier: " + str(self.sleep_multiplier))
        if self.random:
            print("iterations: " + str(self.iterations) + ", cycles: " + str(self.cycles) +
                ", delay: random, offset: n/a")
        else:
            print("iterations: " + str(self.iterations) + ", cycles: " + str(self.cycles) +
                ", delay: " + str(self.delay) + ", offset: " + str(self.offset))
        print("Cycle time used for this test: " + str(self.cycle_duration))
        print(globals.separator)

    # run one test -- starts our main state machine, "resume()"
    def run(self, args, shadow_handler, skip_first_update):
        self.args = args
        self.shadow_handler = shadow_handler
        self.skip_first_update = skip_first_update
        self.step = 0
        self.failures = 0
        self.status = TestStatus.RUNNING
        self.resume()

    # go on to next step in "resume()" state machine
    def advance(self):
        self.step += 1

    # step 0
    def prepare_for_test(self):
        self.set_test_characteristics()
        self.print_test_characteristics()
        self.test_start = datetime.datetime.now()
        self.step = 0
        self.iteration = 0
        if (self.skip_first_update):  # we only have to do the initial update for the first test
            self.step = 9
        else:
            self.advance()

    # step 1
    def send_first_update(self):
        self.cycle = 0
        self.cycle_start = datetime.datetime.now()
        self.cycle_end = None

        # send request to update "connect_not_flowing" and "sleep_multiplier" values to shadow
        item1 = shadow_items.wifiConnectNotFlowing
        item1.desired_value = str(self.connect_not_flowing)
        item2 = shadow_items.wifiConnectSleepMultiplier
        item2.desired_value = str(self.sleep_multiplier)
        globals.outgoing_dict = {}
        item1.set_desired_values_to_json_dict([item1, item2])
        json_str = json.dumps(globals.outgoing_dict)
        globals.update_accepted = False
        print("Sending first 'update' request to Shadow to set sleep parameters")
        self.shadow_handler.shadowUpdate(json_str, callback_my_shadow_update, 5)
        self.advance()

    # step 2
    def verify_first_update(self):
        # the callback sets update_accepted flag for us when update accept message comes in
        if globals.update_accepted:
            globals.update_accepted = False
            print("First 'update' request was accepted")
            self.advance()
            return

        # see if we've timed out waiting for one cycle
        self.check_for_timeout()
        if self.cycle_timed_out:
            self.cycle_timed_out = False
            print("\rTimeout: no update after " + str(self.cycle_duration) + " seconds")
            self.cycle += 1
            if self.cycle >= self.cycles:
                globals.abort_flag = True
                globals.abort_reason = "First update was never accepted"
            else:
                # start another cycle
                print("Starting cycle " + str(self.cycle + 1))
                self.cycle_start = datetime.datetime.now()

    # step 3 send an empty "get" request to fetch the entire shadow
    def send_first_get(self):
        self.cycle = 0
        self.cycle_start = datetime.datetime.now()
        self.cycle_end = None
        print("Sending first 'get' request to Shadow")
        globals.get_accepted = False
        self.shadow_handler.shadowGet(callback_my_shadow_get, 5)
        sleep(2)
        self.advance()

    # step 4
    def verify_first_get(self):
        # look for flag that says 'get' was received
        if globals.get_accepted:
            # yes, we got a 'get', check that our two valve params are not undfined
            globals.get_accepted = False
            self.check_valve_params()

            # now see if values have taken effect
            item1 = shadow_items.wifiConnectNotFlowing
            item2 = shadow_items.wifiConnectSleepMultiplier
            if item1.get_reported_value_from_json_dict() and \
                    item2.get_reported_value_from_json_dict():
                if item1.desired_value == item1.reported_value and item2.desired_value == item2.reported_value:
                    print("'get' succeeded, connect_not_flowing = " + item1.reported_value \
                          + ", sleep_multiplier = " + item2.reported_value)
                    print(globals.separator)

                    self.advance()
                    return

        # see if we've timed out waiting for one cycle
        self.check_for_timeout()
        if self.cycle_timed_out:
            self.cycle_timed_out = False
            print("\rTimeout: no update after " + str(self.cycle_duration) + " seconds")
            self.cycle += 1
            if self.cycle >= self.cycles:
                globals.abort_flag = True
                globals.abort_reason = "First get was never accepted"
            else:
                # start another cycle
                msg = colored("Starting cycle " + str(self.cycle + 1), "red")
                print(msg)
                self.cycle_start = datetime.datetime.now()

        else:
            if self.step == 4:
                self.display_cycle_timer()

    # step 5
    def send_second_update(self):
        self.cycle = 0
        self.cycle_start = datetime.datetime.now()
        self.cycle_end = None

        # get current valve type and motor params
        vtype = shadow_items.valveType
        item1 = shadow_items.motorMaxI
        item2 = shadow_items.motorMaxT
        item3 = shadow_items.motorBackT
        items = [item1, item2, item3]
        if vtype.get_reported_value_from_json_dict():
            # set desired values for motor params based on valve type
            if vtype.reported_value == "1":  # gate
                item1.val1 = "0.90"
                item1.val2 = "0.89"
                item2.val1 = "60"
                item2.val2 = "61"
                item3.val1 = "100"
                item3.val2 = "101"
            elif vtype.reported_value == "2":  # ball
                item1.val1 = "1.20"
                item1.val2 = "1.19"
                item2.val1 = "15"
                item2.val2 = "16"
                item3.val1 = "500"
                item3.val2 = "501"
            else:
                self.step = 9
                return

        # if desired values already match reported values, we can skip this step
        for item in items:
            if item.get_reported_value_from_json_dict():
                if not (item.val1 == item.reported_value) and not (item.val2 == item.reported_value):

                    # send request to update the three motor parameters to shadow
                    globals.outgoing_dict = {}

                    for item in items:
                        # get desired val of same param
                        if item.val1 == item.reported_value:
                            item.desired_value = item.val2
                        else:
                            item.desired_value = item.val1

                        item.set_desired_values_to_json_dict(items)

                    json_str = json.dumps(globals.outgoing_dict)
                    globals.update_accepted = False
                    print("Sending second 'update' request to Shadow to set motor parameters")
                    self.shadow_handler.shadowUpdate(json_str, callback_my_shadow_update, 5)
                    self.advance()
                    return
        # all items match, skip these steps
        print("Motor parameters are already correct for this valve type")
        self.step = 9

    # step 6
    def verify_second_update(self):
        # the callback sets update_accepted flag for us when update accept message comes in
        if globals.update_accepted:
            globals.update_accepted = False
            print("Second 'update' request was accepted")
            self.advance()
            self.cycle = 0
            self.cycle_start = datetime.datetime.now()
            self.cycle_end = None
            return

        # see if we've timed out waiting for one cycle
        self.check_for_timeout()
        if self.cycle_timed_out:
            self.cycle_timed_out = False
            print("\rTimeout: no update after " + str(self.cycle_duration) + " seconds")
            self.cycle += 1
            if self.cycle >= self.cycles:
                globals.abort_flag = True
                globals.abort_reason = "second update was never accepted"
            else:
                # start another cycle
                print("Starting cycle " + str(self.cycle + 1))
                self.cycle_start = datetime.datetime.now()

        if self.step == 6:
            self.display_cycle_timer()

    # step 7 send an empty "get" request to fetch the entire shadow
    def send_second_get(self):
        print("Sending second 'get' request to Shadow")
        globals.get_accepted = False
        self.poll_start = datetime.datetime.now()
        self.shadow_handler.shadowGet(callback_my_shadow_get, 5)
        self.advance()

    # step 8
    def verify_second_get(self):
        # look for flag that says 'get' was received
        if globals.get_accepted:
            # yes, we got a 'get'
            globals.get_accepted = False
            self.check_valve_params()

            # now see if values have taken effect
            item1 = shadow_items.motorMaxI
            item2 = shadow_items.motorMaxT
            item3 = shadow_items.motorBackT
            items = [item1, item2, item3]
            for item in items:

                # if desired values match reported values, we can go on
                if item1.desired_value == item1.reported_value and \
                        item2.desired_value == item2.reported_value and \
                        item3.desired_value == item3.reported_value:
                    self.advance()
                    return

        # bad luck, no response yet, wait a few seconds before trying again
        duration = (datetime.datetime.now - self.poll_start).total_seconds()
        if duration >= self.poll_seconds:
            step = 7    # loop back and poll again
            return

        # see if we've timed out waiting for one cycle
        self.check_for_timeout()
        if self.cycle_timed_out:
            self.cycle_timed_out = False
            print("\rTimeout: no update after " + str(self.cycle_duration) + " seconds")
            self.cycle += 1
            if self.cycle >= self.cycles:
                globals.abort_flag = True
                globals.abort_reason = "Second get was never accepted"
            else:
                # start another cycle
                msg = colored("Starting cycle " + str(self.cycle + 1), "red")
                print(msg)
                self.cycle_start = datetime.datetime.now()

        else:
            if self.step == 8:
                self.display_cycle_timer()
            sleep(5)
            self.step = 7

    # step 9
    def delay_before_iteration(self):
        if self.delaying:
            elapsed_time = (datetime.datetime.now() - self.delay_start).total_seconds()
            if elapsed_time > self.current_delay:
                self.delaying = False
                self.advance()
            else:
                self.display_delay_timer()

        else:
            self.delay_start = datetime.datetime.now()
            self.iteration_start = datetime.datetime.now()
            self.iteration_end = None
            self.cycle  = 0
            self.cycle_start = datetime.datetime.now()
            self.cycle_end = None

            if self.random:
                self.current_delay = (random.randint(0,1000000) / 1000000.0) * self.cycle_duration
                print("Waiting for a random delay of {0:.2f} seconds".format(self.current_delay))
                self.delaying = True
            elif self.delay > 0.0:
                self.current_delay = self.delay + (self.iteration * self.offset)
                print("Waiting for a delay of " + str(self.current_delay) + " seconds")
                self.delaying = True
            else:
                print("No delay time specified")
                self.delaying = False
                self.advance()

    # step 10
    def run_one_iteration(self):
        # nothing to do in base class
        return

    # step 11
    def verify_one_iteration(self):
        # see if wait time has elapsed
        if self.delaying:
            wait_time = (datetime.datetime.now() - self.delay_start).total_seconds()
            if wait_time > self.current_delay:
                self.delaying = False

        # see if we've timed out waiting for one cycle
        self.check_for_timeout()
        if self.cycle_timed_out:
            self.cycle_timed_out = False
            cycle_start = datetime.datetime.now()

            print("\rTimeout: no update after " + str(self.cycle_duration) + " seconds")
            self.cycle += 1
            if self.cycle >= self.cycles:
                text = colored("FAIL - failed to update after " + str(self.cycles) + " cycles", 'red')
                print(text)
                self.failures += 1
                print(globals.separator)
                self.advance()

            else:
                # start another cycle
                self.cycle_start = datetime.datetime.now()
                text = colored("Starting cycle " + str(self.cycle + 1), 'red')
                print(text)

        else:
            self.display_cycle_timer()


    # step 12
    def loop_back(self):
        # bump iteration count and see if we've done all of our iterations
        self.iteration += 1
        if self.iteration >= self.iterations:
            self.advance()
        else:
            self.step = 9

    # step 13
    def finish_test(self):
        self.status = TestStatus.COMPLETE
        self.step = -1

    # abnormal termination
    def abort_test(self):
        text = colored("Test aborted: " + globals.abort_reason, "red")
        print(text)
        exit(2)

    # this is the state machine that runs every test
    def resume(self):
        while True:
            # always check to see if we've aborted
            if globals.abort_flag:
                self.abort_test()
                return

            # normal execution drives through this state machine
            if self.step == 0:
                self.prepare_for_test()
            elif self.step == 1:
                self.send_first_update()
            elif self.step == 2:
                self.verify_first_update()
            elif self.step == 3:
                self.send_first_get()
            elif self.step == 4:
                self.verify_first_get()
            elif self.step == 5:
                self.send_second_update()
            elif self.step == 6:
                self.verify_second_update()
            elif self.step == 7:
                self.send_second_get()
            elif self.step == 8:
                self.verify_second_get()
            elif self.step == 9:
                self.delay_before_iteration()
            elif self.step == 10:
                self.run_one_iteration()
            elif self.step == 11:
                self.verify_one_iteration()
            elif self.step == 12:
                self.loop_back()
            elif self.step == 13:
                self.finish_test()
                return

            sleep(0.5)

    def display_delay_timer(self):
        if self.delay_start != None:
            duration = datetime.datetime.now() - self.delay_start
            print("\rWaiting for delay ... (" + self.format_time(duration) + ")", end='')

    def display_cycle_timer(self):
        if self.cycle_start != None:
            duration = datetime.datetime.now() - self.cycle_start
            print("\rWaiting for response... (" + self.format_time(duration) + ")", end='')

    def check_for_timeout(self):
        if self.cycle_timed_out:
            return

        duration = (datetime.datetime.now() - self.cycle_start).total_seconds()

        if duration >= self.cycle_duration:
            self.cycle_timed_out = True
        else:
            self.cycle_timed_out = False

    def check_valve_params(self):
        text = ""
        item1 = shadow_items.valveState
        item2 = shadow_items.requestedValveStateReq
        if item1.get_reported_value_from_json_dict() and \
                item2.get_reported_value_from_json_dict():
            if item1.reported_value == "0":
                if item2.reported_value == "0":
                    text = colored("\nFAIL - Both valve_state and valve_state_req are in an unknown state.\n" + \
                                   "Please reset both to a known state before you run this app.", 'red')
                else:
                    text = colored("\nFAIL - valve_state is in an unknown state.\n" + \
                                   "Please reset valve_state to a known state before you run this app.", 'red')
            elif item2.reported_value == "0":
                    text = colored("\nFAIL - valve_state_req is in an unknown state.\n" + \
                                   "Please reset valve_state_req to a known state before you run this app.", 'red')
            if not text == "":
                print(text)
                print(globals.terminator)
                exit(3)

    def format_time(self, td: datetime.timedelta):
        str = ""
        seconds = td.total_seconds()
        s = int(seconds) % 60
        m = int(seconds / 60) % 60
        h = int(seconds / 3600)
        if h == 0:
            if m < 10:
                str = f'{m:d}:{s:02d}'
            else:
                str = f'{m:02d}:{s:02d}'
        else:
            str = f'{h:d}:{m:02d}:{s:02d}'
        return str


def callback_my_shadow_update(payload, responseStatus, token):
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
        globals.abort_flag = True
        globals.abort_reason = "Update request timed out"
        return

    if responseStatus == "accepted":
        globals.incoming_dict = json.loads(payload)
        globals.update_accepted = True

    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")
        globals.abort_flag = True
        globals.abort_reason = "Error - shadow rejected our update request"


def callback_my_shadow_get(payload, responseStatus, token):
    if responseStatus == "timeout":
        print("Get request " + token + " time out!")
        globals.abort_flag = True
        globals.abort_reason = "The 'get' request timed out"
        return

    if responseStatus == "accepted":
        globals.get_accepted = True
        globals.incoming_dict = json.loads(payload)

    if responseStatus == "rejected":
        print("Get request " + token + " rejected!")
        globals.abort_flag = True
        globals.abort_reason = "Error - shadow rejected our 'get' request"


# call us back whenever an updated message is generated, regardless of token
def callback_any_shadow_update(payload, responseStatus, token):
    # print("callback_any_shadow_update")
    # print("\r" + responseStatus + "                        ")
    globals.incoming_dict = json.loads(payload)
    # print("state: " + str(payloadDict["state"]))
    globals.update_accepted = True

