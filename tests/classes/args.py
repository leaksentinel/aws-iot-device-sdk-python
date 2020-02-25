# Args.py
# Created 23 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

import argparse

# this class encapsulates all of the arguments parsed from the command line
class Args:
    def __init__(self, parser: argparse.ArgumentParser):

        cmd = parser.parse_args()
        self.numbers = cmd.numbers
        self.run_all = cmd.run_all
        self.battery = cmd.battery
        self.timecode = cmd.timecode
        self.unix_timecode = cmd.unix_timecode
        self.loops = cmd.loops
        self.iterations = cmd.iterations
        self.cycles = cmd.cycles
        self.random = cmd.random
        self.delay = cmd.delay
        self.offset = cmd.offset
        self.connect_not_flowing = cmd.connect_not_flowing
        self.sleep_multiplier = cmd.sleep_multiplier


