# -*- encoding: utf-8 -*-
'''
@File      :   GUI.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2022, lunzhiPenxil仑质
@Desc      :   None
'''

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
    window_title = 'OlivOS OnebotV11 协议端 正向WS'
    route_name = 'confDict'
    url_scheme = 'ws'
    remap_mode = 'auto'
    tree_y = 64
    tree_height = 321

    def __init__(self, Model_name, logger_proc=None):
        self.Model_name = Model_name
        self.UIObject = {}
        self.UIData = {}
        self.UIConfig = {}
        self.logger_proc = logger_proc
        self.UIData['flag_open'] = False
        self.UIData['click_record'] = {}
        self.UIData['loading_extra_fields'] = False
        self.UIConfig.update(dictColorContext)
        self.routeData = {}

    def start(self):
        self.UIObject['root'] = tkinter.Toplevel()
        self.UIObject['root'].title(self.window_title)
        self.UIObject['root'].geometry('518x400')
        self.UIObject['root'].resizable(
            width=False,
            height=False
        )
        self.UIObject['root'].configure(bg=self.UIConfig['color_001'])

        self.tree_init()

        self.tree_UI_Button_init(
            name='root_Button_SAVE',
            text='保存 并重载',
            command=lambda: self.tree_save(),
            x=15,
            y=15,
            width=140,
            height=34
        )

        self.tree_UI_Button_init(
            name='root_Button_REMAPPING',
            text='重新分配 并重载',
            command=lambda: self.tree_remapping(),
            x=15 + (140 + 15) * 1,
            y=15,
            width=140,
            height=34
        )

        self.tree_edit_UI_Entry_init(
            obj_root='root',
            obj_name='root_Entry_PORT',
            str_name='root_Entry_PORT_StringVar',
            x=15 + (140 + 15) * 2 + 50,
            y=19,
            width_t=50,
            width=100,
            height=26,
            action=None,
            title='端口:'
        )
        self.UIData['root_Entry_PORT_StringVar'].trace('w', self.entry_port_edit)

        self.init_extra_fields()

        self.UIObject['root'].iconbitmap('./resource/tmp_favoricon.ico')
        self.UIObject['root'].mainloop()
        OlivOSOnebotV11.GUI.flag_open = False

    def tree_init(self):
        self.UIObject['tree'] = ttk.Treeview(self.UIObject['root'])
        self.UIObject['tree']['show'] = 'headings'
        self.UIObject['tree']['columns'] = ('KEY', 'PORT')
        self.UIObject['tree'].column('KEY', width=270)
        self.UIObject['tree'].column('PORT', width=180)
        self.UIObject['tree'].heading('KEY', text='账号')
        self.UIObject['tree'].heading('PORT', text='地址')
        self.UIObject['tree']['selectmode'] = 'browse'
        # self.UIObject['tree_rightkey_menu'] = tkinter.Menu(self.UIObject['root'], tearoff = False)
        self.UIObject['tree'].bind('<<TreeviewSelect>>', lambda x: self.treeSelect('tree', x))
        self.tree_load_init()
        self.tree_load()
        self.UIObject['tree'].place(x=15, y=self.tree_y, width=488 - 18, height=self.tree_height)
        # self.UIObject['tree'].bind('<Button-3>', lambda x : self.tree_rightKey(x))
        self.UIObject['tree_yscroll'] = ttk.Scrollbar(
            self.UIObject['root'],
            orient="vertical",
            command=self.UIObject['tree'].yview
        )
        self.UIObject['tree_yscroll'].place(
            x=15 + 488 - 18,
            y=self.tree_y,
            width=18,
            height=self.tree_height
        )
        self.UIObject['tree'].configure(
            yscrollcommand=self.UIObject['tree_yscroll'].set
        )

    def tree_load_init(self):
        route_source = getattr(OlivOSOnebotV11.main, self.route_name)
        for hash in route_source:
            if 'hash' in route_source[hash] and 'port' in route_source[hash]:
                self.routeData[route_source[hash]['hash']] = route_source[hash].copy()

    def init_extra_fields(self):
        pass

    def load_extra_fields(self, bot_hash):
        pass

    def save_extra_fields(self, bot_hash):
        pass

    def tree_save_extra_fields(self):
        force = get_tree_force(self.UIObject['tree'])
        if force['text'] in self.routeData:
            self.save_extra_fields(force['text'])

    def get_ws_url(self, port):
        if port is None or len(str(port)) <= 0:
            return ''
        return '%s://localhost:%s' % (self.url_scheme, str(port))

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
                        text=hash,
                        values=(
                            key,
                            self.get_ws_url(self.routeData[hash]['port'])
                        )
                    )
                except Exception:
                    pass

    def treeSelect(self, name, x):
        if name == 'tree':
            force = get_tree_force(self.UIObject['tree'])
            if force['text'] in self.routeData:
                port = self.routeData[force['text']]['port']
                if port is None:
                    port = ''
                self.UIData['root_Entry_PORT_StringVar'].set(str(port))
                self.load_extra_fields(force['text'])

    def tree_UI_Button_init(self, name, text, command, x, y, width, height):
        self.UIObject[name] = tkinter.Button(
            self.UIObject['root'],
            text=text,
            command=command,
            bd=0,
            activebackground=self.UIConfig['color_002'],
            activeforeground=self.UIConfig['color_001'],
            bg=self.UIConfig['color_003'],
            fg=self.UIConfig['color_004'],
            relief='groove'
        )
        self.UIObject[name].bind('<Enter>', lambda x: self.buttom_action(name, '<Enter>'))
        self.UIObject[name].bind('<Leave>', lambda x: self.buttom_action(name, '<Leave>'))
        self.UIObject[name].bind('<Button-1>', lambda x: self.clickRecord(name, x))
        self.UIObject[name].place(
            x=x,
            y=y,
            width=width,
            height=height
        )

    def buttom_action(self, name, action):
        if name in self.UIObject:
            if action == '<Enter>':
                self.UIObject[name].configure(bg=self.UIConfig['color_006'])
            if action == '<Leave>':
                self.UIObject[name].configure(bg=self.UIConfig['color_003'])

    def clickRecord(self, name, event):
        self.UIData['click_record'][name] = event

    def tree_edit_UI_Entry_init(self, obj_root, obj_name, str_name, x, y, width_t,
                                width, height, action, title='', mode='NONE'):
        self.UIObject[obj_name + '=Label'] = tkinter.Label(
            self.UIObject[obj_root],
            text=title
        )
        self.UIObject[obj_name + '=Label'].configure(
            bg=self.UIConfig['color_001'],
            fg=self.UIConfig['color_004']
        )
        self.UIObject[obj_name + '=Label'].place(
            x=x - width_t,
            y=y,
            width=width_t,
            height=height
        )
        self.UIData[str_name] = tkinter.StringVar()
        self.UIObject[obj_name] = tkinter.Entry(
            self.UIObject[obj_root],
            textvariable=self.UIData[str_name]
        )
        self.UIObject[obj_name].configure(
            bg=self.UIConfig['color_004'],
            fg=self.UIConfig['color_005'],
            bd=0
        )
        if mode == 'SAFE':
            self.UIObject[obj_name].configure(
                show='●'
            )
        self.UIObject[obj_name].place(
            x=x,
            y=y,
            width=width,
            height=height
        )

    def entry_port_edit(self, *args, **kwargs):
        self.tree_save_port()

    def tree_save_port(self):
        force = get_tree_force(self.UIObject['tree'])
        selection = self.UIObject['tree'].selection()
        if force['text'] in self.routeData:
            try:
                port = self.UIData['root_Entry_PORT_StringVar'].get().strip()
                if len(port) <= 0:
                    self.routeData[force['text']]['port'] = None
                    self.UIObject['tree'].set(selection, column='PORT', value='')
                    return
                self.routeData[force['text']]['port'] = int(port)
                self.UIObject['tree'].set(selection, column='PORT', value=self.get_ws_url(port))
                # self.tree_load()
            except Exception:
                pass

    def tree_save(self):
        self.tree_save_extra_fields()
        setattr(OlivOSOnebotV11.main, self.route_name, self.routeData)
        OlivOSOnebotV11.main.ProcObj.set_restart()

    def tree_remapping(self):
        used_port = set()
        for hash in self.routeData:
            if self.remap_mode == 'free':
                port = OlivOSOnebotV11.httpServer.get_free_port()
                while port in used_port:
                    port = OlivOSOnebotV11.httpServer.get_free_port()
                used_port.add(port)
                self.routeData[hash]['port'] = port
            else:
                self.routeData[hash]['port'] = None
        self.tree_save()


