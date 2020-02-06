# globals.py
# Created 30 Jan 2020
# By J K Thomson
# Copyright (c) 2020 LeakSentinel, Inc

import ssl
import urllib.request

class MicrobotButton:
    def __init__(self, name, push, press, release, reveal):
        self.name = name
        self.pushUrl = push
        self.pressUrl = press
        self.releaseUrl = release
        self.revealUrl = reveal

    def push(self):
        print("Push!")
        self.request(self.pushUrl)

    def press(self):
        print("Press!")
        self.request(self.pressUrl)

    def release(self):
        print("Release!")
        self.request(self.releaseUrl)

    def reveal(self):
        print("Reveal!")
        self.request(self.revealUrlUrl)

    def request(self, url):
        import requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        result = requests.get(url, headers=headers)
        print(result.content.decode())

pwrButton = MicrobotButton("PWR", \
    "https://o1.prota.space/mib/do/push?_id=cd8aeed89601117383ac7411d8e9f4d5", \
    "https://o1.prota.space/mib/do/press?_id=cd8aeed89601117383ac7411d8e9f4d5", \
    "https://o1.prota.space/mib/do/release?_id=cd8aeed89601117383ac7411d8e9f4d5", \
    "https://o1.prota.space/mib/do/reveal?_id=cd8aeed89601117383ac7411d8e9f4d5")

wifiButton = MicrobotButton("PWR", \
    "https://o1.prota.space/mib/do/push?_id=69ce2a6ade53c6aae168fa1785d1b450", \
    "https://o1.prota.space/mib/do/press?_id=69ce2a6ade53c6aae168fa1785d1b450", \
    "https://o1.prota.space/mib/do/release?_id=69ce2a6ade53c6aae168fa1785d1b450", \
    "https://o1.prota.space/mib/do/reveal?_id=69ce2a6ade53c6aae168fa1785d1b450")
