# -*-coding:utf-8 -*-

import wx
import time
import wx.grid
import pickle
import os
import redis


def chkfile(filename):
    file_path = filename

    if (os.path.isfile(file_path)):
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
            return data

    else:
        with open(file_path, 'wb') as f:
            data = {'item': [], "RedisServer": None}
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
            return data


def whirefile(filename, data):
    with open(filename, 'wb') as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        return data


class SubclassDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title=u"主機管理", size=(400, 400))

        wx.StaticText(self, label=u"主機管理頁面", pos=(100, 10), size=(-1, -1)).SetFont(
            wx.Font(18, wx.DECORATIVE, wx.ITALIC, wx.NORMAL))

        self.grid1 = wx.grid.Grid(self, wx.ID_ANY, (20, 50), size=wx.Size(330, 130), style=wx.SIMPLE_BORDER)
        self.grid1.CreateGrid(4, 3)

        self.grid1.SetRowLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.grid1.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        [self.grid1.SetColLabelValue(i, col) for i, col in enumerate([u"服務器名稱", u"Redis Key", u"警報等級"])]

        ChoiceEditor = wx.grid.GridCellChoiceEditor([u'低', u'中', u'高'], allowOthers=False)

        [self.grid1.SetCellEditor(i, 2, ChoiceEditor) for i in range(4)]

        # self.grid1 set value
        self.data = chkfile('data.pkl')
        if self.data["item"]:
            for r, items in enumerate(self.data["item"]):
                for c, v in enumerate(items.values()):
                    self.grid1.SetCellValue(r, c, v["text"])
                    self.grid1.SetCellBackgroundColour(r, c, v["bg"])

        self.Btn_OK = wx.Button(self, wx.ID_OK, "OK", pos=(100, 200), size=(50, 50))
        self.Btn_Cancel = wx.Button(self, wx.ID_CANCEL, "Cancel", pos=(200, 200), size=(50, 50))

        self.CreateGirdEvent()

    def CreateGirdEvent(self):
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_CHANGING, self.cellchange)


    def cellchange(self, event):

        Row = event.GetRow()
        Col = event.GetCol()

        # 警報等級 黃橙紅
        AlarmLabel = {
            u"低": (247, 247, 0),
            u"中": (255, 128, 0),
            u"高": wx.RED,
        }

        if Col == 2:

            if AlarmLabel.get(event.GetString()):
                self.grid1.SetCellBackgroundColour(Row, Col, AlarmLabel[event.GetString()])


