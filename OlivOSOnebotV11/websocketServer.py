# -*- encoding: utf-8 -*-
'''
@File      :   websocketServer.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2022, lunzhiPenxil仑质
@Desc      :   None
'''

import asyncio
import socket
import threading
import traceback
from contextlib import closing

import websockets

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
    finally:
        s.close()
    return flag


def get_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def log(level, message):
    ProcObj = OlivOSOnebotV11.main.ProcObj
    if ProcObj is None:
        return
    ProcObj.log(level, message, [('OlivOSOnebotV11', 'default')])


def format_bot_info(bot_hash):
    bot_info = OlivOSOnebotV11.main.botInfoDict.get(bot_hash)
    if bot_info is None:
        return str(bot_hash)
    try:
        return '%s|%s' % (
            str(bot_info.platform['platform']),
            str(bot_info.id)
        )
    except (AttributeError, KeyError, TypeError):
        return str(bot_hash)


def start_websocket(confDict):
    for server_this in confDict:
        if 'port' not in confDict[server_this] or confDict[server_this]['port'] is None:
            confDict[server_this]['port'] = get_free_port()
        threading.Thread(
            target=OlivOSOnebotV11.websocketServer.init_websocket,
            args=(confDict[server_this],),
            daemon=True
        ).start()
    threading.Thread(
        target=OlivOSOnebotV11.eventRouter.fakeHeartbeatGen,
        args=(),
        daemon=True
    ).start()


class connectionAdapter(object):
    def __init__(self, connection, server_port, path=None):
        self.connection = connection
        self.server_port = int(server_port)
        self.path = path
        self.address = getattr(connection, 'remote_address', None)
        self.data = None
        self.bot_hash = None
        self.loop = asyncio.get_running_loop()
        self.sendQueue = asyncio.Queue()
        self.closed = False

    def sendMessage(self, message):
        if self.closed:
            return
        try:
            self.loop.call_soon_threadsafe(self.sendMessageOnLoop, message)
        except RuntimeError:
            self.closed = True

    def sendMessageOnLoop(self, message):
        if self.closed:
            return
        self.sendQueue.put_nowait(message)

    async def sendLoop(self):
        try:
            while True:
                message = await self.sendQueue.get()
                await self.connection.send(message)
        except asyncio.CancelledError:
            raise
        except websockets.ConnectionClosed:
            pass
        except Exception as e:
            skip_result = '%s\n%s' % (
                str(e),
                traceback.format_exc()
            )
            log(3, skip_result)


def register_client(adapter):
    clientList.append(adapter)
    bot_hash_this = None
    server_port = adapter.server_port
    for bot_hash in OlivOSOnebotV11.main.confDict:
        conf_this = OlivOSOnebotV11.main.confDict[bot_hash]
        if str(conf_this['port']) != str(server_port):
            continue
        port_key = str(conf_this['port'])
        clientDict.setdefault(port_key, [])
        clientDict[port_key].append({
            'info': conf_this.copy(),
            'obj': adapter
        })
        clientMapDict[bot_hash] = port_key
        adapter.bot_hash = bot_hash
        bot_hash_this = bot_hash
        break
    if bot_hash_this is None:
        log(
            3,
            str(adapter.address) + ' - connected to [' + str(server_port) + '] without account route'
        )
        return
    tmp_bot_hash_this = format_bot_info(bot_hash_this)
    log(
        2,
        str(adapter.address) + ' - connected to [' + str(server_port) + '] for [' + tmp_bot_hash_this + ']'
    )


def unregister_client(adapter):
    try:
        clientList.remove(adapter)
    except ValueError:
        pass
    server_port = adapter.server_port
    for client_this in list(clientDict.get(str(server_port), [])):
        if client_this['obj'] is adapter:
            clientDict[str(server_port)].remove(client_this)
    log(
        2,
        str(adapter.address) + ' - closed to [' + str(server_port) + ']'
    )


async def handle_connection(connection, server_port, path=None):
    adapter = connectionAdapter(connection, server_port, path)
    send_task = None
    try:
        register_client(adapter)
        send_task = asyncio.create_task(adapter.sendLoop())
        async for message in connection:
            if isinstance(message, bytes):
                try:
                    message = message.decode('utf-8')
                except UnicodeDecodeError:
                    log(3, str(adapter.address) + ' - invalid utf-8 payload')
                    continue
            adapter.data = message
            actionObj = OlivOSOnebotV11.eventRouter.txEvent(adapter, hostType='ws')
            actionObj.doRouter()
    except asyncio.CancelledError:
        raise
    except websockets.ConnectionClosed:
        pass
    except Exception as e:
        skip_result = '%s\n%s' % (
            str(e),
            traceback.format_exc()
        )
        log(3, skip_result)
    finally:
        adapter.closed = True
        if send_task is not None:
            send_task.cancel()
            await asyncio.gather(send_task, return_exceptions=True)
        unregister_client(adapter)


def create_handler(server_port):
    async def handler(connection, path=None):
        await handle_connection(connection, server_port, path)
    return handler


async def serve(server_this):
    global server
    server_port = int(server_this['port'])
    handler = create_handler(server_port)
    async with websockets.serve(handler, '0.0.0.0', server_port, max_size=None) as server_obj:
        server = server_obj
        tmp_bot_hash_info = format_bot_info(server_this['hash'])
        log(
            2,
            '账号 [' + tmp_bot_hash_info + '] 运行于Websocket，请使用 [ws://localhost:' +
            str(server_port) + '] 进行连接'
        )
        await asyncio.Future()


def init_websocket(server_this):
    try:
        asyncio.run(serve(server_this))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        skip_result = '%s\n%s' % (
            str(e),
            traceback.format_exc()
        )
        log(3, skip_result)
