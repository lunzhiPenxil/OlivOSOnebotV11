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
import time
import hashlib

import OlivOS
import OlivOSOnebotV11

def releaseDir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def initBotInfo(bot_info:dict, default_port = 55009):
    tmp_default_port = default_port
    releaseDir('./plugin')
    releaseDir('./plugin/data')
    releaseDir('./plugin/data/OlivOSOnebotV11')
    path = './plugin/data/OlivOSOnebotV11/config.json'

    conf_obj = None
    try:
        conf_obj = None
        with open(path, 'r', encoding = 'utf-8') as conf_f:
            conf_obj = json.loads(conf_f.read())
    except:
        conf_obj = None
    if type(conf_obj) is not dict:
        conf_obj = {}
    conf_obj.setdefault('route', [])
    conf_obj.setdefault('r-route', [])

    # route
    res_1 = None
    try:
        res_1 = {}
        for route_this in conf_obj['route']:
            if 'port' in route_this \
            and 'hash' in route_this:
                res_1[route_this['hash']] = {
                    'hash': route_this['hash'],
                    'port': route_this['port']
                }
    except:
        res_1 = None
    if res_1 is None:
        res_1 = {}
    for bot_info_hash in bot_info:
        if bot_info_hash not in res_1:
            res_1[bot_info_hash] = {
                'hash': bot_info_hash,
                'port': tmp_default_port
            }
    res_new = {}
    for bot_info_hash in res_1:
        if bot_info_hash in bot_info:
            res_new[bot_info_hash] = res_1[bot_info_hash]
    res_1 = res_new

    # r-route
    res_2 = None
    try:
        res_2 = {}
        for route_this in conf_obj['r-route']:
            if 'path' in route_this \
            and 'hash' in route_this:
                res_2[route_this['hash']] = {
                    'hash': route_this['hash'],
                    'path': route_this['path']
                }
    except:
        res_2 = None
    if res_2 is None:
        res_2 = {}
    for bot_info_hash in bot_info:
        if bot_info_hash not in res_2 \
        or (bot_info_hash in res_2 \
        and 'path' in res_2[bot_info_hash] \
        and type(res_2[bot_info_hash]['path']) is not list):
            res_2[bot_info_hash] = {
                'hash': bot_info_hash,
                'path': []
            }
    res_new = {}
    for bot_info_hash in res_2:
        if bot_info_hash in bot_info:
            res_new[bot_info_hash] = res_2[bot_info_hash]
    res_2 = res_new

    for bot_info_hash in bot_info:
        OlivOSOnebotV11.main.eventRegDict.setdefault(bot_info_hash, {})

    return res_1, res_2

def saveBotInfo(data, r_data):
    releaseDir('./plugin')
    releaseDir('./plugin/data')
    releaseDir('./plugin/data/OlivOSOnebotV11')
    path = './plugin/data/OlivOSOnebotV11/config.json'
    try:
        res = {
            'route': [],
            'r-route': []
        }
        for route_this in data:
            res['route'].append(data[route_this])
        for r_route_this in r_data:
            res['r-route'].append(r_data[r_route_this])
        with open(path, 'w', encoding = 'utf-8') as conf_f:
            conf_f.write(
                json.dumps(
                    obj = res,
                    ensure_ascii = False,
                    indent = 4
                )
            )
    except:
        pass

