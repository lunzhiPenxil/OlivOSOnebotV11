# -*- encoding: utf-8 -*-
'''
@File      :   eventRouter.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2022, lunzhiPenxil仑质
@Desc      :   None
'''

import json
import traceback
import os

import OlivOS
import OlivOSOnebotV11

def releaseDir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def initBotInfo():
    res = None
    releaseDir('./plugin')
    releaseDir('./plugin/data')
    releaseDir('./plugin/data/OlivOSOnebotV11')
    path = './plugin/data/OlivOSOnebotV11/config.json'
    try:
        conf_obj = None
        with open(path, 'r', encoding = 'utf-8') as conf_f:
            conf_obj = json.loads(conf_f.read())
        res = {}
        for route_this in conf_obj['route']:
            if 'port' in route_this:
                if 'hash' in route_this:
                    res[route_this['hash']] = {
                        'hash': route_this['hash'],
                        'port': route_this['port']
                    }
    except:
        res = None
    return res

class rxEvent(object):
    def __init__(self, funcType, plugin_event, Proc):
        self.funcType = funcType
        self.plugin_event = plugin_event
        self.Proc = Proc
        self.rvData = None
        self.rvMsg = None

    def doRouter(self):
        try:
            if self.plugin_event.bot_info.hash in OlivOSOnebotV11.main.confDict:
                if hasattr(eventRouter, self.funcType):
                    getattr(eventRouter, self.funcType)(self)
            if self.rvData != None:
                tmp_rvMsg = self.rvData
                self.rvMsg = json.dumps(tmp_rvMsg)
            if self.rvMsg != None:
                if self.plugin_event.bot_info.hash in OlivOSOnebotV11.websocketServer.clientMapDict:
                    if OlivOSOnebotV11.websocketServer.clientMapDict[self.plugin_event.bot_info.hash] in OlivOSOnebotV11.websocketServer.clientDict:
                        for client in OlivOSOnebotV11.websocketServer.clientDict[OlivOSOnebotV11.websocketServer.clientMapDict[self.plugin_event.bot_info.hash]]:
                            client['obj'].sendMessage(self.rvMsg)
        except Exception as e:
            skip_result = '%s\n%s' % (
                str(e),
                traceback.format_exc()
            )
            self.Proc.log(3, skip_result, [
                ('OlivOSOnebotV11', 'default')
            ])

def paraMapper(paraList):
    res = []
    for para in paraList:
        tmp_para = para.__dict__
        if para.type == 'at':
            tmp_para = {}
            tmp_para['type'] = 'at'
            tmp_para['data'] = {}
            tmp_para['data']['qq'] = para.data['id']
        res.append(tmp_para)
    return res

def paraRvMapper(paraList):
    res = None
    res_list = []
    for para in paraList:
        tmp_para = para
        tmp_para_this = None
        if para['type'] == 'at':
            tmp_para = {}
            tmp_para['type'] = 'at'
            tmp_para['data'] = {}
            tmp_para['data']['id'] = para['data']['qq']
        if hasattr(OlivOS.messageAPI.PARA, tmp_para['type']):
            tmp_para_this = getattr(OlivOS.messageAPI.PARA, tmp_para['type'])(**tmp_para['data'])
        res_list.append(tmp_para_this)
    res = OlivOS.messageAPI.Message_templet(
        'olivos_para',
        res_list
    )
    return res

