# -*- encoding: utf-8 -*-
'''
@File      :   websocketLink.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2023, lunzhiPenxil仑质
@Desc      :   None
'''

import OlivOSOnebotV11

import time
import uuid
import websocket
import threading

clientList = []
clientDict = {}
clientMapDict = {}

def start_websocket(confDict):
    for server_this in confDict:
        if 'hash' in confDict[server_this] \
        and 'path' in confDict[server_this] \
        and type(confDict[server_this]['path']) is list:
            for ws_path in confDict[server_this]['path']:
                threading.Thread(
                    target = OlivOSOnebotV11.websocketLink.init_websocket,
                    args = (confDict[server_this], ws_path)
                ).start()

def init_websocket(server_conf, ws_path):
    websocketLinkObj = server(server_conf, ws_path)
    websocketLinkObj.run()

class server(object):
    def __init__(
        self,
        server_conf,
        ws_path
    ):
        self.Proc_config = {}
        self.Proc_data = {}
        self.Proc_config['server_conf'] = server_conf
        self.Proc_config['hash'] = server_conf['hash']
        self.Proc_config['ws_path'] = ws_path
        self.Proc_config['bot_info'] = None
        self.Proc_data['ws_obj'] = None
        self.Proc_data['ws_item'] = None
        for botHash in OlivOSOnebotV11.main.botInfoDict:
            if botHash == self.Proc_config['hash']:
                self.Proc_config['bot_info'] = OlivOSOnebotV11.main.botInfoDict[botHash]
                break

    def run(self):
        OlivOSOnebotV11.main.ProcObj.log(2, str(self.Proc_config['ws_path']) + ' - running for [' + self.Proc_config['hash'] + ']', [
            ('OlivOSOnebotV11', 'default')
        ])
        while True:
            self.run_websocket_rx_connect_start()
            time.sleep(2)

    def on_message(self, ws, message):
        actionObj = OlivOSOnebotV11.eventRouter.txEvent(
            ws,
            hostType = 'r-ws',
            msg = message,
            hash = self.Proc_config['hash']
        )
        actionObj.doRouter()

    def on_error(self, ws, error):
        OlivOSOnebotV11.main.ProcObj.log(0, str(self.Proc_config['ws_path']) + ' - error for [' + self.Proc_config['hash'] + ']', [
            ('OlivOSOnebotV11', 'default')
        ])

    def on_close(self, ws, close_status_code, close_msg):
        OlivOSOnebotV11.main.ProcObj.log(0, str(self.Proc_config['ws_path']) + ' - closed for [' + self.Proc_config['hash'] + ']', [
            ('OlivOSOnebotV11', 'default')
        ])

    def on_open(self, ws):
        OlivOSOnebotV11.main.ProcObj.log(2, str(self.Proc_config['ws_path']) + ' - connected for [' + self.Proc_config['hash'] + ']', [
            ('OlivOSOnebotV11', 'default')
        ])

    def run_pulse(self):
        pass
        return

    def run_websocket_rx_connect_start(self):
        global clientList, clientDict, clientMapDict
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            self.Proc_config['ws_path'],
            header = {
                'X-Self-ID': str(self.Proc_config['bot_info'].id)
            },
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.Proc_data['ws_obj'] = ws
        self.Proc_data['ws_item'] = uuid.uuid4()
        clientDict.setdefault(self.Proc_config['hash'], [])
        clientDict[self.Proc_config['hash']].append(ws)
        ws.run_forever()
        self.Proc_data['ws_obj'] = None
        self.Proc_data['ws_item'] = None
        OlivOSOnebotV11.main.ProcObj.log(2, str(self.Proc_config['ws_path']) + ' - lost for [' + self.Proc_config['hash'] + ']', [
            ('OlivOSOnebotV11', 'default')
        ])