class ConfigHTTPUI(ConfigUI):
    window_title = 'OlivOS OnebotV11 协议端 正向HTTP'
    route_name = 'httpConfDict'
    url_scheme = 'http'
    remap_mode = 'free'
    tree_y = 105
    tree_height = 280

    def init_extra_fields(self):
        self.tree_edit_UI_Entry_init(
            obj_root='root',
            obj_name='root_Entry_ACCESS_TOKEN',
            str_name='root_Entry_ACCESS_TOKEN_StringVar',
            x=65,
            y=69,
            width_t=50,
            width=438,
            height=26,
            action=None,
            title='令牌:',
            mode='SAFE'
        )
        self.UIData['root_Entry_ACCESS_TOKEN_StringVar'].trace('w', self.entry_access_token_edit)

    def entry_access_token_edit(self, *args, **kwargs):
        if self.UIData.get('loading_extra_fields', False):
            return
        self.tree_save_extra_fields()

    def load_extra_fields(self, bot_hash):
        conf_this = self.routeData[bot_hash]
        token = conf_this.get('access_token', '')
        if token is None or len(str(token)) <= 0:
            token = conf_this.get('token', '')
        if token is None:
            token = ''
        self.UIData['loading_extra_fields'] = True
        try:
            self.UIData['root_Entry_ACCESS_TOKEN_StringVar'].set(str(token))
        finally:
            self.UIData['loading_extra_fields'] = False

    def save_extra_fields(self, bot_hash):
        conf_this = self.routeData[bot_hash]
        token = self.UIData['root_Entry_ACCESS_TOKEN_StringVar'].get()
        conf_this.pop('token', None)
        if len(token) > 0:
            conf_this['access_token'] = token
        else:
            conf_this.pop('access_token', None)