class eventRouter(object):
    def group_message(eventObj):
        eventObj.rvData = {}
        eventObj.rvData['time'] = eventObj.plugin_event.base_info['time']
        eventObj.rvData['self_id'] = int(eventObj.plugin_event.base_info['self_id'])
        eventObj.rvData['post_type'] = 'message'
        eventObj.rvData['message_type'] = 'group'
        eventObj.rvData['sub_type'] = 'normal'
        eventObj.rvData['message_id'] = eventObj.plugin_event.data.message_id
        eventObj.rvData['user_id'] = int(eventObj.plugin_event.data.user_id)
        eventObj.rvData['group_id'] = int(eventObj.plugin_event.data.group_id)
        eventObj.rvData['message'] = paraMapper(eventObj.plugin_event.data.message.data)
        eventObj.rvData['raw_message'] = paraMapper(eventObj.plugin_event.data.raw_message.data)
        eventObj.rvData['anonymous'] = None
        eventObj.rvData['font'] = eventObj.plugin_event.data.font
        eventObj.rvData['sender'] = {}
        eventObj.rvData['sender']['user_id'] = eventObj.plugin_event.data.sender['id']
        eventObj.rvData['sender']['nickname'] = eventObj.plugin_event.data.sender['name']

    def private_message(eventObj):
        eventObj.rvData = {}
        eventObj.rvData['time'] = eventObj.plugin_event.base_info['time']
        eventObj.rvData['self_id'] = int(eventObj.plugin_event.base_info['self_id'])
        eventObj.rvData['post_type'] = 'message'
        eventObj.rvData['message_type'] = 'private'
        eventObj.rvData['sub_type'] = eventObj.plugin_event.data.sub_type
        eventObj.rvData['message_id'] = eventObj.plugin_event.data.message_id
        eventObj.rvData['user_id'] = int(eventObj.plugin_event.data.user_id)
        eventObj.rvData['message'] = paraMapper(eventObj.plugin_event.data.message.data)
        eventObj.rvData['raw_message'] = paraMapper(eventObj.plugin_event.data.raw_message.data)
        eventObj.rvData['font'] = eventObj.plugin_event.data.font
        eventObj.rvData['sender'] = {}
        eventObj.rvData['sender']['user_id'] = eventObj.plugin_event.data.sender['id']
        eventObj.rvData['sender']['nickname'] = eventObj.plugin_event.data.sender['name']

class txEvent(object):
    def __init__(self, ws):
        self.active = True
        self.ws = ws
        self.raw = ws.data
        self.json = None
        self.funcType = None
        self.echo = None
        self.params = None
        self.plugin_event = None
        self.Proc = OlivOSOnebotV11.main.ProcObj
        self.rvData = None
        self.rvMsg = None
        self.doInit()

    def doInit(self):
        try:
            self.json = json.loads(self.raw)
            self.funcType = self.json['action']
            self.echo = self.json['echo']
            if 'params' in self.json:
                self.params = self.json['params']
        except:
            self.active = False
        if self.active:
            self.Proc.log(1, 'websocket receive action [%s]' % self.funcType, [
                ('OlivOSOnebotV11', 'default')
            ])
            botInfoDict_key = None
            if str(list(self.ws.server.serversocket.getsockname())[1]) in OlivOSOnebotV11.websocketServer.clientDict:
                if len(OlivOSOnebotV11.websocketServer.clientDict[str(list(self.ws.server.serversocket.getsockname())[1])]) >= 1:
                    botInfoDict_key = OlivOSOnebotV11.websocketServer.clientDict[str(list(self.ws.server.serversocket.getsockname())[1])][0]['info']['hash']
            if botInfoDict_key == None:
                if len(list(OlivOSOnebotV11.main.confDict)) >= 1:
                    botInfoDict_key = list(OlivOSOnebotV11.main.confDict)[0]
                    pass
            if botInfoDict_key != None:
                self.plugin_event = OlivOS.API.Event(
                    OlivOS.contentAPI.fake_sdk_event(
                        bot_info = OlivOSOnebotV11.main.botInfoDict[botInfoDict_key],
                        fakename = OlivOSOnebotV11.main.pluginName
                    ),
                    self.Proc.log
                )

    def doRouter(self):
        #print(self.json)
        try:
            if self.active:
                if hasattr(actionRouter, self.funcType):
                    getattr(actionRouter, self.funcType)(self)
                    if self.active:
                        resData = {}
                        resData['echo'] = self.echo
                        resData['status'] = 'ok'
                        resData['retcode'] = 0
                        if self.rvData != None:
                            resData['data'] = self.rvData
                        self.rvMsg = json.dumps(resData)
            if self.rvMsg != None:
                self.ws.sendMessage(self.rvMsg)
        except Exception as e:
            skip_result = '%s\n%s' % (
                str(e),
                traceback.format_exc()
            )
            self.Proc.log(3, skip_result, [
                ('OlivOSOnebotV11', 'default')
            ])

