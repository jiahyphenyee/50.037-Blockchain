# !/usr/bin/env python
import sys
import threading
import time
import subprocess

import wx
from miner import Miner
from SPVClient import SPVClient


APP_EXIT = 1
FILE_SAVE = 2
FILE_OPEN = 3
SHOW_HELP = 4
SHOW_ABOUT = 5

JOIN_NETWORK = 31
START_MINE = 32
MAKE_TXN = 33
VALIDATE_TXN = 34
GET_HEADER = 35
UPDATE_BAL = 36
VERIFY_TXN = 37

class MyFrame(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent)
        self.InitUI()

    def InitUI(self):
        panel=PlayerPanel(self, sys.argv[2])
        self.SetSize((1300, 250))
        self.SetTitle(panel.title)
        self.Center()
        self.Show(True)


class PlayerPanel(wx.Panel):
    def __init__(self, parent, type):
        wx.Panel.__init__(self, parent)
        print(type)

        self.type = type
        self.node = None
        self.title = None

        self.btn_join = wx.Button(self, label='Join Network', pos=(50, 20))
        self.btn_join.id = JOIN_NETWORK
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, self.btn_join)


        self.balance_value = wx.StaticText(self, label='0', pos=(200, 60))

        if type == "m":
            self.balance_label = wx.StaticText(self, label='Balance:  ', pos=(200, 20))
            self.btn_mine = wx.Button(self, label='Start Mining', pos=(50, 60))
            self.btn_mine.id = START_MINE
            self.Bind(wx.EVT_BUTTON, self.OnBtnClick, self.btn_mine)
            self.title = f"Miner at port {sys.argv[1]}"
        if type == "s":
            self.btn_balance = wx.Button(self, label='Balance Update  ', pos=(200, 20))
            self.btn_balance.id = UPDATE_BAL
            self.Bind(wx.EVT_BUTTON, self.OnBtnClick, self.btn_balance)

            self.btn_hd = wx.Button(self, label='Get Headers', pos=(50, 60))
            self.btn_hd.id = GET_HEADER
            self.Bind(wx.EVT_BUTTON, self.OnBtnClick, self.btn_hd)
            self.title = f"Spv at port {sys.argv[1]}"

        self.to_label = wx.StaticText(self, label='Recipient ', pos=(50, 100))
        self.to_field = wx.TextCtrl(self, pos=(120, 100), size=(100, 30))

        self.amt_label = wx.StaticText(self, label='Amount ', pos=(50, 140))
        self.amt_field = wx.TextCtrl(self, pos=(120, 140), size=(100, 30))

        self.btn_txn = wx.Button(self, label='Make A Transaction', pos=(50, 180))
        self.btn_txn.id = MAKE_TXN
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, self.btn_txn, id=MAKE_TXN)

        self.logger = wx.TextCtrl(self, pos=(350, 20), size=(900, 200), style=wx.TE_MULTILINE | wx.TE_READONLY)

        redir = RedirectText(self.logger)
        sys.stdout = redir

    # def SetUp(self):
    #     vbox = wx.BoxSizer(wx.VERTICAL)
    #     self.SetSizer(vbox)
    #
    #     # add main widgets
    #     fgs = wx.FlexGridSizer(rows=len(self.widgets), cols=2, vgap=10, hgap=15)
    #     fgs.AddMany([(widget) for widget in self.widgets])
    #     vbox.Add(fgs, proportion=1, flag=wx.ALL | wx.EXPAND, border=20)

    def OnBtnClick(self, event):
        identifier = event.GetEventObject().id
        if identifier == JOIN_NETWORK:
            if self.type == "m":
                self.node = Miner.new(("localhost", int(sys.argv[1])))
            elif self.type == "s":
                self.node = SPVClient.new(("localhost", int(sys.argv[1])))
        elif identifier == START_MINE:
            self.node.mine()
            self.balance_value.SetLabel(str(self.node.get_own_balance())+"  ")
        elif identifier == GET_HEADER:
            self.node.get_blk_headers()
        elif identifier == UPDATE_BAL:
            balance = self.node.request_balance()
            self.balance_value.SetLabel(str(balance) + "  ")
        elif identifier == VERIFY_TXN:
            pass
            # self.node.verify_user_transaction(tx=)
        elif identifier == MAKE_TXN:
            receiver_port = self.to_field.GetValue()
            receiver_node = self.node.find_peer_by_addr(("localhost", int(receiver_port)))
            print(f"receiver node = {receiver_node}")
            receiver_pubkey = receiver_node["pubkey"]
            print(f"found receiver pubkey = {receiver_pubkey}")

            self.node.make_transaction(receiver=receiver_pubkey, amount=float(self.amt_field.GetValue()))


class RedirectText(object):
    def __init__(self, aWxTextCtrl):
        self.out=aWxTextCtrl

    def write(self, string):
        wx.CallAfter(self.out.WriteText, string)


def main():
    app = wx.App()
    MyFrame(None)
    app.MainLoop()


if __name__ == '__main__':
    main()

