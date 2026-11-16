from types import SimpleNamespace

import pytest

from OlivOSOnebotV11 import eventRouter, main


actionRouter = eventRouter.actionRouter


class _BotInfo(object):
    def __init__(self, bot_hash='bot-a'):
        self.hash = bot_hash


class _Recorder(object):
    def __init__(self, bot_hash='bot-a'):
        self.bot_info = _BotInfo(bot_hash)
        self.calls = []

    def __getattr__(self, name):
        def record(**kwargs):
            self.calls.append((name, kwargs))
            return None
        return record


class _GetterRecorder(object):
    def __init__(self, bot_hash, result):
        self.bot_info = _BotInfo(bot_hash)
        self.result = result

    def __getattr__(self, name):
        def get(**kwargs):
            return self.result
        return get


class _Event(object):
    def __init__(self, plugin_event, params):
        self.plugin_event = plugin_event
        self.params = params
        self.active = True
        self.rvData = object()


def test_send_private_msg_keeps_mapping_and_para_conversion():
    recorder = _Recorder()
    event = _Event(recorder, {'user_id': 'wxid_abc', 'message': 'hello'})

    actionRouter.send_private_msg(event)

    assert recorder.calls == [(
        'send',
        {
            'send_type': 'private',
            'target_id': 'wxid_abc',
            'message': eventRouter.paraRvMapper('hello'),
        }
    )]
    assert event.rvData is None


def test_send_group_msg_keeps_host_mapping():
    recorder = _Recorder()
    eventRouter.updateHostIdDict('bot-a', 200, 100)
    event = _Event(recorder, {'group_id': 100, 'message': 'hello'})

    actionRouter.send_group_msg(event)

    assert recorder.calls == [(
        'send',
        {
            'send_type': 'group',
            'target_id': '100',
            'message': eventRouter.paraRvMapper('hello'),
            'host_id': '200',
        }
    )]
    assert event.rvData is None


@pytest.mark.parametrize(
    'message_type,params,expected_target,expected_host',
    [
        ('private', {'user_id': 42, 'message': 'hello'}, '42', None),
        ('group', {'group_id': 100, 'message': 'hello'}, '100', '200'),
    ]
)
def test_send_msg_keeps_private_and_group_routes(message_type, params, expected_target, expected_host):
    recorder = _Recorder()
    eventRouter.updateHostIdDict('bot-a', 200, 100)
    event = _Event(recorder, dict(params, message_type=message_type))

    actionRouter.send_msg(event)

    assert recorder.calls == [(
        'send',
        {
            'send_type': message_type,
            'target_id': expected_target,
            'message': eventRouter.paraRvMapper('hello'),
            'host_id': expected_host,
        }
    )]
    assert event.rvData is None


def test_delete_msg_is_defined_once_and_invokes_plugin_event():
    recorder = _Recorder()
    event = _Event(recorder, {'message_id': 99})

    actionRouter.delete_msg(event)

    assert recorder.calls == [('delete_msg', {'message_id': 99})]
    assert event.rvData is None


@pytest.mark.parametrize(
    'method,params,expected',
    [
        ('send_like', {'user_id': 42}, {'user_id': '42', 'times': 1}),
        (
            'set_group_kick',
            {'group_id': 100, 'user_id': 42},
            {'group_id': '100', 'user_id': '42', 'reject_add_request': False},
        ),
        (
            'set_group_ban',
            {'group_id': 100, 'user_id': 42},
            {'group_id': '100', 'user_id': '42', 'duration': 1800},
        ),
        ('set_group_whole_ban', {'group_id': 100}, {'group_id': '100'}),
        (
            'set_group_admin',
            {'group_id': 100, 'user_id': 42},
            {'group_id': '100', 'user_id': '42', 'enable': True},
        ),
        (
            'set_group_anonymous',
            {'group_id': 100},
            {'group_id': '100', 'enable': True},
        ),
        (
            'set_group_card',
            {'group_id': 100, 'user_id': 42},
            {'group_id': '100', 'user_id': '42', 'card': ''},
        ),
        (
            'set_group_name',
            {'group_id': 100, 'group_name': 'group'},
            {'group_id': '100', 'group_name': 'group'},
        ),
        (
            'set_group_leave',
            {'group_id': 100},
            {'group_id': '100', 'is_dismiss': False},
        ),
        (
            'set_group_special_title',
            {'group_id': 100, 'user_id': 42},
            {'group_id': '100', 'user_id': '42', 'special_title': '', 'duration': -1},
        ),
        (
            'set_friend_add_request',
            {'flag': 'flag-a'},
            {'flag': 'flag-a', 'approve': True, 'remark': ''},
        ),
        (
            'set_group_add_request',
            {'group_id': 100, 'type': 'add'},
            {'group_id': '100', 'sub_type': 'add', 'approve': True, 'reason': ''},
        ),
    ]
)
def test_void_actions_still_call_plugin_event(method, params, expected):
    recorder = _Recorder()
    event = _Event(recorder, params)

    getattr(actionRouter, method)(event)

    assert recorder.calls == [(method, expected)]
    assert event.rvData is None


def test_get_login_info_keeps_existing_field_mapping():
    recorder = _GetterRecorder('bot-a', {'active': True, 'data': {'id': '42', 'name': 'Alice'}})
    event = _Event(recorder, {})

    actionRouter.get_login_info(event)

    assert event.rvData == {'user_id': 42, 'nickname': 'Alice'}


def test_getter_none_result_keeps_original_fallback():
    recorder = _GetterRecorder('bot-a', None)
    event = _Event(recorder, {})

    actionRouter.get_friend_list(event)

    assert event.rvData == []
    assert event.active is True


def test_getter_inactive_result_deactivates_request():
    recorder = _GetterRecorder('bot-a', {'active': False})
    event = _Event(recorder, {})

    actionRouter.get_version_info(event)

    assert event.active is False


def test_registered_reply_event_is_reused():
    original = _Recorder()
    registered = _Recorder()
    event = _Event(original, {'user_id': 42, 'message': 'hello'})
    main.eventRegDict['bot-a'] = {'private_message/42': registered}

    actionRouter.send_private_msg(event)

    assert original.calls == []
    assert len(registered.calls) == 1


def test_action_event_can_be_built_with_plain_namespace():
    event = SimpleNamespace(params={'group_id': 100}, plugin_event=_Recorder(), active=True, rvData=None)
    actionRouter.set_group_whole_ban(event)
    assert event.plugin_event.calls == [('set_group_whole_ban', {'group_id': '100'})]