class actionRouter(object):
    def get_msg(eventObj):
        res = eventObj.plugin_event.get_msg()
        if res == None:
            eventObj.rvData = {}
        elif res['active']:
            eventObj.rvData = {}
            eventObj.rvData['message_id'] = res['data']['message_id']
            eventObj.rvData['real_id'] = res['data']['id']
            eventObj.rvData['sender'] = {}
            eventObj.rvData['sender']['user_id'] = int(res['data']['sender']['id'])
            eventObj.rvData['sender']['nickname'] = res['data']['sender']['name']
            eventObj.rvData['time'] = res['data']['time']
            eventObj.rvData['message'] = res['data']['message']
            eventObj.rvData['raw_message'] = res['data']['raw_message']
        else:
            eventObj.active = False

    def get_login_info(eventObj):
        res = eventObj.plugin_event.get_login_info()
        if res == None:
            eventObj.active = False
        elif res['active']:
            eventObj.rvData = {}
            eventObj.rvData['user_id'] = int(res['data']['id'])
            eventObj.rvData['nickname'] = res['data']['name']
        else:
            eventObj.active = False

    def get_group_list(eventObj):
        res = eventObj.plugin_event.get_group_list()
        if res == None:
            eventObj.rvData = []
        elif res['active']:
            eventObj.rvData = []
            for data_this in res['data']:
                tmp_data_this = {}
                tmp_data_this['group_id'] = int(data_this['id'])
                tmp_data_this['group_name'] = data_this['name']
                tmp_data_this['group_memo'] = data_this['memo']
                tmp_data_this['member_count'] = data_this['member_count']
                tmp_data_this['max_member_count'] = data_this['max_member_count']
                eventObj.rvData.append(tmp_data_this)
        else:
            eventObj.active = False

    def get_group_info(eventObj):
        res = eventObj.plugin_event.get_group_info(
            group_id = str(eventObj.params['group_id'])
        )
        if res == None:
            eventObj.rvData = {}
        elif res['active']:
            eventObj.rvData = {}
            eventObj.rvData['group_id'] = int(res['data']['id'])
            eventObj.rvData['group_name'] = res['data']['name']
            eventObj.rvData['group_memo'] = res['data']['memo']
            eventObj.rvData['member_count'] = res['data']['member_count']
            eventObj.rvData['max_member_count'] = res['data']['max_member_count']
        else:
            eventObj.active = False

    def get_stranger_info(eventObj):
        res = eventObj.plugin_event.get_stranger_info(
            user_id = str(eventObj.params['user_id'])
        )
        if res == None:
            eventObj.rvData = {}
        elif res['active']:
            eventObj.rvData = {}
            eventObj.rvData['user_id'] = int(res['data']['id'])
            eventObj.rvData['nickname'] = res['data']['name']
        else:
            eventObj.active = False

    def get_friend_list(eventObj):
        res = eventObj.plugin_event.get_friend_list()
        if res == None:
            eventObj.rvData = []
        elif res['active']:
            eventObj.rvData = []
            for data_this in res['data']:
                tmp_data_this = {}
                tmp_data_this['user_id'] = int(data_this['id'])
                tmp_data_this['nickname'] = data_this['name']
                eventObj.rvData.append(tmp_data_this)
        else:
            eventObj.active = False

    def get_group_member_info(eventObj):
        res = eventObj.plugin_event.get_group_member_info(
            group_id = str(eventObj.params['group_id']),
            user_id = str(eventObj.params['user_id'])
        )
        if res == None:
            eventObj.rvData = {}
        elif res['active']:
            eventObj.rvData = {}
            eventObj.rvData['group_id'] = res['data']['group_id']
            eventObj.rvData['user_id'] = int(res['data']['id'])
            eventObj.rvData['join_time'] = res['data']['times']['join_time']
            eventObj.rvData['last_sent_time'] = res['data']['times']['last_sent_time']
            eventObj.rvData['shut_up_timestamp'] = res['data']['times']['shut_up_timestamp']
            eventObj.rvData['role'] = res['data']['role']
            eventObj.rvData['card'] = res['data']['card']
            eventObj.rvData['title'] = res['data']['title']
        else:
            eventObj.active = False

    def get_group_member_list(eventObj):
        res = eventObj.plugin_event.get_group_member_list(
            group_id = str(eventObj.params['group_id'])
        )
        if res == None:
            eventObj.rvData = []
        elif res['active']:
            eventObj.rvData = []
            for data_this in res['data']:
                tmp_data_this = {}
                tmp_data_this['group_id'] = data_this['group_id']
                tmp_data_this['user_id'] = int(data_this['id'])
                tmp_data_this['join_time'] = data_this['times']['join_time']
                tmp_data_this['last_sent_time'] = data_this['times']['last_sent_time']
                tmp_data_this['shut_up_timestamp'] = data_this['times']['shut_up_timestamp']
                tmp_data_this['role'] = data_this['role']
                tmp_data_this['card'] = data_this['card']
                tmp_data_this['title'] = data_this['title']
                eventObj.rvData.append(tmp_data_this)
        else:
            eventObj.active = False

    def can_send_image(eventObj):
        res = eventObj.plugin_event.can_send_image()
        if res == None:
            eventObj.rvData = {}
            eventObj.rvData['yes'] = False
        elif res['active']:
            eventObj.rvData = {}
            eventObj.rvData['yes'] = res['data']['yes']
        else:
            eventObj.active = False

    def can_send_record(eventObj):
        res = eventObj.plugin_event.can_send_record()
        if res == None:
            eventObj.rvData = {}
            eventObj.rvData['yes'] = False
        elif res['active']:
            eventObj.rvData = {}
            eventObj.rvData['yes'] = res['data']['yes']
        else:
            eventObj.active = False

    def get_status(eventObj):
        res = eventObj.plugin_event.get_status()
        if res == None:
            eventObj.active = False
        elif res['active']:
            eventObj.rvData = {}
            eventObj.rvData['online'] = res['data']['online']
            eventObj.rvData['stat'] = {}
            eventObj.rvData['stat'] = res['data']['status']['packet_received']
            eventObj.rvData['stat'] = res['data']['status']['packet_sent']
            eventObj.rvData['stat'] = res['data']['status']['packet_lost']
            eventObj.rvData['stat'] = res['data']['status']['message_received']
            eventObj.rvData['stat'] = res['data']['status']['message_sent']
            eventObj.rvData['stat'] = res['data']['status']['disconnect_times']
            eventObj.rvData['stat'] = res['data']['status']['lost_times']
            eventObj.rvData['stat'] = res['data']['status']['last_message_time']
        else:
            eventObj.active = False

    def get_version_info(eventObj):
        res = eventObj.plugin_event.get_version_info()
        if res == None:
            eventObj.active = False
        elif res['active']:
            eventObj.rvData = {}
            eventObj.rvData['app_name'] = res['data']['name']
            eventObj.rvData['app_full_name'] = res['data']['version_full']
            eventObj.rvData['app_version'] = res['data']['version']
            eventObj.rvData['coolq_directory'] = res['data']['path']
            eventObj.rvData['runtime_os'] = res['data']['os']
        else:
            eventObj.active = False

    def send_private_msg(eventObj):
        res = eventObj.plugin_event.send(
            send_type = 'private',
            target_id = str(eventObj.params['user_id']),
            message = paraRvMapper(
                eventObj.params['message']
            )
        )
        eventObj.rvData = None

    def send_group_msg(eventObj):
        res = eventObj.plugin_event.send(
            send_type = 'group',
            target_id = str(eventObj.params['group_id']),
            message = paraRvMapper(
                eventObj.params['message']
            )
        )
        eventObj.rvData = None

    def send_msg(eventObj):
        res = eventObj.plugin_event.send(
            send_type = eventObj.params['message_type'],
            target_id = str(eventObj.params['group_id']),
            message = paraRvMapper(
                eventObj.params['message']
            )
        )
        eventObj.rvData = None

    def delete_msg(eventObj):
        res = eventObj.plugin_event.delete_msg(
            message_id = eventObj.params['message_id']
        )
        eventObj.rvData = None

    def delete_msg(eventObj):
        res = eventObj.plugin_event.delete_msg(
            message_id = eventObj.params['message_id']
        )
        eventObj.rvData = None

    def send_like(eventObj):
        tmp_val = {
            'user_id': str(eventObj.params['user_id']),
            'times': 1
        }
        if 'times' in eventObj.params:
            tmp_val['times'] = eventObj.params['times']
        res = eventObj.plugin_event.send_like(**tmp_val)
        eventObj.rvData = None

    def set_group_kick(eventObj):
        tmp_val = {
            'group_id': str(eventObj.params['group_id']),
            'user_id': str(eventObj.params['user_id']),
            'reject_add_request': False
        }
        if 'reject_add_request' in eventObj.params:
            tmp_val['reject_add_request'] = eventObj.params['reject_add_request']
        res = eventObj.plugin_event.set_group_kick(**tmp_val)
        eventObj.rvData = None

    def set_group_ban(eventObj):
        tmp_val = {
            'group_id': str(eventObj.params['group_id']),
            'user_id': str(eventObj.params['user_id']),
            'duration': 30 * 60
        }
        if 'duration' in eventObj.params:
            tmp_val['duration'] = eventObj.params['duration']
        res = eventObj.plugin_event.set_group_ban(**tmp_val)
        eventObj.rvData = None

    def set_group_whole_ban(eventObj):
        tmp_val = {
            'group_id': str(eventObj.params['group_id'])
        }
        res = eventObj.plugin_event.set_group_whole_ban(**tmp_val)
        eventObj.rvData = None

    def set_group_admin(eventObj):
        tmp_val = {
            'group_id': str(eventObj.params['group_id']),
            'user_id': str(eventObj.params['user_id']),
            'enable': True
        }
        if 'enable' in eventObj.params:
            tmp_val['enable'] = eventObj.params['enable']
        res = eventObj.plugin_event.set_group_admin(**tmp_val)
        eventObj.rvData = None

    def set_group_anonymous(eventObj):
        tmp_val = {
            'group_id': str(eventObj.params['group_id']),
            'enable': True
        }
        if 'enable' in eventObj.params:
            tmp_val['enable'] = eventObj.params['enable']
        res = eventObj.plugin_event.set_group_anonymous(**tmp_val)
        eventObj.rvData = None

    def set_group_card(eventObj):
        tmp_val = {
            'group_id': str(eventObj.params['group_id']),
            'user_id': str(eventObj.params['user_id']),
            'card': ''
        }
        if 'card' in eventObj.params:
            tmp_val['card'] = eventObj.params['card']
        res = eventObj.plugin_event.set_group_card(**tmp_val)
        eventObj.rvData = None

    def set_group_name(eventObj):
        tmp_val = {
            'group_id': str(eventObj.params['group_id']),
            'group_name': eventObj.params['group_name']
        }
        res = eventObj.plugin_event.set_group_name(**tmp_val)
        eventObj.rvData = None

    def set_group_leave(eventObj):
        tmp_val = {
            'group_id': str(eventObj.params['group_id']),
            'is_dismiss': False
        }
        if 'is_dismiss' in eventObj.params:
            tmp_val['is_dismiss'] = eventObj.params['is_dismiss']
        res = eventObj.plugin_event.set_group_leave(**tmp_val)
        eventObj.rvData = None

    def set_group_special_title(eventObj):
        tmp_val = {
            'group_id': str(eventObj.params['group_id']),
            'user_id': str(eventObj.params['user_id']),
            'special_title': '',
            'duration': -1
        }
        if 'special_title' in eventObj.params:
            tmp_val['special_title'] = eventObj.params['special_title']
        if 'duration' in eventObj.params:
            tmp_val['duration'] = eventObj.params['duration']
        res = eventObj.plugin_event.set_group_special_title(**tmp_val)
        eventObj.rvData = None

    def set_friend_add_request(eventObj):
        tmp_val = {
            'flag': str(eventObj.params['flag']),
            'approve': True,
            'remark': ''
        }
        if 'approve' in eventObj.params:
            tmp_val['approve'] = eventObj.params['approve']
        if 'remark' in eventObj.params:
            tmp_val['remark'] = eventObj.params['remark']
        res = eventObj.plugin_event.set_friend_add_request(**tmp_val)
        eventObj.rvData = None

    def set_group_add_request(eventObj):
        tmp_val = {
            'group_id': str(eventObj.params['group_id']),
            'sub_type': None,
            'approve': True,
            'reason': ''
        }
        if 'sub_type' in eventObj.params:
            tmp_val['sub_type'] = eventObj.params['sub_type']
        if 'type' in eventObj.params:
            tmp_val['sub_type'] = eventObj.params['type']
        if 'approve' in eventObj.params:
            tmp_val['approve'] = eventObj.params['approve']
        if 'reason' in eventObj.params:
            tmp_val['reason'] = eventObj.params['reason']
        res = eventObj.plugin_event.set_group_add_request(**tmp_val)
        eventObj.rvData = None