class MyFrame1(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, id=wx.ID_ANY, title=u"Zabbix 報警程序", pos=wx.DefaultPosition,
                          size=wx.Size(300, 350),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX | wx.TAB_TRAVERSAL)

        self.SetBackgroundColour('White')

        # --- Default
        self.data = chkfile('data.pkl')
        if not self.data["RedisServer"]:
            self.data["RedisServer"] = "127.0.0.1"

        self.rc = redis.StrictRedis(self.data["RedisServer"])

        # --- Menu
        self.m_menubar = wx.MenuBar(0)
        self.Menu = wx.Menu()
        self.menuSetting = wx.MenuItem(self.Menu, 1, u"RedisServer", help="")
        self.Menu.AppendItem(self.menuSetting)
        self.menuItem1 = wx.MenuItem(self.Menu, 2, u"服務器管理", help="")
        self.Menu.AppendItem(self.menuItem1)

        self.m_menubar.Append(self.Menu, u"設定")

        self.SetMenuBar(self.m_menubar)

        # --- 系統時間

        self.Label_Nowtime = wx.StaticText(self, wx.ID_ANY, time.strftime("%Y/%m/%d %H:%M:%S"), (30, 5),
                                           wx.Size(-1, -1), 0)

        self.Label_Nowtime.SetFont(wx.Font(18, wx.DECORATIVE, wx.ITALIC, wx.NORMAL))

        # --- RedisServer
        wx.StaticText(self, 1, "Redis Server:", (15, 50), (-1, -1)).SetFont(
            wx.Font(14, wx.DECORATIVE, wx.ITALIC, wx.NORMAL))
        self.Label_RedisServer = wx.StaticText(self, 1, self.data["RedisServer"], (150, 50), (-1, -1))

        self.Label_RedisServer.SetFont(
            wx.Font(14, wx.DECORATIVE, wx.ITALIC, wx.NORMAL))

        # --- Button
        # BtnPos = [(60, 80),(150, 80),(60, 160),(150, 160)]
        self.Btn1 = wx.Button(self, wx.ID_ANY, "", (60, 120), wx.Size(60, 60), 0)
        self.Btn2 = wx.Button(self, wx.ID_ANY, "", (150, 120), wx.Size(60, 60), 0)
        self.Btn3 = wx.Button(self, wx.ID_ANY, "", (60, 200), wx.Size(60, 60), 0)
        self.Btn4 = wx.Button(self, wx.ID_ANY, "", (150, 200), wx.Size(60, 60), 0)
        self.Group_Btn = [self.Btn1, self.Btn2, self.Btn3, self.Btn4]
        [i.Hide() for i in self.Group_Btn]
        [i.SetName("0") for i in self.Group_Btn]

        # --- StaticText
        self.Label_RadisStatus = wx.StaticText(self, wx.ID_ANY, u"Redis服務器無法連接", (50, 120), wx.Size(-1, -1), 0)
        self.Label_RadisStatus.SetFont(wx.Font(14, wx.DECORATIVE, wx.ITALIC, wx.NORMAL))
        self.Label_RadisStatus.SetForegroundColour(wx.RED)
        self.Label_RadisStatus.Hide()

        # --- 監控項目
        self.Label_itemtitle = wx.StaticText(self, 1, u"監控項目", (90, 85), (-1, -1))
        self.Label_itemtitle.SetFont(wx.Font(14, wx.DECORATIVE, wx.ITALIC, wx.NORMAL))

        # 啟動
        self.createTimer()
        self.bindMenuEvent()
        self.chkredis(self.rc)

    def chkredis(self, rc):
        try:
            rc.ping()
            self.Label_RadisStatus.Hide()
            self.Label_itemtitle.Show()
            self.timerItem.Start(1000)
        except:
            self.Label_RadisStatus.Show()
            self.Label_itemtitle.Hide()
            [i.Hide() for i in self.Group_Btn]
            self.timerItem.Stop()

    # --- MenuEvent

    def bindMenuEvent(self):
        self.Bind(wx.EVT_MENU, self.OnRedissetting, id=1)
        self.Bind(wx.EVT_MENU, self.OnHostsetting, id=2)

    def OnRedissetting(self, event):
        dlg = wx.TextEntryDialog(self, u'設定Redis Server IP', u"設定")
        dlg.SetValue(self.data["RedisServer"])

        if dlg.ShowModal() == wx.ID_OK:
            [i.Hide() for i in self.Group_Btn]
            self.data["RedisServer"] = dlg.GetValue()
            whirefile("data.pkl", self.data)
            self.Label_RedisServer.SetLabel(self.data["RedisServer"])
            self.rc = redis.StrictRedis(self.data["RedisServer"])
            self.chkredis(self.rc)

        dlg.Destroy()

    def OnHostsetting(self, event):

        dialog = SubclassDialog(self)
        dlg = dialog.ShowModal()
        if dlg == wx.ID_OK:
            [i.Hide() for i in self.Group_Btn]
            self.data["item"] = []
            for r in range(dialog.grid1.GetNumberRows()):
                if dialog.grid1.GetCellValue(r, 0):
                    data = {}
                    for c in range(dialog.grid1.GetNumberCols()):
                        content = {
                            "text": dialog.grid1.GetCellValue(r, c),
                            "bg": dialog.grid1.GetCellBackgroundColour(r, c)
                        }
                        data[dialog.grid1.GetColLabelValue(c)] = content
                    self.data["item"].append(data)

            whirefile("data.pkl", self.data)
            self.timerItem.Start(1000)

        else:
            print "Cancel"
        dialog.Destroy()

    # --- Timer

    def createTimer(self):

        self.timer1 = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._OnReTime, self.timer1)
        self.timer1.Start(1000)

        self.timerItem = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._OnRefresh, self.timerItem)

    def _OnReTime(self,event):
        # 系統時間
        NowTime = time.strftime("%Y/%m/%d %H:%M:%S")
        self.Label_Nowtime.SetLabel(NowTime)

    def _OnRefresh(self,event):

        for i, btn in zip(self.data["item"], self.Group_Btn):

            key = self.rc.get(i[u"Redis Key"]["text"])
            if key:
                btn.Show()
                btn.SetLabel(i[u"服務器名稱"]["text"])
                btnstatus = btn.GetName()
                if "OK" in self.rc.get(i[u"Redis Key"]["text"]):
                    btn.SetBackgroundColour(wx.GREEN)
                else:
                    btn.SetBackgroundColour(i[u'警報等級']["bg"])
                    if not "1" in btnstatus:
                        btn.SetName("1")
                        wx.Sound(r"C:\Windows\Media\tada.wav").Play()



if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame1().Show()
    app.MainLoop()
