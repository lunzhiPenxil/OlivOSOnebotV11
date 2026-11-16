from types import SimpleNamespace

from OlivOSOnebotV11 import eventRouter, httpPost, httpServer, main, websocketLink, websocketServer


def test_init_after_updates_module_globals(monkeypatch):
    bot_info = object()
    proc = SimpleNamespace(Proc_data={'bot_info_dict': {'bot-a': bot_info}})
    route = {'bot-a': {'hash': 'bot-a', 'port': 43000}}
    reverse_route = {'bot-a': {'hash': 'bot-a', 'path': []}}
    http_route = {'bot-a': {'hash': 'bot-a', 'port': None}}
    reverse_http_route = {'bot-a': {'hash': 'bot-a', 'path': []}}
    started = []
    saved = []

    monkeypatch.setattr(
        eventRouter,
        'initBotInfo',
        lambda bot_info_dict, default_port: (route, reverse_route)
    )
    monkeypatch.setattr(
        eventRouter,
        'initHttpBotInfo',
        lambda bot_info_dict: (http_route, reverse_http_route)
    )
    monkeypatch.setattr(websocketServer, 'start_websocket', lambda value: started.append(('server', value)))
    monkeypatch.setattr(websocketLink, 'start_websocket', lambda value: started.append(('link', value)))
    monkeypatch.setattr(httpServer, 'start_http', lambda value: started.append(('http', value)))
    monkeypatch.setattr(httpPost, 'start_http_post', lambda value: started.append(('http-post', value)))
    monkeypatch.setattr(
        eventRouter,
        'saveBotInfo',
        lambda data, reverse, http_data, reverse_http_data: saved.append(
            (data, reverse, http_data, reverse_http_data)
        )
    )

    main.Event.init_after(None, proc)

    assert main.ProcObj is proc
    assert main.botInfoDict == {'bot-a': bot_info}
    assert main.confDict is route
    assert main.r_confDict is reverse_route
    assert main.httpConfDict is http_route
    assert main.r_httpConfDict is reverse_http_route
    assert started == [
        ('server', route),
        ('link', reverse_route),
        ('http', http_route),
        ('http-post', reverse_http_route),
    ]
    assert saved == [(route, reverse_route, http_route, reverse_http_route)]


def test_save_uses_module_level_route_data(monkeypatch):
    route = {'bot-a': {'hash': 'bot-a', 'port': 43000}}
    reverse_route = {'bot-a': {'hash': 'bot-a', 'path': []}}
    http_route = {'bot-a': {'hash': 'bot-a', 'port': None}}
    reverse_http_route = {'bot-a': {'hash': 'bot-a', 'path': []}}
    saved = []
    main.confDict = route
    main.r_confDict = reverse_route
    main.httpConfDict = http_route
    main.r_httpConfDict = reverse_http_route
    monkeypatch.setattr(
        eventRouter,
        'saveBotInfo',
        lambda data, reverse, http_data, reverse_http_data: saved.append(
            (data, reverse, http_data, reverse_http_data)
        )
    )

    main.Event.save(None, None)

    assert saved == [(route, reverse_route, http_route, reverse_http_route)]
