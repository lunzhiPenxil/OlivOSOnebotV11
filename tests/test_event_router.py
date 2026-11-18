import json
from pathlib import Path

from OlivOSOnebotV11 import eventRouter, httpPost, main, websocketLink, websocketServer


class _Para(object):
    def __init__(self, para_type, data):
        self.type = para_type
        self.data = data

    def CQ(self):
        if self.type == 'at':
            return '[CQ:at,qq=%s]' % self.data['id']
        return str(self.data['text'])


class _BotInfo(object):
    hash = 'bot-a'


class _PluginEvent(object):
    def __init__(self):
        self.bot_info = _BotInfo()
        self.base_info = {'self_id': '42', 'time': 1700000000}
        self.data = None


class _Proc(object):
    def __init__(self):
        self.logs = []

    def log(self, level, message, segment):
        self.logs.append((level, message, segment))


class _MessageSink(object):
    def __init__(self):
        self.messages = []

    def sendMessage(self, message):
        self.messages.append(message)

    def send(self, message):
        self.messages.append(message)


def test_init_bot_info_reads_config_and_fills_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = Path('plugin/data/OlivOSOnebotV11/config.json')
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps({
            'route': [
                {'hash': 'bot-a', 'port': 43000},
                {'hash': 'removed-bot', 'port': 43001},
                {'hash': 'invalid-route'},
            ],
            'r-route': [
                {'hash': 'bot-a', 'path': ['ws://127.0.0.1:8080/onebot/v11/ws']},
                {'hash': 'bot-b', 'path': 'invalid-path'},
            ],
            'http-route': [
                {'hash': 'bot-a', 'port': 5700, 'access_token': 'token-a'},
                {'hash': 'removed-bot', 'port': 5701},
                {'hash': 'invalid-http-route'},
            ],
            'r-http-route': [
                {
                    'hash': 'bot-a',
                    'path': ['http://127.0.0.1:8080/onebot/v11/http'],
                    'secret': 'secret-a',
                    'timeout': 2,
                },
                {'hash': 'bot-b', 'path': 'invalid-path'},
            ],
        }),
        encoding='utf-8'
    )

    route, reverse_route = eventRouter.initBotInfo(
        {'bot-a': object(), 'bot-b': object()},
        default_port=55010
    )

    assert route == {
        'bot-a': {'hash': 'bot-a', 'port': 43000},
        'bot-b': {'hash': 'bot-b', 'port': 55010},
    }
    assert reverse_route == {
        'bot-a': {'hash': 'bot-a', 'path': ['ws://127.0.0.1:8080/onebot/v11/ws']},
        'bot-b': {'hash': 'bot-b', 'path': []},
    }
    http_route, reverse_http_route = eventRouter.initHttpBotInfo({'bot-a': object(), 'bot-b': object()})
    assert http_route == {
        'bot-a': {'hash': 'bot-a', 'port': 5700, 'access_token': 'token-a'},
        'bot-b': {'hash': 'bot-b', 'port': None},
    }
    assert reverse_http_route == {
        'bot-a': {
            'hash': 'bot-a',
            'path': ['http://127.0.0.1:8080/onebot/v11/http'],
            'secret': 'secret-a',
            'timeout': 2,
        },
        'bot-b': {'hash': 'bot-b', 'path': []},
    }
    assert set(main.eventRegDict) == {'bot-a', 'bot-b'}


def test_init_bot_info_falls_back_on_invalid_section_types(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = Path('plugin/data/OlivOSOnebotV11/config.json')
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps({
            'route': [None],
            'r-route': [None],
            'http-route': [None],
            'r-http-route': [None],
        }),
        encoding='utf-8'
    )

    route, reverse_route = eventRouter.initBotInfo({'bot-a': object()}, default_port=55011)

    assert route == {'bot-a': {'hash': 'bot-a', 'port': 55011}}
    assert reverse_route == {'bot-a': {'hash': 'bot-a', 'path': []}}
    http_route, reverse_http_route = eventRouter.initHttpBotInfo({'bot-a': object()})
    assert http_route == {'bot-a': {'hash': 'bot-a', 'port': None}}
    assert reverse_http_route == {'bot-a': {'hash': 'bot-a', 'path': []}}


def test_save_bot_info_round_trips(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    route = {'bot-a': {'hash': 'bot-a', 'port': 43000}}
    reverse_route = {'bot-a': {'hash': 'bot-a', 'path': ['ws://127.0.0.1:8080']}}
    http_route = {'bot-a': {'hash': 'bot-a', 'port': 5700, 'access_token': 'token-a'}}
    reverse_http_route = {
        'bot-a': {
            'hash': 'bot-a',
            'path': ['http://127.0.0.1:8080/onebot/v11/http'],
            'secret': 'secret-a',
            'timeout': 2,
        }
    }

    eventRouter.saveBotInfo(route, reverse_route, http_route, reverse_http_route)
    saved = json.loads(Path('plugin/data/OlivOSOnebotV11/config.json').read_text(encoding='utf-8'))

    assert saved == {
        'route': [{'hash': 'bot-a', 'port': 43000}],
        'r-route': [{'hash': 'bot-a', 'path': ['ws://127.0.0.1:8080']}],
        'http-route': [{'hash': 'bot-a', 'port': 5700, 'access_token': 'token-a'}],
        'r-http-route': [{
            'hash': 'bot-a',
            'path': ['http://127.0.0.1:8080/onebot/v11/http'],
            'secret': 'secret-a',
            'timeout': 2,
        }],
    }
    loaded_route, loaded_reverse_route = eventRouter.initBotInfo({'bot-a': object()})
    loaded_http_route, loaded_reverse_http_route = eventRouter.initHttpBotInfo({'bot-a': object()})
    assert loaded_route == route
    assert loaded_reverse_route == reverse_route
    assert loaded_http_route == http_route
    assert loaded_reverse_http_route == reverse_http_route


def test_save_bot_info_preserves_http_sections_for_legacy_callers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = Path('plugin/data/OlivOSOnebotV11/config.json')
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps({
            'http-route': [{'hash': 'bot-a', 'port': 5700}],
            'r-http-route': [{'hash': 'bot-a', 'path': ['http://127.0.0.1:8080/']}],
        }),
        encoding='utf-8'
    )

    eventRouter.saveBotInfo(
        {'bot-a': {'hash': 'bot-a', 'port': 43000}},
        {'bot-a': {'hash': 'bot-a', 'path': []}}
    )

    saved = json.loads(config_path.read_text(encoding='utf-8'))
    assert saved['http-route'] == [{'hash': 'bot-a', 'port': 5700}]
    assert saved['r-http-route'] == [{'hash': 'bot-a', 'path': ['http://127.0.0.1:8080/']}]