def fakeHeartbeatGen():
    while True:
        for botHash in OlivOSOnebotV11.main.confDict:
            if botHash in OlivOSOnebotV11.main.ProcObj.Proc_data['bot_info_dict']:
                if botHash in OlivOSOnebotV11.main.ProcObj.Proc_data['bot_info_dict']:
                    fake_plugin_event = OlivOS.API.Event(
                        OlivOS.contentAPI.fake_sdk_event(
                            bot_info = OlivOSOnebotV11.main.ProcObj.Proc_data['bot_info_dict'][botHash],
                            fakename = OlivOSOnebotV11.main.pluginName
                        ),
                        OlivOSOnebotV11.main.ProcObj.log
                    )
                rxEvent = OlivOSOnebotV11.eventRouter.rxEvent(
                    'heartbeat',
                    fake_plugin_event,
                    OlivOSOnebotV11.main.ProcObj
                )
                rxEvent.doRouter()
        time.sleep(5)

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
                    getattr(eventRouter, self.funcType)(self, msgType='msg')
            if self.rvData != None:
                tmp_rvMsg = self.rvData
                self.rvMsg = json.dumps(tmp_rvMsg)
        except Exception as e:
            skip_result = '%s\n%s' % (
                str(e),
                traceback.format_exc()
            )
            self.Proc.log(3, skip_result, [
                ('OlivOSOnebotV11', 'default')
            ])
        try:
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

        try:
            if self.plugin_event.bot_info.hash in OlivOSOnebotV11.main.confDict:
                if hasattr(eventRouter, self.funcType):
                    getattr(eventRouter, self.funcType)(self, msgType='msg')
            if self.rvData != None:
                tmp_rvMsg = self.rvData
                self.rvMsg = json.dumps(tmp_rvMsg)
        except Exception as e:
            skip_result = '%s\n%s' % (
                str(e),
                traceback.format_exc()
            )
            self.Proc.log(3, skip_result, [
                ('OlivOSOnebotV11', 'default')
            ])
        try:
            if self.rvMsg != None:
                if self.plugin_event.bot_info.hash in OlivOSOnebotV11.websocketLink.clientDict:
                    for client in OlivOSOnebotV11.websocketLink.clientDict[self.plugin_event.bot_info.hash]:
                        client.send(self.rvMsg)
        except Exception as e:
            skip_result = '%s\n%s' % (
                str(e),
                traceback.format_exc()
            )
            self.Proc.log(3, skip_result, [
                ('OlivOSOnebotV11', 'default')
            ])

def paraMapper(paraList, msgType='para'):
    res = []
    if 'para' == msgType:
        for para in paraList:
            tmp_para = para.__dict__
            if para.type == 'at':
                tmp_para = {}
                tmp_para['type'] = 'at'
                tmp_para['data'] = {}
                tmp_para['data']['qq'] = para.data['id']
            res.append(tmp_para)
    elif 'msg' == msgType:
        res = ''
        for para in paraList:
            res += para.CQ()
    return res

def paraRvMapper(paraList):
    res = None
    res_list = []
    if type(paraList) is list:
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
    else:
        res = OlivOS.messageAPI.Message_templet(
            'old_string',
            str(paraList)
        )
    return res

def updateHostIdDict(botHash, hostId, groupId):
    if hostId != None:
        if botHash not in OlivOSOnebotV11.main.hostIdDict:
            OlivOSOnebotV11.main.hostIdDict[botHash] = {}
        OlivOSOnebotV11.main.hostIdDict[botHash][str(groupId)] = str(hostId)

def getHostIdDict(botHash, groupId):
    res = None
    if botHash in OlivOSOnebotV11.main.hostIdDict:
        if str(groupId) in OlivOSOnebotV11.main.hostIdDict[botHash]:
            res = OlivOSOnebotV11.main.hostIdDict[botHash][str(groupId)]
    if res == 'None':
        res = None
    return res

def setMappingIdDict(botHash:str, id):
    try:
        targetId = int(id)
    except:
        targetId = None
    if targetId is None:
        targetId_hash = hashlib.new('md5')
        targetId_hash.update(str(id).encode(encoding='UTF-8'))
        targetId = int(int(targetId_hash.hexdigest(), 16) % 1000000000)
    OlivOSOnebotV11.main.mappingIdDict.setdefault(botHash, {})
    if str(targetId) != str(id):
        OlivOSOnebotV11.main.mappingIdDict[botHash][str(targetId)] = id
    return targetId

def getMappingIdDict(botHash:str, id):
    res = OlivOSOnebotV11.main.mappingIdDict.get(botHash, {}).get(str(id), id)
    if res == 'None':
        res = None
    return res

def updateEventRegDict(botHash:str, key:str, event):
    OlivOSOnebotV11.main.eventRegDict.setdefault(botHash, {})
    OlivOSOnebotV11.main.eventRegDict[botHash][key] = event

def getEventRegDict(botHash:str, key:str):
    res = OlivOSOnebotV11.main.eventRegDict.get(botHash, {}).get(key, None)
    return res

