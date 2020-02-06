# test4.py
# Created 23 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.
import json
import time

from classes.connection import Connection
from classes.test import Test

class Test4(Test):
    def __init__(self):
        super().__init__(4, 'test4', 'open and shut')

