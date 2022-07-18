# -*- encoding: utf-8 -*-
'''
@File      :   main.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2022, lunzhiPenxil仑质
@Desc      :   None
'''


import OlivOS
import OlivOSOnebotV11

ProcObj = None
botInfoDict = {}

confDict = {}

hostIdDict = {}

pluginName = 'OlivOSOnebotV11协议端'

class Event(object):
    def init(plugin_event, Proc):
        pass

    def init_after(plugin_event, Proc):
        global ProcObj
        global botInfoDict
        global confDict
        ProcObj = Proc
        for bot_info_hash in ProcObj.Proc_data['bot_info_dict']:
            botInfoDict[bot_info_hash] = ProcObj.Proc_data['bot_info_dict'][bot_info_hash]
            if ProcObj.Proc_data['bot_info_dict'][bot_info_hash].platform['sdk'] == 'onebot':
                tmp_default_hash = bot_info_hash
        confDict = OlivOSOnebotV11.eventRouter.initBotInfo(tmp_default_hash, 55009)
        OlivOSOnebotV11.websocketServer.start_websocket(confDict)
        OlivOSOnebotV11.eventRouter.saveBotInfo(confDict)

    def save(plugin_event, Proc):
        global confDict
        OlivOSOnebotV11.eventRouter.saveBotInfo(confDict)

    def private_message(plugin_event, Proc):
        rxEvent = OlivOSOnebotV11.eventRouter.rxEvent('private_message', plugin_event, Proc)
        rxEvent.doRouter()
        pass

    def group_message(plugin_event, Proc):
        rxEvent = OlivOSOnebotV11.eventRouter.rxEvent('group_message', plugin_event, Proc)
        rxEvent.doRouter()
        pass