class eventRouter(object):
    def heartbeat(eventObj:rxEvent, **kwargs):
        botHash = eventObj.plugin_event.bot_info.hash
        eventObj.rvData = {}
        eventObj.rvData['post_type'] = 'meta_event'
        eventObj.rvData['meta_event_type'] = 'heartbeat'
        eventObj.rvData['time'] = backport_int(time.time())
        eventObj.rvData['self_id'] = setMappingIdDict(botHash, backport_int(eventObj.plugin_event.base_info['self_id']))
        eventObj.rvData['status'] = {}
        eventObj.rvData['status']['enable'] = True
        eventObj.rvData['status']['interval'] = 5000
        eventObj.rvData['interval'] = 5000

    def group_message(eventObj:rxEvent, **kwargs):
        botHash = eventObj.plugin_event.bot_info.hash
        eventObj.rvData = {}
        eventObj.rvData['time'] = eventObj.plugin_event.base_info['time']
        eventObj.rvData['self_id'] = setMappingIdDict(botHash, backport_int(eventObj.plugin_event.base_info['self_id']))
        eventObj.rvData['post_type'] = 'message'
        eventObj.rvData['message_type'] = 'group'
        eventObj.rvData['sub_type'] = 'normal'
        eventObj.rvData['message_id'] = setMappingIdDict(botHash, backport_int(eventObj.plugin_event.data.message_id))
        eventObj.rvData['user_id'] = setMappingIdDict(botHash, backport_int(eventObj.plugin_event.data.user_id))
        eventObj.rvData['group_id'] = setMappingIdDict(botHash, backport_int(eventObj.plugin_event.data.group_id))
        eventObj.rvData['message'] = paraMapper(eventObj.plugin_event.data.message.data, msgType=kwargs.get('msgType', 'para'))
        eventObj.rvData['raw_message'] = eventObj.rvData['message']
        eventObj.rvData['anonymous'] = None
        eventObj.rvData['font'] = 1
        eventObj.rvData['sender'] = {}
        eventObj.rvData['sender']['user_id'] = eventObj.rvData['user_id']
        eventObj.rvData['sender']['nickname'] = eventObj.plugin_event.data.sender['name']
        eventObj.rvData['sender']['role'] = 'owner'
        if 'role' in eventObj.plugin_event.data.sender:
            eventObj.rvData['sender']['role'] = eventObj.plugin_event.data.sender['role']
        eventObj.rvData['sender']['sex'] = 'unknown'
        eventObj.rvData['sender']['age'] = 0
        updateHostIdDict(
            botHash = botHash,
            hostId = str(eventObj.plugin_event.data.host_id),
            groupId = str(eventObj.plugin_event.data.group_id)
        )
        updateEventRegDict(
            botHash = botHash,
            key = f'group_message/{eventObj.rvData["group_id"]}',
            event = eventObj.plugin_event
        )

    def private_message(eventObj:rxEvent, **kwargs):
        botHash = eventObj.plugin_event.bot_info.hash
        eventObj.rvData = {}
        eventObj.rvData['time'] = eventObj.plugin_event.base_info['time']
        eventObj.rvData['self_id'] = setMappingIdDict(botHash, backport_int(eventObj.plugin_event.base_info['self_id']))
        eventObj.rvData['post_type'] = 'message'
        eventObj.rvData['message_type'] = 'private'
        eventObj.rvData['sub_type'] = eventObj.plugin_event.data.sub_type
        eventObj.rvData['message_id'] = setMappingIdDict(botHash, backport_int(eventObj.plugin_event.data.message_id))
        eventObj.rvData['user_id'] = setMappingIdDict(botHash, backport_int(eventObj.plugin_event.data.user_id))
        eventObj.rvData['message'] = paraMapper(eventObj.plugin_event.data.message.data, msgType=kwargs.get('msgType', 'para'))
        eventObj.rvData['raw_message'] = eventObj.rvData['message']
        eventObj.rvData['font'] = 1
        eventObj.rvData['sender'] = {}
        eventObj.rvData['sender']['user_id'] = eventObj.rvData['user_id']
        eventObj.rvData['sender']['nickname'] = eventObj.plugin_event.data.sender['name']
        updateEventRegDict(
            botHash = botHash,
            key = f'private_message/{eventObj.rvData["user_id"]}',
            event = eventObj.plugin_event
        )

