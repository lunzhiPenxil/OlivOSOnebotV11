# -*- encoding: utf-8 -*-
'''
@File      :   httpServer.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2022, lunzhiPenxil仑质
@Desc      :   None
'''

import hmac
import http.server
import json
import re
import socket
import threading
import traceback
import urllib.parse
from contextlib import closing

import OlivOSOnebotV11

serverList = []
serverDict = {}

STRING_PARAM_KEYS = {
    'message',
    'message_type',
    'sub_type',
    'flag',
    'reason',
    'remark',
    'card',
    'group_name',
    'special_title',
    'echo',
}


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


def get_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def parse_http_param(key, value):
    if not isinstance(value, str):
        return value
    if key in STRING_PARAM_KEYS:
        if key == 'message' and value[:1] in ('[', '{'):
            try:
                return json.loads(value)
            except (TypeError, ValueError):
                pass
        return value
    lowered = value.lower()
    if lowered == 'true':
        return True
    if lowered == 'false':
        return False
    if lowered == 'null':
        return None
    if re.match(r'^-?\d+$', value):
        try:
            return int(value)
        except ValueError:
            pass
    if re.match(r'^-?(?:\d+\.\d*|\d*\.\d+)$', value):
        try:
            return float(value)
        except ValueError:
            pass
    if value[:1] in ('[', '{'):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            pass
    return value


def parse_pairs(pairs):
    res = {}
    for key in pairs:
        if key == 'access_token':
            continue
        values = pairs[key]
        value = ''
        if isinstance(values, list) and len(values) >= 1:
            value = values[-1]
        res[key] = parse_http_param(key, value)
    return res


def errorPayload(retcode, echo=None):
    res = {
        'status': 'failed',
        'retcode': retcode,
        'data': None
    }
    if echo is not None:
        res['echo'] = echo
    return res


class httpRequestAdapter(object):
    def __init__(self, data, server_port, bot_hash):
        self.data = data
        self.server_port = int(server_port)
        self.bot_hash = bot_hash
        self.messages = []

    def sendMessage(self, message):
        self.messages.append(message)


class httpRequestHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.handle_api_request()

    def do_POST(self):
        self.handle_api_request()

    def send_json_text(self, status, text):
        body = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        if self.close_connection:
            self.send_header('Connection', 'close')
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_json(self, status, payload):
        self.send_json_text(status, json.dumps(payload, ensure_ascii=False))

    def check_access_token(self, server_this, query_data):
        token = server_this.get('access_token') or server_this.get('token') or ''
        if not token:
            return None
        auth = self.headers.get('Authorization', '')
        provided = None
        if auth.lower().startswith('bearer '):
            provided = auth[7:]
        if provided is None:
            values = query_data.get('access_token', [])
            if isinstance(values, list) and len(values) >= 1:
                provided = values[-1]
        if provided is None:
            return 401
        if not hmac.compare_digest(
            str(provided).encode('utf-8'),
            str(token).encode('utf-8')
        ):
            return 403
        return None

    def read_post_params(self):
        content_type = self.headers.get('Content-Type', '')
        content_type = content_type.split(';', 1)[0].strip().lower()
        if content_type not in ('application/json', 'application/x-www-form-urlencoded'):
            self.close_connection = True
            return 406, None
        length_text = self.headers.get('Content-Length', '0')
        try:
            length = int(length_text)
        except (TypeError, ValueError):
            self.close_connection = True
            return 400, None
        if length < 0:
            self.close_connection = True
            return 400, None
        body = self.rfile.read(length)
        if content_type == 'application/json':
            if not body:
                return 200, {}
            try:
                payload = json.loads(body.decode('utf-8'))
            except (TypeError, ValueError, UnicodeDecodeError):
                return 400, None
            if not isinstance(payload, dict):
                return 400, None
            res = {}
            for key in payload:
                if key == 'access_token':
                    continue
                res[key] = parse_http_param(key, payload[key])
            return 200, res
        try:
            text = body.decode('utf-8')
        except UnicodeDecodeError:
            return 400, None
        return 200, parse_pairs(urllib.parse.parse_qs(text, keep_blank_values=True))

    def handle_api_request(self):
        try:
            self.handle_api_request_inner()
        except Exception as e:
            skip_result = '%s\n%s' % (
                str(e),
                traceback.format_exc()
            )
            log(3, skip_result)
            self.send_json(500, errorPayload(1500))

    def handle_api_request_inner(self):
        request_data = urllib.parse.urlsplit(self.path)
        query_data = urllib.parse.parse_qs(request_data.query, keep_blank_values=True)
        params = parse_pairs(query_data)
        if self.command == 'POST':
            status, post_params = self.read_post_params()
            if status != 200:
                self.send_json(status, errorPayload(status * 10))
                return
            params.update(post_params)
        path = request_data.path
        if path != '/' and path.endswith('/'):
            path = path[:-1]
        action = urllib.parse.unquote(path[1:]) if path.startswith('/') else ''
        if not action or '/' in action or action.startswith('_'):
            self.send_json(404, errorPayload(1404))
            return
        server_this = getattr(self.server, 'server_this', {})
        auth_status = self.check_access_token(server_this, query_data)
        if auth_status == 401:
            self.send_json(401, errorPayload(1401))
            return
        if auth_status == 403:
            self.send_json(403, errorPayload(1403))
            return
        echo = params.pop('echo', None)
        action_func = getattr(OlivOSOnebotV11.eventRouter.actionRouter, action, None)
        if not callable(action_func):
            self.send_json(404, errorPayload(1404, echo))
            return
        payload = {
            'action': action,
            'params': params
        }
        if echo is not None:
            payload['echo'] = echo
        adapter = httpRequestAdapter(
            json.dumps(payload, ensure_ascii=False),
            server_this['port'],
            server_this['hash']
        )
        actionObj = OlivOSOnebotV11.eventRouter.txEvent(adapter, hostType='http')
        actionObj.doRouter()
        if actionObj.rvMsg is not None:
            self.send_json_text(200, actionObj.rvMsg)
            return
        self.send_json(200, errorPayload(1100, echo))


class httpThreadingServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def create_server(server_this):
    port = int(server_this['port'])
    server_obj = httpThreadingServer(('0.0.0.0', port), httpRequestHandler)
    server_obj.server_this = server_this
    return server_obj


def init_http(server_this):
    if server_this.get('port') is None:
        return
    server_obj = None
    try:
        server_obj = create_server(server_this)
        serverList.append(server_obj)
        serverDict[str(server_this['port'])] = server_obj
        log(
            2,
            '账号 [' + format_bot_info(server_this['hash']) + '] 运行于HTTP，请使用 [http://localhost:' +
            str(server_this['port']) + '/] 进行调用'
        )
        server_obj.serve_forever()
    except Exception as e:
        skip_result = '%s\n%s' % (
            str(e),
            traceback.format_exc()
        )
        log(3, skip_result)
    finally:
        if server_obj is not None:
            server_obj.server_close()
            if server_obj in serverList:
                serverList.remove(server_obj)
            serverDict.pop(str(server_this['port']), None)


def start_http(confDict):
    for bot_hash in confDict:
        server_this = confDict[bot_hash]
        if server_this.get('port') is None:
            continue
        threading.Thread(
            target=OlivOSOnebotV11.httpServer.init_http,
            args=(server_this,),
            daemon=True
        ).start()
