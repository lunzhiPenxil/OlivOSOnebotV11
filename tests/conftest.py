import importlib
import sys
import types

import pytest


class _FakePara(object):
    def __init__(self, para_type, data):
        self.type = para_type
        self.data = data


class _FakeParaFactory(object):
    @staticmethod
    def at(**kwargs):
        return _FakePara('at', kwargs)

    @staticmethod
    def text(**kwargs):
        return _FakePara('text', kwargs)


class _FakeMessageTemplet(object):
    def __init__(self, mode, data):
        self.mode = mode
        self.data = data

    def __eq__(self, other):
        return (
            isinstance(other, _FakeMessageTemplet) and
            self.mode == other.mode and
            self.data == other.data
        )


class _FakeEvent(object):
    def __init__(self, sdk_event=None, log=None):
        self.sdk_event = sdk_event
        self.log = log
        self.bot_info = getattr(sdk_event, 'bot_info', None)


class _FakeSDKEvent(object):
    def __init__(self, bot_info, fakename):
        self.bot_info = bot_info
        self.fakename = fakename


class _FakeShallow(object):
    pass


def _install_olivos_stub():
    for module_name in list(sys.modules):
        if module_name == 'OlivOS' or module_name.startswith('OlivOS.'):
            del sys.modules[module_name]

    olivos = types.ModuleType('OlivOS')
    api = types.ModuleType('OlivOS.API')
    plugin_api = types.ModuleType('OlivOS.pluginAPI')
    content_api = types.ModuleType('OlivOS.contentAPI')
    message_api = types.ModuleType('OlivOS.messageAPI')

    api.Event = _FakeEvent
    plugin_api.shallow = _FakeShallow
    content_api.fake_sdk_event = lambda bot_info, fakename: _FakeSDKEvent(bot_info, fakename)
    message_api.PARA = _FakeParaFactory
    message_api.Message_templet = _FakeMessageTemplet

    olivos.API = api
    olivos.pluginAPI = plugin_api
    olivos.contentAPI = content_api
    olivos.messageAPI = message_api

    sys.modules['OlivOS'] = olivos
    sys.modules['OlivOS.API'] = api
    sys.modules['OlivOS.pluginAPI'] = plugin_api
    sys.modules['OlivOS.contentAPI'] = content_api
    sys.modules['OlivOS.messageAPI'] = message_api


_install_olivos_stub()


def _reset_plugin_state():
    main = importlib.import_module('OlivOSOnebotV11.main')
    websocket_link = importlib.import_module('OlivOSOnebotV11.websocketLink')
    websocket_server = importlib.import_module('OlivOSOnebotV11.websocketServer')

    main.ProcObj = None
    main.botInfoDict.clear()
    main.confDict.clear()
    main.r_confDict.clear()
    main.hostIdDict.clear()
    main.mappingIdDict.clear()
    main.eventRegDict.clear()

    websocket_link.clientList.clear()
    websocket_link.clientDict.clear()
    websocket_link.clientMapDict.clear()

    websocket_server.server = None
    websocket_server.clientList.clear()
    websocket_server.clientDict.clear()
    websocket_server.clientMapDict.clear()


@pytest.fixture(autouse=True)
def reset_plugin_state():
    _reset_plugin_state()
    yield
    _reset_plugin_state()