class txEvent(object):
    def __init__(self, ws, hostType = 'ws', msg:'str|None' = None, hash = None):
        self.active = True
        self.hostType = hostType
        self.ws = ws
        self.hash = hash
        self.raw = msg
        if 'ws' == self.hostType:
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
        if 'ws' == self.hostType:
            if self.active:
                if str(list(self.ws.server.serversocket.getsockname())[1]) in OlivOSOnebotV11.websocketServer.clientDict:
                    if len(OlivOSOnebotV11.websocketServer.clientDict[str(list(self.ws.server.serversocket.getsockname())[1])]) >= 1:
                        botInfoDict_key = OlivOSOnebotV11.websocketServer.clientDict[str(list(self.ws.server.serversocket.getsockname())[1])][0]['info']['hash']
                if botInfoDict_key == None:
                    if len(list(OlivOSOnebotV11.main.confDict)) >= 1:
                        botInfoDict_key = list(OlivOSOnebotV11.main.confDict)[0]
                        pass
        if 'r-ws' == self.hostType:
            if self.hash is not None:
                botInfoDict_key = self.hash
        if botInfoDict_key != None:
            self.plugin_event = OlivOS.API.Event(
                OlivOS.contentAPI.fake_sdk_event(
                    bot_info = OlivOSOnebotV11.main.botInfoDict[botInfoDict_key],
                    fakename = OlivOSOnebotV11.main.pluginName
                ),
                self.Proc.log
            )

    def doRouter(self):
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
            if 'ws' == self.hostType:
                if self.rvMsg != None:
                    self.ws.sendMessage(self.rvMsg)
            if 'r-ws' == self.hostType:
                if self.rvMsg != None:
                    self.ws.send(self.rvMsg)
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
        res = eventObj.plugin_event.get_msg(
            message_id = str(eventObj.params['message_id'])
        )
        if res == None:
            eventObj.rvData = {}
        elif res['active']:
            eventObj.rvData = {}
            eventObj.rvData['message_id'] = res['data']['message_id']
            eventObj.rvData['real_id'] = res['data']['id']
            eventObj.rvData['sender'] = {}
            eventObj.rvData['sender']['user_id'] = backport_int(res['data']['sender']['id'])
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
            eventObj.rvData['user_id'] = backport_int(res['data']['id'])
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
                tmp_data_this['group_id'] = backport_int(data_this['id'])
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
            eventObj.rvData['group_id'] = backport_int(res['data']['id'])
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
            eventObj.rvData['user_id'] = backport_int(res['data']['id'])
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
                tmp_data_this['user_id'] = backport_int(data_this['id'])
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
            eventObj.rvData['user_id'] = backport_int(res['data']['id'])
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
                tmp_data_this['user_id'] = backport_int(data_this['id'])
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
        botHash = eventObj.plugin_event.bot_info.hash
        tmp_pluginEvent = getEventRegDict(
            botHash = botHash,
            key = f'private_message/{eventObj.params["user_id"]}'
        )
        if tmp_pluginEvent != None:
            eventObj.plugin_event = tmp_pluginEvent
        res = eventObj.plugin_event.send(
            send_type = 'private',
            target_id = getMappingIdDict(botHash, str(eventObj.params['user_id'])),
            message = paraRvMapper(
                eventObj.params['message']
            )
        )
        eventObj.rvData = None

    def send_group_msg(eventObj):
        botHash = eventObj.plugin_event.bot_info.hash
        tmp_pluginEvent = getEventRegDict(
            botHash = botHash,
            key = f'group_message/{eventObj.params["group_id"]}'
        )
        if tmp_pluginEvent != None:
            eventObj.plugin_event = tmp_pluginEvent
        res = eventObj.plugin_event.send(
            send_type = 'group',
            target_id = getMappingIdDict(botHash, str(eventObj.params['group_id'])),
            message = paraRvMapper(
                eventObj.params['message']
            ),
            host_id = getMappingIdDict(botHash, getHostIdDict(
                botHash = botHash,
                groupId = str(eventObj.params['group_id'])
            ))
        )
        eventObj.rvData = None

    def send_msg(eventObj):
        botHash = eventObj.plugin_event.bot_info.hash
        tmp_hostId = None
        tmp_targetId = None
        tmp_pluginEvent = None
        if eventObj.params['message_type'] == 'group':
            tmp_targetId = str(eventObj.params['group_id'])
            tmp_hostId = getHostIdDict(
                botHash = botHash,
                groupId = str(eventObj.params['group_id'])
            )
            tmp_pluginEvent = getEventRegDict(
                botHash = botHash,
                key = f'group_message/{eventObj.params["group_id"]}'
            )
        else:
            tmp_targetId = str(eventObj.params['user_id'])
            tmp_pluginEvent = getEventRegDict(
                botHash = botHash,
                key = f'private_message/{eventObj.params["user_id"]}'
            )
        if tmp_pluginEvent != None:
            eventObj.plugin_event = tmp_pluginEvent
        res = eventObj.plugin_event.send(
            send_type = eventObj.params['message_type'],
            target_id = getMappingIdDict(botHash, tmp_targetId),
            message = paraRvMapper(
                eventObj.params['message']
            ),
            host_id = getMappingIdDict(botHash, tmp_hostId)
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

def backport_int(src):
    res = src
    try:
        res = int(res)
    except:
        res = res
    return res
