# -*- encoding: utf-8 -*-
'''
@File      :   websocketServer.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2022, lunzhiPenxil仑质
@Desc      :   None
'''

import threading
import traceback
import socket
from contextlib import closing

import OlivOSOnebotV11

server = None
clientList = []
clientDict = {}
clientMapDict = {}


def isInuse(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    flag = True
    try:
        s.connect((ip, port))
        s.shutdown(2)
        flag = True
    except OSError:
        flag = False
    return flag


def get_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def start_websocket(confDict):
    for server_this in confDict:
        if confDict[server_this]['port'] is None or (
            False and isInuse('127.0.0.1', confDict[server_this]['port'])
        ):
            confDict[server_this]['port'] = get_free_port()
        threading.Thread(
            target=OlivOSOnebotV11.websocketServer.init_websocket,
            args=(confDict[server_this],)
        ).start()
    threading.Thread(
        target=OlivOSOnebotV11.eventRouter.fakeHeartbeatGen,
        args=()
    ).start()


def init_websocket(server_this):
    global server

    class serverClass(OlivOSOnebotV11.SimpleWebSocketServer.WebSocket):
        def handleMessage(self):
            actionObj = OlivOSOnebotV11.eventRouter.txEvent(self)
            actionObj.doRouter()

        def handleConnected(self):
            try:
                clientList.append(self)
                bot_hash_this = None
                server_port = list(self.server.serversocket.getsockname())[1]
                for bot_hash in OlivOSOnebotV11.main.confDict:
                    if OlivOSOnebotV11.main.confDict[bot_hash]['port'] == server_port:
                        if str(OlivOSOnebotV11.main.confDict[bot_hash]['port']) not in clientDict:
                            clientDict[str(OlivOSOnebotV11.main.confDict[bot_hash]['port'])] = []
                        clientDict[str(OlivOSOnebotV11.main.confDict[bot_hash]['port'])].append({
                            'info': OlivOSOnebotV11.main.confDict[bot_hash].copy(),
                            'obj': self
                        })
                        clientMapDict[bot_hash] = str(OlivOSOnebotV11.main.confDict[bot_hash]['port'])
                        bot_hash_this = bot_hash
                        break
                tmp_bot_hash_this = bot_hash_this
                tmp_bot_hash_this = '%s|%s' % (
                    str(OlivOSOnebotV11.main.botInfoDict[bot_hash_this].platform['platform']),
                    str(OlivOSOnebotV11.main.botInfoDict[bot_hash_this].id)
                )
                OlivOSOnebotV11.main.ProcObj.log(
                    2,
                    str(self.address) + ' - connected to [' + str(server_port) + '] for [' + tmp_bot_hash_this + ']',
                    [('OlivOSOnebotV11', 'default')]
                )
            except Exception as e:
                skip_result = '%s\n%s' % (
                    str(e),
                    traceback.format_exc()
                )
                OlivOSOnebotV11.main.ProcObj.log(3, skip_result, [
                    ('OlivOSOnebotV11', 'default')
                ])

        def handleClose(self):
            try:
                clientList.remove(self)
                server_port = list(self.server.serversocket.getsockname())[1]
                for client_this in clientDict[str(server_port)]:
                    if client_this['obj'] == self:
                        clientDict[str(server_port)].remove(client_this)
                OlivOSOnebotV11.main.ProcObj.log(
                    2,
                    str(self.address) + ' - closed to [' + str(server_port) + ']',
                    [('OlivOSOnebotV11', 'default')]
                )
            except Exception as e:
                skip_result = '%s\n%s' % (
                    str(e),
                    traceback.format_exc()
                )
                OlivOSOnebotV11.main.ProcObj.log(3, skip_result, [
                    ('OlivOSOnebotV11', 'default')
                ])

    server = OlivOSOnebotV11.SimpleWebSocketServer.SimpleWebSocketServer('0.0.0.0', server_this['port'], serverClass)
    tmp_bot_hash_info = server_this['hash']
    if server_this['hash'] in OlivOSOnebotV11.main.botInfoDict:
        tmp_bot_hash_info = '%s|%s' % (
            str(OlivOSOnebotV11.main.botInfoDict[server_this['hash']].platform['platform']),
            str(OlivOSOnebotV11.main.botInfoDict[server_this['hash']].id)
        )
    OlivOSOnebotV11.main.ProcObj.log(
        2,
        '账号 [' + tmp_bot_hash_info + '] 运行于Websocket，请使用 [ws://localhost:' +
        str(server_this['port']) + '] 进行连接',
        [('OlivOSOnebotV11', 'default')]
    )
    server.serveforever()
