from types import SimpleNamespace

from OlivOSOnebotV11 import eventRouter, main, websocketLink, websocketServer


def test_init_after_updates_module_globals(monkeypatch):
    bot_info = object()
    proc = SimpleNamespace(Proc_data={'bot_info_dict': {'bot-a': bot_info}})
    route = {'bot-a': {'hash': 'bot-a', 'port': 43000}}
    reverse_route = {'bot-a': {'hash': 'bot-a', 'path': []}}
    started = []
    saved = []

    monkeypatch.setattr(
        eventRouter,
        'initBotInfo',
        lambda bot_info_dict, default_port: (route, reverse_route)
    )
    monkeypatch.setattr(websocketServer, 'start_websocket', lambda value: started.append(('server', value)))
    monkeypatch.setattr(websocketLink, 'start_websocket', lambda value: started.append(('link', value)))
    monkeypatch.setattr(eventRouter, 'saveBotInfo', lambda data, reverse: saved.append((data, reverse)))

    main.Event.init_after(None, proc)

    assert main.ProcObj is proc
    assert main.botInfoDict == {'bot-a': bot_info}
    assert main.confDict is route
    assert main.r_confDict is reverse_route
    assert started == [('server', route), ('link', reverse_route)]
    assert saved == [(route, reverse_route)]


def test_save_uses_module_level_route_data(monkeypatch):
    route = {'bot-a': {'hash': 'bot-a', 'port': 43000}}
    reverse_route = {'bot-a': {'hash': 'bot-a', 'path': []}}
    saved = []
    main.confDict = route
    main.r_confDict = reverse_route
    monkeypatch.setattr(eventRouter, 'saveBotInfo', lambda data, reverse: saved.append((data, reverse)))

    main.Event.save(None, None)

    assert saved == [(route, reverse_route)]
