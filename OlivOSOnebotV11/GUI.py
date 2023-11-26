# -*- encoding: utf-8 -*-
'''
@File      :   GUI.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2022, lunzhiPenxil仑质
@Desc      :   None
'''

import platform

import OlivOS
import OlivOSOnebotV11

import tkinter
from tkinter import ttk

flag_open = True

dictColorContext = {
    'color_001': '#00A0EA',
    'color_002': '#BBE9FF',
    'color_003': '#40C3FF',
    'color_004': '#FFFFFF',
    'color_005': '#000000',
    'color_006': '#80D7FF'
}


class ConfigUI(object):
    def __init__(self, Model_name, logger_proc = None):
        self.Model_name = Model_name
        self.UIObject = {}
        self.UIData = {}
        self.UIConfig = {}
        self.logger_proc = logger_proc
        self.UIData['flag_open'] = False
        self.UIData['click_record'] = {}
        self.UIConfig.update(dictColorContext)
        self.routeData = {}

    def start(self):
        self.UIObject['root'] = tkinter.Toplevel()
        self.UIObject['root'].title('OlivOS OnebotV11 协议端')
        self.UIObject['root'].geometry('518x400')
        self.UIObject['root'].resizable(
            width = False,
            height = False
        )
        self.UIObject['root'].configure(bg = self.UIConfig['color_001'])

        self.tree_init()

        self.tree_UI_Button_init(
            name = 'root_Button_SAVE',
            text = '保存 并重载',
            command = lambda : self.tree_save(),
            x = 15,
            y = 15,
            width = 140,
            height = 34
        )

        self.tree_UI_Button_init(
            name = 'root_Button_REMAPPING',
            text = '重新分配 并重载',
            command = lambda : self.tree_remapping(),
            x = 15 + (140 + 15) * 1,
            y = 15,
            width = 140,
            height = 34
        )

        self.tree_edit_UI_Entry_init(
            obj_root = 'root',
            obj_name = 'root_Entry_PORT',
            str_name = 'root_Entry_PORT_StringVar',
            x = 15 + (140 + 15) * 2 + 50,
            y = 19,
            width_t = 50,
            width = 100,
            height = 26,
            action = None,
            title = '端口:'
        )
        self.UIData['root_Entry_PORT_StringVar'].trace('w', self.entry_port_edit)

        self.UIObject['root'].iconbitmap('./resource/tmp_favoricon.ico')
        self.UIObject['root'].mainloop()
        OlivOSOnebotV11.GUI.flag_open = False

    def tree_init(self):
        self.UIObject['tree'] = ttk.Treeview(self.UIObject['root'])
        self.UIObject['tree']['show'] = 'headings'
        self.UIObject['tree']['columns'] = ('KEY', 'PORT')
        self.UIObject['tree'].column('KEY', width = 270)
        self.UIObject['tree'].column('PORT', width = 180)
        self.UIObject['tree'].heading('KEY', text = '账号')
        self.UIObject['tree'].heading('PORT', text = '地址')
        self.UIObject['tree']['selectmode'] = 'browse'
        #self.UIObject['tree_rightkey_menu'] = tkinter.Menu(self.UIObject['root'], tearoff = False)
        self.UIObject['tree'].bind('<<TreeviewSelect>>', lambda x : self.treeSelect('tree', x))
        self.tree_load_init()
        self.tree_load()
        self.UIObject['tree'].place(x = 15, y = 64, width = 488 - 18 , height = 321)
        #self.UIObject['tree'].bind('<Button-3>', lambda x : self.tree_rightKey(x))
        self.UIObject['tree_yscroll'] = ttk.Scrollbar(
            self.UIObject['root'],
            orient = "vertical",
            command = self.UIObject['tree'].yview
        )
        self.UIObject['tree_yscroll'].place(
            x = 15 + 488 - 18,
            y = 64,
            width = 18,
            height = 321
        )
        self.UIObject['tree'].configure(
            yscrollcommand = self.UIObject['tree_yscroll'].set
        )

    def tree_load_init(self):
        for hash in OlivOSOnebotV11.main.confDict:
            if 'hash' in OlivOSOnebotV11.main.confDict[hash] and 'port' in OlivOSOnebotV11.main.confDict[hash]:
                self.routeData[OlivOSOnebotV11.main.confDict[hash]['hash']] = {
                    'hash': OlivOSOnebotV11.main.confDict[hash]['hash'],
                    'port': OlivOSOnebotV11.main.confDict[hash]['port']
                }

    def get_ws_url(self, port):
        return 'ws://localhost:%s' % str(port)

    def tree_load(self):
        tmp_tree_item_children = self.UIObject['tree'].get_children()
        for tmp_tree_item_this in tmp_tree_item_children:
            self.UIObject['tree'].delete(tmp_tree_item_this)
        for hash in self.routeData:
            if hash in OlivOSOnebotV11.main.botInfoDict:
                key = '%s - %s' % (
                    str(OlivOSOnebotV11.main.botInfoDict[hash].platform['platform']),
                    str(OlivOSOnebotV11.main.botInfoDict[hash].id)
                )
                try:
                    self.UIObject['tree'].insert(
                        '',
                        0,
                        text = hash,
                        values=(
                            key,
                            self.get_ws_url(str(self.routeData[hash]['port']))
                        )
                    )
                except:
                    pass

    def treeSelect(self, name, x):
        if name == 'tree':
            force = get_tree_force(self.UIObject['tree'])
            if force['text'] in self.routeData:
                self.UIData['root_Entry_PORT_StringVar'].set(str(self.routeData[force['text']]['port']))

    def tree_UI_Button_init(self, name, text, command, x, y, width, height):
        self.UIObject[name] = tkinter.Button(
            self.UIObject['root'],
            text = text,
            command = command,
            bd = 0,
            activebackground = self.UIConfig['color_002'],
            activeforeground = self.UIConfig['color_001'],
            bg = self.UIConfig['color_003'],
            fg = self.UIConfig['color_004'],
            relief = 'groove'
        )
        self.UIObject[name].bind('<Enter>', lambda x : self.buttom_action(name, '<Enter>'))
        self.UIObject[name].bind('<Leave>', lambda x : self.buttom_action(name, '<Leave>'))
        self.UIObject[name].bind('<Button-1>', lambda x : self.clickRecord(name, x))
        self.UIObject[name].place(
            x = x,
            y = y,
            width = width,
            height = height
        )

    def buttom_action(self, name, action):
        if name in self.UIObject:
            if action == '<Enter>':
                self.UIObject[name].configure(bg = self.UIConfig['color_006'])
            if action == '<Leave>':
                self.UIObject[name].configure(bg = self.UIConfig['color_003'])

    def clickRecord(self, name, event):
        self.UIData['click_record'][name] = event

    def tree_edit_UI_Entry_init(self, obj_root, obj_name, str_name, x, y, width_t, width, height, action, title = '', mode = 'NONE'):
        self.UIObject[obj_name + '=Label'] = tkinter.Label(
            self.UIObject[obj_root],
            text = title
        )
        self.UIObject[obj_name + '=Label'].configure(
            bg = self.UIConfig['color_001'],
            fg = self.UIConfig['color_004']
        )
        self.UIObject[obj_name + '=Label'].place(
            x = x - width_t,
            y = y,
            width = width_t,
            height = height
        )
        self.UIData[str_name] = tkinter.StringVar()
        self.UIObject[obj_name] = tkinter.Entry(
            self.UIObject[obj_root],
            textvariable = self.UIData[str_name]
        )
        self.UIObject[obj_name].configure(
            bg = self.UIConfig['color_004'],
            fg = self.UIConfig['color_005'],
            bd = 0
        )
        if mode == 'SAFE':
            self.UIObject[obj_name].configure(
                show = '●'
            )
        self.UIObject[obj_name].place(
            x = x,
            y = y,
            width = width,
            height = height
        )

    def entry_port_edit(self, *args, **kwargs):
        self.tree_save_port()

    def tree_save_port(self):
        force = get_tree_force(self.UIObject['tree'])
        selection = self.UIObject['tree'].selection()
        if force['text'] in self.routeData:
            try:
                port = self.UIData['root_Entry_PORT_StringVar'].get()
                self.routeData[force['text']]['port'] = int(port)
                self.UIObject['tree'].set(selection, column = 'PORT', value = self.get_ws_url(port))
                #self.tree_load()
            except:
                pass

    def tree_save(self):
        OlivOSOnebotV11.main.confDict = self.routeData
        OlivOSOnebotV11.main.ProcObj.set_restart()

    def tree_remapping(self):
        for hash in self.routeData:
            self.routeData[hash]['port'] = None
        self.tree_save()

def get_tree_force(tree_obj):
    return tree_obj.item(tree_obj.focus())
