# connection.py
# Created 23 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc.

import time
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import configparser
import pathlib

class Connection:
    # initialize connection parameters
    def __init__(self):
        self.use_web_socket = True
        self.client_id = "1234567890"   # a made-up number we don't currently use for anything
        self.port = 443

        # get some settings from ~/.aws/config file
        config = configparser.RawConfigParser()
        path = pathlib.PosixPath('~/.aws/config')
        config.read(path.expanduser())
        try:
            # endpoint for interacting with the shadow
            self.host = config.get('leaktest', 'endpoint')
        except:
            print("Error - no endpoint specified in ~/.aws/config file")
            exit(2)
        try:
            self.root_ca_path = config.get('leaktest', 'root_ca_path')
        except:
            print("Error - no root_ca_path specified in ~/.aws/config file")
            exit(2)
        try:
            self.thing_name = config.get('leaktest', 'thing_name')
        except:
            print("Error - no thing_name specified in ~/.aws/config file")
            exit(2)

    def connect_to_aws_iot(self) -> AWSIoTMQTTShadowClient:
        # initialize a shadow client
        myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(self.client_id, useWebsocket=True)
        myAWSIoTMQTTShadowClient.configureEndpoint(self.host, self.port)
        myAWSIoTMQTTShadowClient.configureCredentials(self.root_ca_path)

        # configure shadow client
        myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
        myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
        myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

        # Connect to AWS IoT
        myAWSIoTMQTTShadowClient.connect()
        return myAWSIoTMQTTShadowClient
