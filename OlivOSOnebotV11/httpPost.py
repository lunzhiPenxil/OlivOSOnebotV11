# -*- encoding: utf-8 -*-
'''
@File      :   httpPost.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2022, lunzhiPenxil仑质
@Desc      :   None
'''

import hashlib
import hmac
import json
import queue
import threading
import traceback
from urllib import error, request

import OlivOS
import OlivOSOnebotV11

DEFAULT_TIMEOUT = 5
QUEUE_MAXSIZE = 256

endpointDict = {}
endpointList = []


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


def get_self_id(bot_hash):
    bot_info = OlivOSOnebotV11.main.botInfoDict.get(bot_hash)
    if bot_info is None:
        return None
    return getattr(bot_info, 'id', None)


def as_bool(value):
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes', 'on')
    return bool(value)


def build_quick_reply(plugin_event, payload):
    reply = payload.get('reply')
    if reply is None:
        return None
    if as_bool(payload.get('auto_escape', False)) and isinstance(reply, str):
        message = OlivOS.messageAPI.Message_templet(
            'olivos_para',
            [OlivOS.messageAPI.PARA.text(text=reply)]
        )
    else:
        message = OlivOSOnebotV11.eventRouter.paraRvMapper(reply)
    if as_bool(payload.get('at_sender', False)):
        event_data = getattr(plugin_event, 'data', None)
        user_id = getattr(event_data, 'user_id', None)
        if user_id is not None and message is not None:
            message.data.insert(0, OlivOS.messageAPI.PARA.at(id=str(user_id)))
    return message


def handle_quick_actions(plugin_event, payload):
    if plugin_event is None or not isinstance(payload, dict):
        return
    try:
        if 'reply' in payload and payload['reply'] is not None:
            message = build_quick_reply(plugin_event, payload)
            plugin_event.reply(message)
    except Exception as e:
        skip_result = '%s\n%s' % (
            str(e),
            traceback.format_exc()
        )
        log(3, skip_result)
    event_data = getattr(plugin_event, 'data', None)
    if event_data is None:
        return
    message_id = getattr(event_data, 'message_id', None)
    group_id = getattr(event_data, 'group_id', None)
    user_id = getattr(event_data, 'user_id', None)
    host_id = getattr(event_data, 'host_id', None)
    try:
        if as_bool(payload.get('delete', False)) and message_id is not None:
            plugin_event.delete_msg(str(message_id))
    except Exception as e:
        skip_result = '%s\n%s' % (
            str(e),
            traceback.format_exc()
        )
        log(3, skip_result)
    if group_id is None or user_id is None:
        return
    try:
        if as_bool(payload.get('kick', False)):
            plugin_event.set_group_kick(
                str(group_id),
                str(user_id),
                host_id=host_id
            )
        if as_bool(payload.get('ban', False)):
            plugin_event.set_group_ban(
                str(group_id),
                str(user_id),
                host_id=host_id,
                duration=int(payload.get('ban_duration', 30 * 60))
            )
    except Exception as e:
        skip_result = '%s\n%s' % (
            str(e),
            traceback.format_exc()
        )
        log(3, skip_result)


class endpoint(object):
    def __init__(self, url, secret='', timeout=DEFAULT_TIMEOUT, bot_hash=None, self_id=None):
        self.url = url
        self.secret = secret
        self.timeout = timeout
        self.bot_hash = bot_hash
        self.self_id = self_id
        self.queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
        self.stopEvent = threading.Event()
        self.thread = None

    def start(self):
        if self.thread is not None:
            return
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stopEvent.set()
        try:
            self.queue.put_nowait(None)
        except queue.Full:
            pass
        if self.thread is not None:
            self.thread.join(timeout=2)
            self.thread = None

    def send(self, message, plugin_event=None):
        if not isinstance(message, (str, bytes)):
            message = json.dumps(message, ensure_ascii=False)
        try:
            self.queue.put_nowait((message, plugin_event))
            return True
        except queue.Full:
            log(3, 'HTTP上报队列已满，事件已丢弃')
            return False

    def run(self):
        while not self.stopEvent.is_set():
            try:
                item = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                if item is None or self.stopEvent.is_set():
                    break
                message, plugin_event = item
                self.post(message, plugin_event)
            finally:
                self.queue.task_done()

    def build_headers(self, body):
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'User-Agent': 'OlivOSOnebotV11'
        }
        if self.self_id is not None:
            headers['X-Self-ID'] = str(self.self_id)
        if self.secret:
            signature = hmac.new(
                str(self.secret).encode('utf-8'),
                body,
                hashlib.sha1
            ).hexdigest()
            headers['X-Signature'] = 'sha1=' + signature
        return headers

    def post(self, message, plugin_event=None):
        if isinstance(message, bytes):
            body = message
        else:
            body = str(message).encode('utf-8')
        headers = self.build_headers(body)
        req = request.Request(
            self.url,
            data=body,
            headers=headers,
            method='POST'
        )
        timeout = self.timeout
        if timeout is not None and timeout <= 0:
            timeout = None
        try:
            response = request.urlopen(req, timeout=timeout)
            try:
                status = response.getcode()
                content = response.read()
            finally:
                response.close()
            if status >= 400:
                log(3, 'HTTP上报返回状态码 [%s]：%s' % (str(status), self.url))
                return False
            if content:
                try:
                    payload = json.loads(content.decode('utf-8'))
                except (TypeError, ValueError, UnicodeDecodeError):
                    payload = None
                if payload is not None:
                    handle_quick_actions(plugin_event, payload)
            return True
        except error.HTTPError as e:
            log(3, 'HTTP上报返回状态码 [%s]：%s' % (str(e.code), self.url))
            return False
        except Exception as e:
            skip_result = '%s\n%s' % (
                str(e),
                traceback.format_exc()
            )
            log(3, skip_result)
            return False


def start_http_post(confDict):
    for bot_hash in confDict:
        conf_this = confDict[bot_hash]
        paths = conf_this.get('path', [])
        if not isinstance(paths, list):
            continue
        secret = conf_this.get('secret', '')
        timeout = conf_this.get('timeout', DEFAULT_TIMEOUT)
        try:
            timeout = float(timeout)
        except (TypeError, ValueError):
            timeout = DEFAULT_TIMEOUT
        for url in paths:
            if not isinstance(url, str) or len(url) <= 0:
                continue
            endpoint_obj = endpoint(
                url,
                secret=secret,
                timeout=timeout,
                bot_hash=bot_hash,
                self_id=get_self_id(bot_hash)
            )
            endpointDict.setdefault(bot_hash, []).append(endpoint_obj)
            endpointList.append(endpoint_obj)
            endpoint_obj.start()
            log(
                2,
                '账号 [' + format_bot_info(bot_hash) + '] 运行于HTTP上报，事件将发送至 [' + url + ']'
            )


def send(bot_hash, message, plugin_event=None):
    endpoints = endpointDict.get(bot_hash, [])
    count = 0
    for endpoint_obj in endpoints:
        if endpoint_obj.send(message, plugin_event):
            count += 1
    return count


def stop_all():
    for endpoint_obj in list(endpointList):
        endpoint_obj.stop()
    endpointList.clear()
    endpointDict.clear()
