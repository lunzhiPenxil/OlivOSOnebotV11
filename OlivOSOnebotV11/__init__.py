# -*- encoding: utf-8 -*-
'''
@File      :   __init__.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2022, lunzhiPenxil仑质
@Desc      :   None
'''
import platform

from . import main
from . import SimpleWebSocketServer
from . import websocketLink
from . import websocketServer
from . import eventRouter
if(platform.system() == 'Windows'):
    from . import GUI
