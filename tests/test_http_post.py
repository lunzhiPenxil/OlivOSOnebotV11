import hashlib
import hmac
import json
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

from OlivOSOnebotV11 import httpPost, main


class _Proc(object):
    def __init__(self):
        self.logs = []

    def log(self, level, message, segment):
        self.logs.append((level, message, segment))


class _CaptureHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length)
        self.server.requests.append({
            'path': self.path,
            'headers': dict(self.headers.items()),
            'body': body,
        })
        response_body = self.server.response_body
        self.send_response(self.server.response_status)
        self.send_header('Content-Length', str(len(response_body)))
        self.end_headers()
        if response_body:
            self.wfile.write(response_body)


@contextmanager
def _capture_server(response_status=204, response_body=b''):
    server_obj = ThreadingHTTPServer(('127.0.0.1', 0), _CaptureHandler)
    server_obj.daemon_threads = True
    server_obj.requests = []
    server_obj.response_status = response_status
    server_obj.response_body = response_body
    thread = threading.Thread(target=server_obj.serve_forever, daemon=True)
    thread.start()
    port = server_obj.server_address[1]
    try:
        yield server_obj, 'http://127.0.0.1:%d/' % port
    finally:
        server_obj.shutdown()
        server_obj.server_close()
        thread.join(timeout=2)


def _wait_until(predicate, timeout=2.0):
    deadline = time.time() + timeout
    while not predicate():
        if time.time() >= deadline:
            raise AssertionError('condition was not met before timeout')
        time.sleep(0.01)


class _QuickEvent(object):
    def __init__(self, data=None):
        self.data = data
        self.replies = []
        self.calls = []

    def reply(self, message):
        self.replies.append(message)

    def delete_msg(self, message_id):
        self.calls.append(('delete_msg', message_id))

    def set_group_kick(self, group_id, user_id, host_id=None):
        self.calls.append(('set_group_kick', group_id, user_id, host_id))

    def set_group_ban(self, group_id, user_id, host_id=None, duration=1800):
        self.calls.append(('set_group_ban', group_id, user_id, host_id, duration))


def test_http_post_report_signs_body_and_maps_self_id():
    main.ProcObj = _Proc()
    main.botInfoDict['bot-a'] = SimpleNamespace(id=42, platform={'platform': 'qq'})
    message = json.dumps({'post_type': 'meta_event', 'self_id': 42})

    with _capture_server() as (server_obj, url):
        httpPost.start_http_post({
            'bot-a': {
                'hash': 'bot-a',
                'path': [url],
                'secret': 'secret-a',
                'timeout': 2,
            }
        })
        try:
            assert httpPost.send('bot-a', message) == 1
            _wait_until(lambda: len(server_obj.requests) == 1)
        finally:
            httpPost.stop_all()

    request_data = server_obj.requests[0]
    expected_signature = hmac.new(
        b'secret-a',
        message.encode('utf-8'),
        hashlib.sha1
    ).hexdigest()
    assert request_data['path'] == '/'
    assert request_data['body'].decode('utf-8') == message
    headers = {key.lower(): value for key, value in request_data['headers'].items()}
    assert headers['x-self-id'] == '42'
    assert headers['x-signature'] == 'sha1=' + expected_signature
    assert headers['content-type'] == 'application/json; charset=utf-8'


def test_http_post_applies_reply_quick_action():
    main.ProcObj = _Proc()
    with _capture_server(
        response_status=200,
        response_body=json.dumps({'reply': 'pong'}).encode('utf-8')
    ) as (server_obj, url):
        event = _QuickEvent()
        endpoint = httpPost.endpoint(url, timeout=2)

        assert endpoint.post('{post_type:message}', event) is True

    assert len(server_obj.requests) == 1
    assert len(event.replies) == 1
    assert event.replies[0].mode_rx == 'old_string'
    assert event.replies[0].get('old_string') == 'pong'


def test_http_post_applies_group_quick_actions():
    event = _QuickEvent(SimpleNamespace(
        message_id=99,
        group_id=100,
        user_id=42,
        host_id=200,
    ))

    httpPost.handle_quick_actions(event, {
        'delete': True,
        'kick': True,
        'ban': True,
        'ban_duration': 60,
    })

    assert event.calls == [
        ('delete_msg', '99'),
        ('set_group_kick', '100', '42', 200),
        ('set_group_ban', '100', '42', 200, 60),
    ]


def test_http_post_quick_reply_supports_auto_escape_and_at_sender():
    event = _QuickEvent(SimpleNamespace(user_id=42))

    httpPost.handle_quick_actions(event, {
        'reply': '[CQ:face,id=1]',
        'auto_escape': True,
        'at_sender': True,
    })

    assert len(event.replies) == 1
    message = event.replies[0]
    assert message.mode_rx == 'olivos_para'
    assert [para.type for para in message.data] == ['at', 'text']
    assert message.data[0].data['id'] == '42'
    assert message.data[0].data['name'] is None
    assert message.data[1].data == {'text': '[CQ:face,id=1]'}
