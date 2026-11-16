import asyncio
import json
import socket
import threading
from types import SimpleNamespace

import pytest
import websockets

from OlivOSOnebotV11 import eventRouter, main, websocketServer


class _Proc(object):
    def __init__(self):
        self.logs = []

    def log(self, level, message, segment):
        self.logs.append((level, message, segment))


class _WebSocket(object):
    def __init__(self, data=None, port=43000, bot_hash='bot-a'):
        self.data = data
        self.server_port = port
        self.bot_hash = bot_hash
        self.messages = []

    def sendMessage(self, message):
        self.messages.append(message)

    def send(self, message):
        self.messages.append(message)


class _ActionEvent(object):
    def __init__(self, result):
        self.result = result

    def get_msg(self, message_id):
        return self.result


class _LoginEvent(object):
    def __init__(self, sdk_event, log):
        self.bot_info = sdk_event.bot_info

    def get_login_info(self):
        return {
            'active': True,
            'data': {
                'id': '42',
                'name': 'Alice',
            },
        }


async def _wait_until(predicate, timeout=2.0):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not predicate():
        if loop.time() >= deadline:
            raise AssertionError('condition was not met before timeout')
        await asyncio.sleep(0.01)


def test_get_free_port_returns_usable_local_port():
    port = websocketServer.get_free_port()

    assert isinstance(port, int)
    assert port > 0
    assert websocketServer.isInuse('127.0.0.1', port) is False


def test_is_inuse_detects_listening_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind(('127.0.0.1', 0))
        server_socket.listen(1)
        port = server_socket.getsockname()[1]
        assert websocketServer.isInuse('127.0.0.1', port) is True
    finally:
        server_socket.close()


def test_tx_event_keeps_echo_status_and_data_contract():
    main.ProcObj = _Proc()
    main.confDict['bot-a'] = {'hash': 'bot-a', 'port': 43000}
    main.botInfoDict['bot-a'] = SimpleNamespace(hash='bot-a', id=42)
    websocket = _WebSocket(
        data=json.dumps({
            'action': 'get_msg',
            'echo': 'request-1',
            'params': {'message_id': 99},
        })
    )

    event = eventRouter.txEvent(websocket, hostType='ws')
    event.plugin_event = _ActionEvent({
        'active': True,
        'data': {
            'message_id': 99,
            'id': 99,
            'sender': {'id': 42, 'name': 'Alice'},
            'time': 1700000000,
            'message': 'hello',
            'raw_message': 'hello',
        },
    })
    event.doRouter()

    response = json.loads(websocket.messages[0])
    assert response['echo'] == 'request-1'
    assert response['status'] == 'ok'
    assert response['retcode'] == 0
    assert response['data']['message_id'] == 99
    assert response['data']['sender']['user_id'] == 42


def test_tx_event_resolves_account_from_server_port():
    main.ProcObj = _Proc()
    main.confDict['bot-a'] = {'hash': 'bot-a', 'port': 43001}
    main.confDict['bot-b'] = {'hash': 'bot-b', 'port': 43000}
    main.botInfoDict['bot-a'] = SimpleNamespace(hash='bot-a', id=41)
    main.botInfoDict['bot-b'] = SimpleNamespace(hash='bot-b', id=42)
    websocketServer.clientDict['43000'] = [{'info': {'hash': 'bot-b'}}]
    websocket = _WebSocket(
        data=json.dumps({
            'action': 'get_login_info',
            'echo': 'request-2',
            'params': {},
        }),
        bot_hash=None,
    )

    event = eventRouter.txEvent(websocket, hostType='ws')

    assert event.active is True
    assert event.plugin_event.bot_info.hash == 'bot-b'


@pytest.mark.parametrize('raw', ['{invalid-json', json.dumps({'echo': 'missing-action'})])
def test_tx_event_ignores_malformed_requests(raw):
    main.ProcObj = _Proc()
    websocket = _WebSocket(data=raw)

    event = eventRouter.txEvent(websocket, hostType='ws')
    event.doRouter()

    assert event.active is False
    assert websocket.messages == []


def test_tx_event_uses_reverse_link_hash_and_reply_channel():
    main.ProcObj = _Proc()
    main.botInfoDict['bot-a'] = SimpleNamespace(hash='bot-a', id=42)
    websocket = _WebSocket(
        data=json.dumps({
            'action': 'get_login_info',
            'echo': 'request-3',
            'params': {},
        })
    )

    event = eventRouter.txEvent(websocket, hostType='r-ws', msg=websocket.data, hash='bot-a')
    event.plugin_event = SimpleNamespace(
        get_login_info=lambda: {'active': True, 'data': {'id': '42', 'name': 'Alice'}}
    )
    event.doRouter()

    response = json.loads(websocket.messages[0])
    assert response['data'] == {'user_id': 42, 'nickname': 'Alice'}


def test_websockets_server_handles_action_and_thread_safe_send(monkeypatch):
    port = websocketServer.get_free_port()
    server_this = {'hash': 'bot-a', 'port': port}
    main.ProcObj = _Proc()
    main.confDict['bot-a'] = server_this
    main.botInfoDict['bot-a'] = SimpleNamespace(
        hash='bot-a',
        id=42,
        platform={'platform': 'qq'},
    )
    monkeypatch.setattr(eventRouter.OlivOS.API, 'Event', _LoginEvent)

    async def scenario():
        serve_task = asyncio.create_task(websocketServer.serve(server_this))
        connection = None
        try:
            for _ in range(100):
                try:
                    connection = await websockets.connect('ws://127.0.0.1:%d' % port)
                    break
                except OSError:
                    await asyncio.sleep(0.02)
            assert connection is not None

            async with connection:
                await _wait_until(lambda: len(websocketServer.clientList) == 1)
                assert websocketServer.clientMapDict['bot-a'] == str(port)
                assert websocketServer.clientDict[str(port)][0]['info']['hash'] == 'bot-a'

                await connection.send(json.dumps({
                    'action': 'get_login_info',
                    'echo': 'request-4',
                    'params': {},
                }))
                response = json.loads(await asyncio.wait_for(connection.recv(), timeout=2))
                assert response == {
                    'echo': 'request-4',
                    'status': 'ok',
                    'retcode': 0,
                    'data': {'user_id': 42, 'nickname': 'Alice'},
                }

                adapter = websocketServer.clientDict[str(port)][0]['obj']
                assert adapter.server_port == port
                assert adapter.address is not None
                thread = threading.Thread(
                    target=adapter.sendMessage,
                    args=(json.dumps({'post_type': 'meta_event'}),)
                )
                thread.start()
                thread.join(timeout=2)
                assert thread.is_alive() is False
                pushed = json.loads(await asyncio.wait_for(connection.recv(), timeout=2))
                assert pushed == {'post_type': 'meta_event'}

            await _wait_until(lambda: websocketServer.clientList == [])
            await _wait_until(lambda: websocketServer.clientDict[str(port)] == [])
        finally:
            serve_task.cancel()
            await asyncio.gather(serve_task, return_exceptions=True)

    asyncio.run(scenario())