class ConfigRUI(object):
    window_title = 'OlivOS OnebotV11 协议端 反向WS'
    route_name = 'r_confDict'
    content_y = 64
    content_height = 321

    def __init__(self, Model_name, logger_proc=None):
        self.Model_name = Model_name
        self.UIObject = {}
        self.UIData = {}
        self.UIConfig = {}
        self.logger_proc = logger_proc
        self.UIData['flag_open'] = False
        self.UIData['click_record'] = {}
        self.UIData['loading_extra_fields'] = False
        self.UIConfig.update(dictColorContext)
        self.routeData = {}

    def start(self):
        self.UIObject['root'] = tkinter.Toplevel()
        self.UIObject['root'].title(self.window_title)
        self.UIObject['root'].geometry('518x400')
        self.UIObject['root'].resizable(
            width=False,
            height=False
        )
        self.UIObject['root'].configure(bg=self.UIConfig['color_001'])

        self.tree_init()

        self.tree_UI_Button_init(
            name='root_Button_SAVE',
            text='保存 并重载',
            command=lambda: self.tree_save(),
            x=15,
            y=15,
            width=140,
            height=34
        )

        self.tree_UI_Button_init(
            name='root_Button_SAVE_NOW',
            text='保存',
            command=lambda: self.tree_save_now(),
            x=15 + (140 + 15) * 1,
            y=15,
            width=140,
            height=34
        )

        self.tree_edit_UI_Text_init(
            obj_root='root',
            obj_name='root_Text_PATH',
            str_name='root_Text_PATH_StringVar',
            x=15 + (170 + 15) * 1,
            y=self.content_y,
            width=518 - 18 - (170 + 15) * 1 - 15,
            height=self.content_height
        )
        self.UIObject['root_Text_PATH_yscroll'] = ttk.Scrollbar(
            self.UIObject['root'],
            orient="vertical",
            command=self.UIObject['root_Text_PATH'].yview
        )
        self.UIObject['root_Text_PATH_yscroll'].place(
            x=518 - 18 - 15,
            y=self.content_y,
            width=18,
            height=self.content_height
        )
        self.UIObject['root_Text_PATH'].configure(
            yscrollcommand=self.UIObject['root_Text_PATH_yscroll'].set
        )

        self.init_extra_fields()

        self.UIObject['root'].iconbitmap('./resource/tmp_favoricon.ico')
        self.UIObject['root'].mainloop()
        OlivOSOnebotV11.GUI.flag_open = False

    def tree_init(self):
        self.UIObject['tree'] = ttk.Treeview(self.UIObject['root'])
        self.UIObject['tree']['show'] = 'headings'
        self.UIObject['tree']['columns'] = ('KEY', )
        self.UIObject['tree'].column('KEY', width=50)
        self.UIObject['tree'].heading('KEY', text='账号')
        self.UIObject['tree']['selectmode'] = 'browse'
        # self.UIObject['tree_rightkey_menu'] = tkinter.Menu(self.UIObject['root'], tearoff = False)
        self.UIObject['tree'].bind('<<TreeviewSelect>>', lambda x: self.treeSelect('tree', x))
        self.tree_load_init()
        self.tree_load()
        self.UIObject['tree'].place(x=15, y=self.content_y, width=170 - 18, height=self.content_height)
        # self.UIObject['tree'].bind('<Button-3>', lambda x : self.tree_rightKey(x))
        self.UIObject['tree_yscroll'] = ttk.Scrollbar(
            self.UIObject['root'],
            orient="vertical",
            command=self.UIObject['tree'].yview
        )
        self.UIObject['tree_yscroll'].place(
            x=15 + 170 - 18,
            y=self.content_y,
            width=18,
            height=self.content_height
        )
        self.UIObject['tree'].configure(
            yscrollcommand=self.UIObject['tree_yscroll'].set
        )

    def tree_load_init(self):
        route_source = getattr(OlivOSOnebotV11.main, self.route_name)
        for hash in route_source:
            if 'hash' in route_source[hash] \
                    and 'path' in route_source[hash]:
                self.routeData[hash] = route_source[hash].copy()

    def init_extra_fields(self):
        pass

    def load_extra_fields(self, bot_hash):
        pass

    def save_extra_fields(self, bot_hash):
        pass

    def tree_save_extra_fields(self):
        force = get_tree_force(self.UIObject['tree'])
        if force['text'] in self.routeData:
            self.save_extra_fields(force['text'])

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
                        text=hash,
                        values=(
                            key,
                        )
                    )
                except Exception:
                    pass

    def treeSelect(self, name, x):
        if name == 'tree':
            force = get_tree_force(self.UIObject['tree'])
            self.UIObject['root_Text_PATH'].delete('1.0', tkinter.END)
            if force['text'] in self.routeData:
                self.UIObject['root_Text_PATH'].insert('1.0', '\n'.join(self.routeData[force['text']]['path']))
                self.load_extra_fields(force['text'])

    def tree_UI_Button_init(self, name, text, command, x, y, width, height):
        self.UIObject[name] = tkinter.Button(
            self.UIObject['root'],
            text=text,
            command=command,
            bd=0,
            activebackground=self.UIConfig['color_002'],
            activeforeground=self.UIConfig['color_001'],
            bg=self.UIConfig['color_003'],
            fg=self.UIConfig['color_004'],
            relief='groove'
        )
        self.UIObject[name].bind('<Enter>', lambda x: self.buttom_action(name, '<Enter>'))
        self.UIObject[name].bind('<Leave>', lambda x: self.buttom_action(name, '<Leave>'))
        self.UIObject[name].bind('<Button-1>', lambda x: self.clickRecord(name, x))
        self.UIObject[name].place(
            x=x,
            y=y,
            width=width,
            height=height
        )

    def buttom_action(self, name, action):
        if name in self.UIObject:
            if action == '<Enter>':
                self.UIObject[name].configure(bg=self.UIConfig['color_006'])
            if action == '<Leave>':
                self.UIObject[name].configure(bg=self.UIConfig['color_003'])

    def clickRecord(self, name, event):
        self.UIData['click_record'][name] = event

    def tree_edit_UI_Entry_init(self, obj_root, obj_name, str_name, x, y, width_t,
                                width, height, action, title='', mode='NONE'):
        self.UIObject[obj_name + '=Label'] = tkinter.Label(
            self.UIObject[obj_root],
            text=title
        )
        self.UIObject[obj_name + '=Label'].configure(
            bg=self.UIConfig['color_001'],
            fg=self.UIConfig['color_004']
        )
        self.UIObject[obj_name + '=Label'].place(
            x=x - width_t,
            y=y,
            width=width_t,
            height=height
        )
        self.UIData[str_name] = tkinter.StringVar()
        self.UIObject[obj_name] = tkinter.Entry(
            self.UIObject[obj_root],
            textvariable=self.UIData[str_name]
        )
        self.UIObject[obj_name].configure(
            bg=self.UIConfig['color_004'],
            fg=self.UIConfig['color_005'],
            bd=0
        )
        if mode == 'SAFE':
            self.UIObject[obj_name].configure(
                show='●'
            )
        self.UIObject[obj_name].place(
            x=x,
            y=y,
            width=width,
            height=height
        )

    def tree_edit_UI_Text_init(self, obj_root, obj_name, str_name, x, y, width, height):
        self.UIData[str_name] = tkinter.StringVar()
        self.UIObject[obj_name] = tkinter.Text(
            self.UIObject[obj_root],
            wrap=tkinter.WORD
        )
        self.UIObject[obj_name].configure(
            bg=self.UIConfig['color_004'],
            fg=self.UIConfig['color_005'],
            bd=0
        )
        self.UIObject[obj_name].place(
            x=x,
            y=y,
            width=width,
            height=height
        )

    def tree_save_now(self):
        force = get_tree_force(self.UIObject['tree'])
        value = self.UIObject['root_Text_PATH'].get('1.0', tkinter.END)
        value_list = value.split('\n')
        value_list_new = []
        for value_this in value_list:
            if len(value_this) > 0:
                value_list_new.append(value_this)
        if force['text'] in self.routeData:
            self.routeData[force['text']]['path'] = value_list_new
            self.save_extra_fields(force['text'])

    def tree_save(self):
        self.tree_save_now()
        setattr(OlivOSOnebotV11.main, self.route_name, self.routeData)
        OlivOSOnebotV11.main.ProcObj.set_restart()


