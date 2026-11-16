import json
import socket
import struct
from types import SimpleNamespace

import pytest

from OlivOSOnebotV11 import SimpleWebSocketServer, eventRouter, main, websocketServer


class _CaptureWebSocket(SimpleWebSocketServer.WebSocket):
    def __init__(self):
        super().__init__(None, None, None)
        self.messages = []
        self.close_calls = []

    def handleMessage(self):
        self.messages.append(self.data)

    def close(self, status=1000, reason=''):
        self.close_calls.append((status, reason))


class _Proc(object):
    def __init__(self):
        self.logs = []

    def log(self, level, message, segment):
        self.logs.append((level, message, segment))


class _SocketHolder(object):
    def __init__(self, port):
        self.port = port

    def getsockname(self):
        return ('127.0.0.1', self.port)


class _ServerHolder(object):
    def __init__(self, port):
        self.serversocket = _SocketHolder(port)


class _WebSocket(object):
    def __init__(self, data=None, port=43000):
        self.data = data
        self.server = _ServerHolder(port)
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


def _masked_frame(opcode, payload):
    mask = b'\x01\x02\x03\x04'
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    return bytes([0x80 | opcode, 0x80 | len(payload)]) + mask + masked


def _feed(websocket, frame):
    for byte in frame:
        websocket._parseMessage(byte)


def test_check_unicode_matches_python3_strings():
    assert SimpleWebSocketServer._check_unicode('text') is True
    assert SimpleWebSocketServer._check_unicode(b'text') is False


def test_websocket_parses_masked_text_frame():
    websocket = _CaptureWebSocket()

    _feed(websocket, _masked_frame(SimpleWebSocketServer.TEXT, b'hello'))

    assert websocket.messages == ['hello']


def test_websocket_rejects_invalid_utf8_text_frame():
    websocket = _CaptureWebSocket()

    with pytest.raises(Exception, match='invalid utf-8 payload'):
        _feed(websocket, _masked_frame(SimpleWebSocketServer.TEXT, b'\xff'))


def test_websocket_close_frame_keeps_valid_reason():
    websocket = _CaptureWebSocket()
    payload = struct.pack('!H', 1000) + 'bye'.encode('utf-8')

    _feed(websocket, _masked_frame(SimpleWebSocketServer.CLOSE, payload))

    assert websocket.close_calls == [(1000, 'bye')]


def test_websocket_close_frame_marks_invalid_reason_as_protocol_error():
    websocket = _CaptureWebSocket()
    payload = struct.pack('!H', 1000) + b'\xff'

    _feed(websocket, _masked_frame(SimpleWebSocketServer.CLOSE, payload))

    assert websocket.close_calls[0][0] == 1002


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
    websocketServer.clientDict['43000'] = [{'info': {'hash': 'bot-a'}}]
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
            'echo': 'request-2',
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
