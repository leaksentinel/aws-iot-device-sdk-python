# runtest.py
# Created 23 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

import logging
import argparse
from time import sleep
from termcolor import colored
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from tests.tests.test1 import Test1
from tests.tests.test2 import Test2
from tests.tests.test3 import Test3
from tests.tests.test4 import Test4
from tests.tests.test5 import Test5
from tests.classes.test import TestStatus
from tests.classes.args import Args
from tests.classes.connection import Connection
from tests.classes.globals import globals

# configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logging.addLevelName(45, "HIGHLIGHT")
logger.setLevel(logging.ERROR)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

class TestSuite:
    def __init__(self):
        self.tests = [Test1(), Test2(), Test3(), Test4(), Test5()]   # array of tests that can be run

        self.shadow_client = None               # the aws iot shadow client
        self.shadow_handler = None              # the aws iot shadow handler
        self.initial_update_was_done = False    # true if we already ran our initial update and get requests

        self.tests_to_run = []                  # list of tests to run, parsed from command line
        self.current_index = 0                  # the index (in tests_to_run) of the test currently running
        self.current_status = TestStatus.IDLE   # the status of the entire test suite
        self.loop = 0                           # which loop we're on (a "loop" is one time through tests_to_run)

        # get arguments from command line
        parser = argparse.ArgumentParser()
        parser.add_argument('numbers', metavar='n', nargs='*', type=int, help='Test numbers (e.g. 1 2 3 4)')
        parser.add_argument("-a", "--all", action="store_true", dest="run_all", default=False,
                            help="Run all tests")
        parser.add_argument("-v", "--valve_type", action="store", dest="valve_type", type=int, default=1,
                            help="Valve type (1=gate, 2=ball)")
        parser.add_argument("-b", "--battery", action="store_true", dest="battery", default=False,
                            help="True if running on battery power -- AC power is not connected")
        parser.add_argument("-t", "--timecode", action="store_true", dest="timecode", default=False,
                            help="Display 'wall clock' timecode on console")
        parser.add_argument("-u", "--unix_timecode", action="store_true", dest="unix_timecode", default=False,
                            help="Display UNIX-style timecode on console")
        parser.add_argument("-l", "--loops", action="store", dest="loops", type=int, default=1,
                            help="Number of times to repeat the suite of tests")
        parser.add_argument("-i", "--iterations", action="store", dest="iterations", type=int,
                            help="Number of times to repeat a single test", default=10)
        parser.add_argument("-c", "--cycles", action="store", dest="cycles", type=int,
                            help="Number of times to repeat a sleep/wait cycle before timing out", default=2)
        parser.add_argument("-f", "--connect_not_flowing", action="store", dest="connect_not_flowing", type=int,
                            help="Seconds to wait before connecting", default=30)
        parser.add_argument("-s", "--sleep_multiplier", action="store", dest="sleep_multiplier", type=int,
                            help="Multiply this by connectNotFlowing to get seconds until sleep", default=4)
        parser.add_argument("-r", "--random", action="store_true", dest="random", default=False,
                            help="Wait a random number of seconds between iterations")
        parser.add_argument("-d", "--delay", action="store", dest="delay", type=float,
                            help="Amount to delay before next iteration", default=0.0)
        parser.add_argument("-o", "--offset", action="store", dest="offset", type=float,
                            help="Amount to add to delay per iterations", default=0.0)

        # create an Args object that contains the parameter values parsed from command line
        self.args = Args(parser)

        # check test numbers, create array of tests to run
        if self.args.run_all:
            self.tests_to_run = self.tests
        else:
            for index in self.args.numbers:
                if index > 0 and index <= len(self.tests):
                    self.tests_to_run.append(self.tests[index - 1])
                else:
                    print("Error - there is no test number " + str(index))
                    exit(2)

        print(globals.terminator)
        test_str = "Running test"
        if len(self.tests_to_run) > 1:
            test_str += "s"
        for x in self.tests_to_run:
            test_str += " " + str(x.number)
        title = colored(test_str, "blue")
        print(title)
        print(globals.terminator)

        # connect to AWS IoT
        connection = Connection()
        self.shadow_client:AWSIoTMQTTShadowClient = connection.connect_to_aws_iot()

        # create a device shadow handler with persistent subscription
        self.shadow_handler = self.shadow_client.createShadowHandlerWithName(connection.thing_name, True)

    # run one test in the suite
    def run_test(self, skip_first_update):
       curtest = self.tests_to_run[self.current_index]
       if self.args.loops > 1:
           test_str = ("Start Loop " + str(self.loop + 1) + ", Test " + str(curtest.number) + " - " + curtest.name)
       else:
           test_str = ("Start Test " + str(curtest.number) + " - " + curtest.name)
       title = colored(test_str, "blue")
       print(title)
       print(globals.terminator)
       self.current_status = TestStatus.RUNNING
       curtest.run(self.args, self.shadow_handler, skip_first_update)

    # main loop of runtest app
    def runLoop(self):
        while True:
            # if no test is currently running, start the first one
            if self.current_status == TestStatus.IDLE:
                self.current_status = TestStatus.RUNNING
                self.current_test_index = 0
                # print(globals.terminator)
                self.run_test(self.initial_update_was_done)

            # if a test is currently running...
            if self.current_status == TestStatus.RUNNING:

                # ... has it completed yet?
                test = self.tests_to_run[self.current_index]
                if test.status == TestStatus.COMPLETE:

                    # yes, print test results
                    self.print_one_test_result(test)
                    print(globals.terminator)

                    # set flag so we don't have to send connect_not_flowing and sleep_multiplier again
                    self.initial_update_was_done = True

                    # see if there's another test to run
                    self.current_index += 1
                    if self.current_index >= len(self.tests_to_run):

                        # no more tests to run in the suite, should we loop back and start over?
                        print("Finished loop " + str(self.loop + 1) + " through the suite")
                        self.print_all_test_results()
                        self.loop += 1
                        if self.loop >= self.args.loops:
                            print("All tests completed")
                            exit(0)
                        else:
                            self.current_index = 0
                            self.current_status = TestStatus.IDLE
                    else:
                        self.current_status = TestStatus.IDLE

            sleep(1)

    def print_one_test_result(self, test):
        if test.failures > 0:
            text = colored("FAIL - Test " + str(test.number) + " (" + test.name + ") reported "\
                           + str(test.failures) + " failures", "red")
            print(text)
        else:
            text = colored("PASS - Test " + str(test.number) + " (" + test.name\
                           + ") passed all tests", "green")
            print(text)

    def print_all_test_results(self):
        print("Results for all tests in this loop")
        for test in self.tests_to_run:
            self.print_one_test_result(test)
        print(globals.terminator)


# create app object -- this kicks everything off
if __name__ == "__main__":
    test_suite = TestSuite()
    test_suite.runLoop()
