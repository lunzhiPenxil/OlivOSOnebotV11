import pytest

GUI = pytest.importorskip('OlivOSOnebotV11.GUI')


class _StringVar(object):
    def __init__(self, value=''):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_forward_http_ui_loads_and_saves_access_token():
    ui = GUI.ConfigHTTPUI('test')
    ui.routeData['bot-a'] = {
        'hash': 'bot-a',
        'port': 5700,
        'token': 'old-token',
    }
    token_var = _StringVar()
    ui.UIData['root_Entry_ACCESS_TOKEN_StringVar'] = token_var

    ui.load_extra_fields('bot-a')
    assert token_var.get() == 'old-token'

    ui.save_extra_fields('bot-a')
    assert ui.routeData['bot-a']['access_token'] == 'old-token'
    assert 'token' not in ui.routeData['bot-a']

    token_var.set('new-token')
    ui.save_extra_fields('bot-a')
    assert ui.routeData['bot-a']['access_token'] == 'new-token'

    token_var.set('')
    ui.save_extra_fields('bot-a')
    assert 'access_token' not in ui.routeData['bot-a']


def test_reverse_http_ui_loads_and_saves_secret_and_timeout():
    ui = GUI.ConfigRHTTPUI('test')
    ui.routeData['bot-a'] = {
        'hash': 'bot-a',
        'path': ['http://127.0.0.1:8080/'],
        'secret': 'secret-a',
        'timeout': 2,
    }
    secret_var = _StringVar()
    timeout_var = _StringVar()
    ui.UIData['root_Entry_SECRET_StringVar'] = secret_var
    ui.UIData['root_Entry_TIMEOUT_StringVar'] = timeout_var

    ui.load_extra_fields('bot-a')
    assert secret_var.get() == 'secret-a'
    assert timeout_var.get() == '2'

    secret_var.set('')
    timeout_var.set('2.5')
    ui.save_extra_fields('bot-a')
    assert 'secret' not in ui.routeData['bot-a']
    assert ui.routeData['bot-a']['timeout'] == 2.5

    timeout_var.set('invalid')
    ui.save_extra_fields('bot-a')
    assert ui.routeData['bot-a']['timeout'] == 2.5

    timeout_var.set('')
    ui.save_extra_fields('bot-a')
    assert 'timeout' not in ui.routeData['bot-a']


def test_websocket_ui_layout_stays_unchanged():
    assert GUI.ConfigUI.tree_y == 64
    assert GUI.ConfigUI.tree_height == 321
    assert GUI.ConfigRUI.content_y == 64
    assert GUI.ConfigRUI.content_height == 321