def test_backport_int_preserves_values_that_cannot_be_converted():
    assert eventRouter.backport_int('123') == 123
    assert eventRouter.backport_int(123) == 123
    assert eventRouter.backport_int('wxid_abc') == 'wxid_abc'
    assert eventRouter.backport_int(None) is None


def test_mapping_ids_support_numeric_and_platform_ids():
    assert eventRouter.setMappingIdDict('bot-a', '123') == 123
    assert eventRouter.getMappingIdDict('bot-a', '123') == '123'

    mapped = eventRouter.setMappingIdDict('bot-a', 'wxid_abc')
    assert isinstance(mapped, int)
    assert eventRouter.setMappingIdDict('bot-a', 'wxid_abc') == mapped
    assert eventRouter.getMappingIdDict('bot-a', str(mapped)) == 'wxid_abc'


def test_host_ids_preserve_none_compatibility():
    eventRouter.updateHostIdDict('bot-a', None, '100')
    assert eventRouter.getHostIdDict('bot-a', '100') is None

    eventRouter.updateHostIdDict('bot-a', 200, 100)
    assert eventRouter.getHostIdDict('bot-a', '100') == '200'

    eventRouter.updateHostIdDict('bot-a', 'None', 100)
    assert eventRouter.getHostIdDict('bot-a', '100') is None


def test_para_mapper_keeps_para_and_message_modes():
    paras = [
        _Para('text', {'text': 'hello'}),
        _Para('at', {'id': '42'}),
    ]

    assert eventRouter.paraMapper(paras, msgType='para') == [
        {'type': 'text', 'data': {'text': 'hello'}},
        {'type': 'at', 'data': {'qq': '42'}},
    ]
    assert eventRouter.paraMapper(paras, msgType='msg') == 'hello[CQ:at,qq=42]'


def test_para_reverse_mapper_keeps_existing_message_formats():
    message = eventRouter.paraRvMapper([
        {'type': 'at', 'data': {'qq': '42'}},
        {'type': 'text', 'data': {'text': 'hello'}},
    ])
    assert message.mode_rx == 'olivos_para'
    assert message.data[0].type == 'at'
    assert message.data[0].data['id'] == '42'
    assert message.data[0].data['name'] is None
    assert message.data[1].type == 'text'
    assert message.data[1].data == {'text': 'hello'}

    fallback = eventRouter.paraRvMapper('hello')
    assert fallback.mode_rx == 'old_string'
    assert fallback.get('old_string') == 'hello'


def test_rx_event_routes_heartbeat_to_server_and_reverse_link(monkeypatch):
    main.confDict['bot-a'] = {'hash': 'bot-a', 'port': 43000}
    main.r_httpConfDict['bot-a'] = {'hash': 'bot-a', 'path': ['http://127.0.0.1:8080/']}
    websocketServer.clientMapDict['bot-a'] = '43000'
    websocketServer.clientDict['43000'] = [{'obj': _MessageSink()}]
    link_sink = _MessageSink()
    websocketLink.clientDict['bot-a'] = [link_sink]
    http_messages = []
    monkeypatch.setattr(
        httpPost,
        'send',
        lambda bot_hash, message, plugin_event: http_messages.append((bot_hash, message, plugin_event))
    )

    rx_event = eventRouter.rxEvent('heartbeat', _PluginEvent(), _Proc())
    rx_event.doRouter()

    server_sink = websocketServer.clientDict['43000'][0]['obj']
    assert len(server_sink.messages) == 1
    assert len(link_sink.messages) == 1
    message = json.loads(server_sink.messages[0])
    assert message['post_type'] == 'meta_event'
    assert message['meta_event_type'] == 'heartbeat'
    assert message['self_id'] == 42
    assert len(http_messages) == 1
    assert http_messages[0][0] == 'bot-a'
    assert json.loads(http_messages[0][1])['post_type'] == 'meta_event'


def test_unknown_bot_does_not_emit_heartbeat():
    server_sink = _MessageSink()
    websocketServer.clientMapDict['bot-a'] = '43000'
    websocketServer.clientDict['43000'] = [{'obj': server_sink}]

    rx_event = eventRouter.rxEvent('heartbeat', _PluginEvent(), _Proc())
    rx_event.doRouter()

    assert server_sink.messages == []
    assert rx_event.rvMsg is None
