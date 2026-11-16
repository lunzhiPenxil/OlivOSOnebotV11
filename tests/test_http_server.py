import http.client
import json
import threading
from contextlib import contextmanager
from types import SimpleNamespace

from OlivOSOnebotV11 import eventRouter, httpServer, main


class _Proc(object):
    def __init__(self):
        self.logs = []

    def log(self, level, message, segment):
        self.logs.append((level, message, segment))


class _HttpEvent(object):
    calls = []

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

    def send_like(self, user_id, times=1):
        self.calls.append(('send_like', user_id, times))


@contextmanager
def _running_server(monkeypatch, access_token=''):
    port = httpServer.get_free_port()
    main.ProcObj = _Proc()
    main.confDict['bot-a'] = {'hash': 'bot-a', 'port': 43000}
    main.botInfoDict['bot-a'] = SimpleNamespace(
        hash='bot-a',
        id=42,
        platform={'platform': 'qq'},
    )
    monkeypatch.setattr(eventRouter.OlivOS.API, 'Event', _HttpEvent)
    _HttpEvent.calls = []
    server_this = {
        'hash': 'bot-a',
        'port': port,
        'access_token': access_token,
    }
    server_obj = httpServer.create_server(server_this)
    thread = threading.Thread(target=server_obj.serve_forever, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        server_obj.shutdown()
        server_obj.server_close()
        thread.join(timeout=2)


def _request(port, path, method='GET', body=None, headers=None):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        content = response.read().decode('utf-8')
        payload = None
        if content:
            payload = json.loads(content)
        return response.status, payload
    finally:
        connection.close()


def test_http_get_action_keeps_response_contract(monkeypatch):
    with _running_server(monkeypatch) as port:
        status, payload = _request(port, '/get_login_info?echo=request-1')

    assert status == 200
    assert payload == {
        'echo': 'request-1',
        'status': 'ok',
        'retcode': 0,
        'data': {'user_id': 42, 'nickname': 'Alice'},
    }


def test_http_action_echo_is_optional(monkeypatch):
    with _running_server(monkeypatch) as port:
        status, payload = _request(port, '/get_login_info')

    assert status == 200
    assert payload['status'] == 'ok'
    assert 'echo' not in payload


def test_http_post_json_action_parses_string_numbers(monkeypatch):
    with _running_server(monkeypatch) as port:
        status, payload = _request(
            port,
            '/send_like/',
            method='POST',
            body=json.dumps({
                'user_id': '42',
                'times': '3',
                'echo': 'request-2',
            }),
            headers={'Content-Type': 'application/json'},
        )

    assert status == 200
    assert payload['echo'] == 'request-2'
    assert _HttpEvent.calls == [('send_like', '42', 3)]


def test_http_post_form_action(monkeypatch):
    with _running_server(monkeypatch) as port:
        status, payload = _request(
            port,
            '/send_like',
            method='POST',
            body='user_id=42&times=2',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )

    assert status == 200
    assert payload['status'] == 'ok'
    assert _HttpEvent.calls == [('send_like', '42', 2)]


def test_http_parse_param_keeps_message_and_flag_as_strings():
    assert httpServer.parse_http_param('times', '3') == 3
    assert httpServer.parse_http_param('auto_escape', 'true') is True
    assert httpServer.parse_http_param('flag', '00123') == '00123'
    assert httpServer.parse_http_param(
        'message',
        json.dumps([{'type': 'text', 'data': {'text': 'hi'}}])
    ) == [
        {'type': 'text', 'data': {'text': 'hi'}}
    ]
    assert httpServer.parse_http_param('message', '[CQ:face,id=1]') == '[CQ:face,id=1]'


def test_http_unknown_action_returns_404(monkeypatch):
    with _running_server(monkeypatch) as port:
        status, payload = _request(port, '/not_an_action')

    assert status == 404
    assert payload['status'] == 'failed'
    assert payload['retcode'] == 1404


def test_http_rejects_unsupported_content_type(monkeypatch):
    with _running_server(monkeypatch) as port:
        status, payload = _request(
            port,
            '/get_login_info',
            method='POST',
            body='echo=request-3',
            headers={'Content-Type': 'text/plain'},
        )

    assert status == 406
    assert payload['status'] == 'failed'
    assert payload['retcode'] == 4060


def test_http_rejects_invalid_json_body(monkeypatch):
    with _running_server(monkeypatch) as port:
        status, payload = _request(
            port,
            '/get_login_info',
            method='POST',
            body='{invalid-json',
            headers={'Content-Type': 'application/json'},
        )

    assert status == 400
    assert payload['status'] == 'failed'
    assert payload['retcode'] == 4000


def test_http_access_token_accepts_header_and_query(monkeypatch):
    with _running_server(monkeypatch, access_token='token-a') as port:
        missing_status, _ = _request(port, '/get_login_info')
        wrong_status, _ = _request(
            port,
            '/get_login_info',
            headers={'Authorization': 'Bearer token-b'},
        )
        query_status, query_payload = _request(port, '/get_login_info?access_token=token-a')
        header_status, header_payload = _request(
            port,
            '/get_login_info',
            headers={'Authorization': 'Bearer token-a'},
        )

    assert missing_status == 401
    assert wrong_status == 403
    assert query_status == 200
    assert query_payload['status'] == 'ok'
    assert header_status == 200
    assert header_payload['status'] == 'ok'


def test_http_post_auth_error_drains_body_for_keep_alive(monkeypatch):
    with _running_server(monkeypatch, access_token='token-a') as port:
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
        try:
            connection.request(
                'POST',
                '/get_login_info',
                body=json.dumps({'echo': 'unauthorized'}),
                headers={'Content-Type': 'application/json'}
            )
            response = connection.getresponse()
            response.read()
            assert response.status == 401

            connection.request('GET', '/get_login_info?access_token=token-a')
            response = connection.getresponse()
            payload = json.loads(response.read().decode('utf-8'))
            assert response.status == 200
            assert payload['status'] == 'ok'
        finally:
            connection.close()
