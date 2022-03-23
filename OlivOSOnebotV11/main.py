# -*- encoding: utf-8 -*-
'''
@File      :   main.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2022, lunzhiPenxil仑质
@Desc      :   None
'''

import threading

import OlivOS
import OlivOSOnebotV11

ProcObj = None
botInfoDict = {}

confDict = {}

pluginName = 'OlivOSOnebotV11协议端'

class Event(object):
    def init(plugin_event, Proc):
        pass

    def init_after(plugin_event, Proc):
        global ProcObj
        global botInfoDict
        global confDict
        ProcObj = Proc
        tmp_default_hash = None
        tmp_default_port = 55009
        for bot_info_hash in ProcObj.Proc_data['bot_info_dict']:
            botInfoDict[bot_info_hash] = ProcObj.Proc_data['bot_info_dict'][bot_info_hash]
            if ProcObj.Proc_data['bot_info_dict'][bot_info_hash].platform['sdk'] == 'onebot':
                tmp_default_hash = bot_info_hash
        conf_bot_info = OlivOSOnebotV11.eventRouter.initBotInfo()
        if conf_bot_info == None:
            if tmp_default_hash != None:
                confDict[tmp_default_hash] = {
                    'hash': tmp_default_hash,
                    'port': tmp_default_port
                }
        else:
            confDict = conf_bot_info
        for server_this in confDict:
            threading.Thread(
                target = OlivOSOnebotV11.websocketServer.init_websocket,
                args = (confDict[server_this],)
            ).start()

    def private_message(plugin_event, Proc):
        rxEvent = OlivOSOnebotV11.eventRouter.rxEvent('private_message', plugin_event, Proc)
        rxEvent.doRouter()
        pass

    def group_message(plugin_event, Proc):
        rxEvent = OlivOSOnebotV11.eventRouter.rxEvent('group_message', plugin_event, Proc)
        rxEvent.doRouter()
        pass
