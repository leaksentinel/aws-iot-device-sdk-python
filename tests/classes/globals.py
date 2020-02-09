# globals.py
# Created 25 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

# these are mostly used by callback functions
class Globals:
    def __init__(self):
        # global flags used by callbacks
        self.update_accepted = False
        self.get_accepted = False

        self.abort_flag = False
        self.abort_reason = ""

        # incoming payload from MQTT message
        self.incoming_dict = {}

        # outgoing payload from updates
        self.outgoing_dict = {}

        # global strings
        self.separator = "---------------------------------------------------------------------------"
        self.terminator = "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"


globals = Globals()