class ConfigRHTTPUI(ConfigRUI):
    window_title = 'OlivOS OnebotV11 协议端 反向HTTP'
    route_name = 'r_httpConfDict'
    content_y = 105
    content_height = 280

    def init_extra_fields(self):
        self.tree_edit_UI_Entry_init(
            obj_root='root',
            obj_name='root_Entry_SECRET',
            str_name='root_Entry_SECRET_StringVar',
            x=65,
            y=69,
            width_t=50,
            width=270,
            height=26,
            action=None,
            title='密钥:',
            mode='SAFE'
        )
        self.tree_edit_UI_Entry_init(
            obj_root='root',
            obj_name='root_Entry_TIMEOUT',
            str_name='root_Entry_TIMEOUT_StringVar',
            x=400,
            y=69,
            width_t=50,
            width=103,
            height=26,
            action=None,
            title='超时:'
        )
        self.UIData['root_Entry_SECRET_StringVar'].trace('w', self.entry_http_extra_edit)
        self.UIData['root_Entry_TIMEOUT_StringVar'].trace('w', self.entry_http_extra_edit)

    def entry_http_extra_edit(self, *args, **kwargs):
        if self.UIData.get('loading_extra_fields', False):
            return
        self.tree_save_extra_fields()

    def load_extra_fields(self, bot_hash):
        conf_this = self.routeData[bot_hash]
        secret = conf_this.get('secret', '')
        timeout = conf_this.get('timeout', '')
        if secret is None:
            secret = ''
        if timeout is None:
            timeout = ''
        self.UIData['loading_extra_fields'] = True
        try:
            self.UIData['root_Entry_SECRET_StringVar'].set(str(secret))
            self.UIData['root_Entry_TIMEOUT_StringVar'].set(str(timeout))
        finally:
            self.UIData['loading_extra_fields'] = False

    def save_extra_fields(self, bot_hash):
        conf_this = self.routeData[bot_hash]
        secret = self.UIData['root_Entry_SECRET_StringVar'].get()
        if len(secret) > 0:
            conf_this['secret'] = secret
        else:
            conf_this.pop('secret', None)
        timeout_text = self.UIData['root_Entry_TIMEOUT_StringVar'].get().strip()
        if len(timeout_text) <= 0:
            conf_this.pop('timeout', None)
            return
        try:
            timeout = float(timeout_text)
        except (TypeError, ValueError):
            return
        if timeout.is_integer():
            timeout = int(timeout)
        conf_this['timeout'] = timeout


def get_tree_force(tree_obj):
    return tree_obj.item(tree_obj.focus())
