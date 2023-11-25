# -*- encoding: utf-8 -*-
'''
@File      :   main.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2022, lunzhiPenxil仑质
@Desc      :   None
'''

import platform

import OlivOS
import OlivOSOnebotV11

ProcObj = None
botInfoDict = {}

confDict = {}
r_confDict = {}

hostIdDict = {}

mappingIdDict = {}

eventRegDict = {}

pluginName = 'OlivOSOnebotV11协议端'

class Event(object):
    def init(plugin_event:OlivOS.API.Event, Proc:OlivOS.pluginAPI.shallow):
        pass

    def init_after(plugin_event:OlivOS.API.Event, Proc:OlivOS.pluginAPI.shallow):
        global ProcObj
        global botInfoDict
        global confDict, r_confDict
        ProcObj = Proc
        for bot_info_hash in ProcObj.Proc_data['bot_info_dict']:
            botInfoDict[bot_info_hash] = ProcObj.Proc_data['bot_info_dict'][bot_info_hash]
        confDict, r_confDict = OlivOSOnebotV11.eventRouter.initBotInfo(ProcObj.Proc_data['bot_info_dict'], None)
        OlivOSOnebotV11.websocketServer.start_websocket(confDict)
        OlivOSOnebotV11.eventRouter.saveBotInfo(confDict, r_confDict)

    def save(plugin_event:OlivOS.API.Event, Proc:OlivOS.pluginAPI.shallow):
        global confDict, r_confDict
        OlivOSOnebotV11.eventRouter.saveBotInfo(confDict, r_confDict)

    def private_message(plugin_event:OlivOS.API.Event, Proc:OlivOS.pluginAPI.shallow):
        rxEvent = OlivOSOnebotV11.eventRouter.rxEvent('private_message', plugin_event, Proc)
        rxEvent.doRouter()
        pass

    def group_message(plugin_event:OlivOS.API.Event, Proc:OlivOS.pluginAPI.shallow):
        rxEvent = OlivOSOnebotV11.eventRouter.rxEvent('group_message', plugin_event, Proc)
        rxEvent.doRouter()
        pass

    def menu(plugin_event:OlivOS.API.Event, Proc:OlivOS.pluginAPI.shallow):
        if(platform.system() == 'Windows'):
            if plugin_event.data.namespace == 'OlivOSOnebotV11':
                if plugin_event.data.event == 'OlivOSOnebotV11_001':
                    if True or not OlivOSOnebotV11.GUI.flag_open:
                        OlivOSOnebotV11.GUI.flag_open = True
                        OlivOSOnebotV11.GUI.ConfigUI(
                            Model_name = 'shallow_menu_plugin_manage',
                            logger_proc = Proc.Proc_info.logger_proc.log
                        ).start()
