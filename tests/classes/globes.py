# globals.py
# Created 25 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

# these are mostly used by callback functions
class Globes:
    def __init__(self):
        # global flags used by callbacks
        self.update_accepted = False
        self.get_accepted = False

        self.abort_flag = False
        self.abort_reason = ""

        # global strings
        self.separator = "-----------------------------------------------------------------"
        self.terminator = "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"

        self.payload_dict = None

globes = Globes()
