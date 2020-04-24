import sys
import os
import time
from threading import Thread
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QAbstractItemView, QInputDialog, QMessageBox, QLabel, QPushButton, QTableWidgetItem, QMenu
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QUrl
from PyQt5.QtGui import QPixmap, QColor, QIntValidator
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from requests import get
from request.Action import Qpet

class Window(QMainWindow):
    '''加载主窗口'''
    '''加上多线程执行、优化UI界面'''
    def __init__(self):
        super().__init__()
        # 设置UI界面
        loadUi("UI/main.ui", self)
        # 设置状态栏一个信息标签，一个日志按钮
        self.label_status = QLabel("提示：登录即可使用")
        self.statusBar.addWidget(self.label_status, 5)
        pushButton_log = QPushButton("日志")
        self.statusBar.addWidget(pushButton_log, 1)

        # 实例化类，创建属性
        self.timer = QTimer(self)
        self.friendUI = Friend()
        self.mallUI = Mall()
        self.pet = None
        self.log = ""
        self.s = 0          # 持续秒数
        self.isLogin = False
        self.info = self.label_info.text()

        # 设置登录按钮菜单并绑定相应槽函数
        menu = QMenu()
        titles = ("扫码或密码", "Cookies")
        item = [menu.addAction(i) for i in titles]
        item[0].triggered.connect(self._loginRecode)
        item[1].triggered.connect(self._loginCK)
        self.pushButton_login.setMenu(menu)


        # 初始化表格界面
        self._initTable()
        # 绑定周期槽函数
        self.timer.timeout.connect(self.peroid)
        # 绑定接收自定义信号（固定子窗口、信息传递）
        self.mallUI.mall_signal.connect(self._move)
        self.friendUI.friend_signal.connect(self._move)
        self.mallUI.msg_signal.connect(self._status)
        self.friendUI.msg_signal.connect(self._status)
        # 绑定按钮槽函数
        pushButton_log.clicked.connect(self.logClicked)
        self.pushButton_boss.clicked.connect(self.boss)
        self.pushButton_friends.clicked.connect(self.friends)
        self.pushButton_mall.clicked.connect(self.mall)
        self.pushButton_collectedCoins.clicked.connect(lambda :Thread(target=self._collectedCoins).start())
        self.pushButton_collectedVigours.clicked.connect(lambda :Thread(target=self._collectedVigours).start())
        self.pushButton_feeds.clicked.connect(lambda :Thread(target=self._feeds).start())
        self.pushButton_items.clicked.connect(self.items)
        self.pushButton_outer.clicked.connect(self.outer)

    # 重写内置方法
    def moveEvent(self, e):
        self._move()

    def closeEvent(self, e):
        self.friendUI.close()
        self.mallUI.close()
        # 移除日志文件
        if os.path.exists("Data/.tmp.txt"):
            os.remove("Data/.tmp.txt")
        # 移除头像文件
        if os.path.exists("Data/avatar.png"):
            os.remove("Data/avatar.png")

    # 初始化界面，根据信息更新界面
    def initInfo(self):
        # 设置登录按钮状态
        self.pushButton_login.setEnabled(False)
        self.pushButton_outer.setEnabled(True)
        # 输出登录成功
        self._status("登录成功")
        # 设置头像
        image = get(self.pet.avatar)
        path = "Data/avatar.png"
        with open(path, "wb") as f:
            f.write(image.content)
        self.label_avatar.setPixmap(QPixmap(path))
        # 调用peroid函数，设置按钮状态&信息标签
        self.peroid()
        # 填充表格[{id, title, taked, progress[,]}]
        self.fillTable()

    # 内部使用方法
    def _move(self):
        self.friendUI.move(self.pos().x()+self.width(), self.pos().y())
        self.mallUI.move(self.pos().x()+self.width(), self.pos().y())

    def _status(self, text):
        '''
        @param text: 显示在状态栏的文本
        '''
        msg = "提示：{}"
        self.label_status.setText(msg.format(text.replace("\n","")))
        # 加入属性log中
        txt = "[{time}]：{text}\n"
        self.log += txt.format(
            time=time.strftime("%H:%M:%S", time.localtime()),
            text=text.replace("\n","")
            )

    # 初始化设置表格
    def _initTable(self):
        # 设置列宽
        width = (50, 150, 75, 145)
        for index,item in enumerate(width):
            self.tableWidget_missions.setColumnWidth(index, item)
        # 设置整行选择&禁止编辑&单一选择
        self.tableWidget_missions.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget_missions.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget_missions.setSelectionMode(QAbstractItemView.SingleSelection)
        # 设置表格右键菜单并连接槽函数
        self.menu = QMenu()
        titles = ("刷新","做任务","领奖励")
        self.menuItem = []
        for i in titles:
            item = self.menu.addAction(i)
            self.menuItem.append(item)
            if i == "刷新":
                self.menu.addSeparator()
        self.tableWidget_missions.customContextMenuRequested.connect(self.generateMenu)


    def fillTable(self):
        self.tableWidget_missions.setRowCount(0)
        '''填充表格'''
        if self.isLogin:
            items = [list(i.values()) for i in self.pet.listMissions]
            for i,row in enumerate(items):
                self.tableWidget_missions.insertRow(i)
                for j,column in enumerate(row):
                    item = QTableWidgetItem(str(column))
                    item.setTextAlignment(Qt.AlignCenter)
                    # 把完成任务奖励未领取的state栏设为红色
                    if not row[2] and row[3][0]==row[3][1] and j==2:
                        item.setForeground(QColor(255, 0, 0))
                    # 把任务完成奖励已领取的state设为灰色
                    if row[2]:
                        item.setForeground(QColor(139, 139, 139))
                    self.tableWidget_missions.setItem(i, j, item)

    # 表格右键菜单
    def generateMenu(self, pos):
        row = -1
        for i in self.tableWidget_missions.selectionModel().selection().indexes():
            row = i.row()
        if row >= 0:
            # 设置菜单是否可点击
            self.menuItem[1].setEnabled(self.pet.listMissions[row]["progress"][0]!=self.pet.listMissions[row]["progress"][1])
            self.menuItem[2].setEnabled(not self.pet.listMissions[row]["taked"] and self.pet.listMissions[row]["progress"][0]==self.pet.listMissions[row]["progress"][1])
            # 设置菜单弹出&设置点击操作
            pos.setY(pos.y()+int(self.menu.sizeHint().height()/2-10))
            action = self.menu.exec_(self.tableWidget_missions.mapToGlobal(pos))
            if action == self.menuItem[0]:
                # 刷新任务列表&页面信息
                self.pet.getListTask()
                self.pet.getInfo()
            elif action == self.menuItem[1]:
                # 做任务
                id = self.tableWidget_missions.item(row, 0).text()
                msg = self.pet.doTask(id)
                self._status(msg)
            elif action == self.menuItem[2]:
                # 领取奖励
                id = self.tableWidget_missions.item(row, 0).text()
                msg = self.pet.getReward(id)
                self._status(msg)
            self.fillTable()

    # 槽函数
    def logClicked(self):
        '''运行日志文本文档'''
        with open("Data/.tmp.txt", "w", encoding="utf-8") as f:
            f.write(self.log)
        os.startfile(os.path.join(os.getcwd(),"Data/.tmp.txt"))

    def peroid(self):
        '''周期执行'''
        # 设置信息标签
        info = self.info
        info = info.replace("昵称：","昵称：{}".format(self.pet.nick))
        info = info.replace("等级：","等级：{}".format(self.pet.level))
        info = info.replace("经验：","经验：{}".format(self.pet.experience))
        info = info.replace("金币：","金币：{}".format(self.pet.coins if len(str(self.pet.coins))<=6 else str(self.pet.coins)[0:len(str(self.pet.coins))-4]))
        info = info.replace("元气：","元气：{}".format(self.pet.vigours))
        info = info.replace('">储蓄罐：','{}">储蓄罐：{}'.format(" color: red;" if self.pet.bankCoins==self.pet.bankMaxCoins else "", self.pet.bankCoins))
        self.label_info.setText(info)
        # 设置按钮状态
        if self.pet.feedCountdown:
            m,s = divmod(self.pet.feedCountdown, 60)
            h,m = divmod(m, 60)
            feedsText = "{:0>2d}:{:0>2d}:{:0>2d}".format(h, m, s)
            if not self.pet.feedsFinish:
                self.pushButton_feeds.setEnabled(False)
        else:
            feedsText = "喂食"
        self.pushButton_feeds.setText(feedsText)
        if not self.pet.listVigours:
            self.pushButton_collectedVigours.setEnabled(False)
        if not self.pet.bankCoins:
            self.pushButton_collectedCoins.setEnabled(False)
        # 储蓄罐金币增加&喂食时间减少
        self.s += 1
        if not self.s%self.pet.perCoins:
            if self.pet.bankCoins < self.pet.bankMaxCoins:
                self.pet.bankCoins += 1
            else:
                self.pet.bankCoins = self.pet.bankMaxCoins
        if self.pet.feedCountdown:
            self.pet.feedCountdown -= 1

    def _loginCK(self):
        cookies, ok = QInputDialog.getText(self, "ck登录", "请输入qq登录的cookies") 
        if ok:
            self._login(cookies)

    def _loginRecode(self):
        # 扫码登录浏览器
        self.browser = MyWebEngineView()
        self.browser.resize(450, 300)
        self.browser.load(QUrl("https://xui.ptlogin2.qq.com/cgi-bin/xlogin?appid=549000912&daid=5&style=40&s_url=http%3A%2F%2Fqun.qzone.qq.com%2Fgroup"))
        self.browser.urlChanged.connect(self.urlChanged)
        self.browser.show()

    def urlChanged(self, url):
        if url.url() == "http://qun.qzone.qq.com/group":
            cookies = self.browser.getCookie()
            self.browser.close()
            self._login(cookies)


    def _login(self, cookies):
        # 判断是否成功获取了openid和openkey
        self._status("正在登录，请稍等。。。")
        self.pet = Qpet()
        if self.pet.getdata(cookies):
            thread = Thread(target=self.pet.login)
            thread.start()
            thread.join()
            pool = []
            pool.append(Thread(target=self.pet.getListTask))
            pool.append(Thread(target=self.pet.getBankCoins, args=(self.pet.userId,)))
            pool.append(Thread(target=self.pet.getListVigours, args=(self.pet.userId,)))
            pool.append(Thread(target=self.pet.viewFoods))
            pool.append(Thread(target=self.pet.clickStatus))
            pool.append(Thread(target=self.pet.getListgameXcx))
            # 依次执行线程并等待执行完毕
            for thread in pool:
                thread.start()
            for thread in pool:
                thread.join()
            self.isLogin = True

            Thread(target=self.initInfo).start()
            self.timer.start(1000)
        else:
            QMessageBox.information(self, "错误", "请检查输入cookies，是否输入正确或已过期。", QMessageBox.Yes)



    def boss(self):
        '''每日一键'''
        if self.isLogin:
            # 签到
            Thread(target=self._signIn).start()
            # 脱离被捕并洗澡
            thread = Thread(target=self._free)
            thread.start()
            thread.join()
            # 互动点击
            Thread(target=self._clickPlays).start()
            # 打工
            Thread(target=self._game).start()
            # 小程序打卡
            Thread(target=self._gameXcx).start()
            # 收元气
            Thread(target=self._collectedVigours).start()
            # 喂食速食喂食
            thread = Thread(target=self._feedsFinish)
            thread.start()
            thread.join()
            # 道具自动喂食
            Thread(target=self._useItem).start()
            # 做任务
            pass

    def _signIn(self):
        '''判断并签到'''
        if not self.pet.hasSign:
            msg = self.pet.signIn()
            if msg:
                self._status(msg)

    def _free(self):
        '''判断脱离被捕并洗澡'''
        if self.pet.isCapturedBy:
            msg = "脱离抓捕失败" if self.pet.capturesFree() else "脱离抓捕"
            self._status(msg)
        # 洗澡
        if self.pet.isDirty:
            msg = self.pet.useItem(12, self.pet.userId)
            self._status(msg)

    def _clickPlays(self):
        '''互动点击'''
        if self.pet.hasClick:
            gifts = []
            while self.pet.hasClick:
                self.pet.clickStatus()
                str = self.pet.clickPlays()
                if str:
                    gifts.append(str)
            msg = "互动点击获取奖励 [{}]".format("&".join(gifts))
            self._status(msg)

    def _game(self):
        '''打工'''
        coins = []
        flag = True
        while flag:
            coin = self.pet.game()
            if coin:
                coins.append(coin)
            else:
                if coins:
                    msg = "打工获得金币【{}】 {}".format(sum(coins), coins)
                    self._status(msg)
                flag = False

    def _gameXcx(self):
        '''小游戏打卡'''
        coins = []
        for item in self.pet.listGameXcx:
            if not item["todayCompleted"] and item["id"] != 1000:
                coin = self.pet.gameXcx(item["id"])
                if coin:
                    coins.append(coin)
        if coins:
            msg = "小程序获取金币【{}】 {}".format(sum(coins), coins)
            self._status(msg)

    def _feedsFinish(self):
        '''喂食--速食--喂食'''
        if not self.pet.hasFeed:
            self._feeds()
            time.sleep(1)
        if self.pet.hasFinished:
            if self.pet.feedsFinish():
                msg = "速食成功"
                self._status(msg)
                self._feeds()
            else:
                msg = "速食失败"
                self._status(msg)



    def _useItem(self):
        '''使用道具'''
        msg = self.pet.useItem(11, self.pet.userId)
        self._status(msg) 

    def friends(self):
        '''打开好友窗口'''
        if self.isLogin:
            # 发送pet类
            self.friendUI.pet_signal.emit(self.pet)
            self.friendUI.show()
            self.mallUI.close()


    def mall(self):
        '''打开商城窗口'''
        if self.isLogin:
            self.mallUI.pet_signal.emit(self.pet)
            self.mallUI.show()
            self.friendUI.close()

    def _collectedCoins(self):
        '''收取金币'''
        if self.isLogin:
            msg = self.pet.collectedCoins(self.pet.userId)
            self._status(msg)

    def _collectedVigours(self):
        '''领元气'''
        if self.isLogin:
            vigours = []
            if self.pet.listVigours:
                listVigours = self.pet.listVigours.copy()
                print("元气列表", self.pet.listVigours)
                for id in listVigours:
                    vigour = self.pet.collectedVigours(id, self.pet.userId)
                    vigours.append(vigour)
                msg = "收取元气总【{}】 {}".format(sum(vigours), vigours)
                self._status(msg)

    def _feeds(self):
        '''喂食'''
        if self.isLogin:
            # 倒着遍历食物列表
            id = 0
            for i in range(len(self.pet.listFoods)-1, -1, -1):
                if self.pet.listFoods[i]["ad"]:
                    id = self.pet.listFoods[i]["id"]
                    break
                elif self.pet.listFoods[i]["count"]:
                    id = self.pet.listFoods[i]["id"]
                    self.pet.listFoods[i]["count"] -= 1
                    break
            if not id: id = 3
            msg = self.pet.feeds(id)
            self._status(msg)

    def items(self):
        '''道具'''
        if self.isLogin:
            items = ("喂食加速卡[1000]", "爆米花喂食[6000]", "肥皂[240]")
            item, ok = QInputDialog.getItem(self, "道具", "选择道具使用", items, 0, False)
            if ok and item:
                id = items.index(item) + 10
                msg = self.pet.useItem(id, self.pet.userId)
                self._status(msg)

    def outer(self):
        '''登出'''
        self._status("【{name}】登出".format(name=self.pet.nick))
        self.isLogin = False
        self.pet = None
        self.timer.stop()
        self.pushButton_outer.setEnabled(False)
        self.pushButton_login.setEnabled(True)
        self.tableWidget_missions.setRowCount(0)
        self.label_info.setText("昵称：\n等级：\n经验：\n金币：\n元气：\n储蓄罐：")
        self.label_avatar.clear()
        self.pushButton_feeds.setText("喂食")
        self.pushButton_feeds.setEnabled(True)
        self.pushButton_collectedCoins.setEnabled(True)
        self.pushButton_collectedVigours.setEnabled(True)
        self.friendUI.close()
        self.mallUI.close()


class Friend(QWidget, QObject):
    '''加载好友窗口'''
    friend_signal = pyqtSignal()
    pet_signal = pyqtSignal(Qpet)
    msg_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        loadUi("UI/friend.ui", self)
        self.flag = False
        # 设置送礼按钮菜单
        menu = QMenu()
        titles = ("送1个", "送5个")
        action = [menu.addAction(i) for i in titles]
        self.pushButton_sendGifts.setMenu(menu)
        action[0].triggered.connect(lambda : self.sendGifts(False))
        action[1].triggered.connect(lambda : self.sendGifts(True))


        self.pet_signal.connect(self.getSignal)
        self.pushButton_boss.clicked.connect(self.boss)
        self.pushButton_captures.clicked.connect(self.captures)
        self.pushButton_stealCoins.clicked.connect(self.stealCoins)
        self.pushButton_stealVigours.clicked.connect(self.stealVigours)
        self.pushButton_sendGifts.clicked.connect(self.sendGifts)
        self.listWidget_friends.currentRowChanged.connect(self.clickItem)

    def moveEvent(self, e):
        self.friend_signal.emit()

    def closeEvent(self, e):
        self.flag = False

    def getSignal(self, pet):
        if not self.flag:
            self.flag = True
            self.pet = pet
            # 获取好友列表
            self.pet.getListFriends()
            # 填充列表&并选中第一行
            self.listWidget_friends.clear()
            self.listName = [i["nick"] for i in self.pet.listFriends]
            self.listWidget_friends.addItems(self.listName)
            self.listWidget_friends.setCurrentRow(0)

    def _captures(self, index):
        '''抓捕'''
        userId = self.pet.listFriends[index]["id"]
        msg = self.pet.capture(userId)
        self.msg_signal.emit(msg)

    def _stealCoins(self, index):
        '''偷金币'''
        userId = self.pet.listFriends[index]["id"]
        msg = self.pet.collectedCoins(userId)
        self.msg_signal.emit(msg)
        if msg.find("[")>0:
            try:
                coin = int(msg[msg.find("[")+1:msg.find("]")])
            except:
                coin = 0
        else:
            coin = 0
        return coin


    def _stealVigours(self, index):
        '''偷元气'''
        userId = self.pet.listFriends[index]["id"]
        # 如果没有元气列表，就开始查看并填写元气列表
        if not self.pet.listFriends[index].get("vigours"):
            self.pet.listFriends[index]["vigours"] = self.pet.getListVigours(userId)
        vigours = []
        listVigours = self.pet.listFriends[index]["vigours"].copy()
        for id in listVigours:
            vigour = self.pet.collectedVigours(id, userId)
            vigours.append(vigour)
        msg = "收取元气【{}】 {}".format(sum(vigours), vigours)
        self.msg_signal.emit(msg)
        return sum(vigours)

    def _sendGifts(self, index, hastotal):
        '''送礼物'''
        if hastotal:
            flag = True
            while flag:
                msg = self.pet.useItem(50, self.pet.listFriends[index]["id"])
                self.msg_signal.emit(msg)
                time.sleep(1)
                if msg == "今日赠送已达上限":
                    flag = False
                elif msg == "操作太快了":
                    time.sleep(1)
        else:
            msg = self.pet.useItem(50, self.pet.listFriends[index]["id"])
            self.msg_signal.emit(msg)


    def _boss(self):
        '''遍历好友一键偷取'''
        coins = []
        vigours = []
        for index,item in enumerate(self.pet.listFriends):
            # 偷金币
            if item["hasCoins"]:
                coin = self._stealCoins(index)
                coins.append(coin)
            # 偷元气
            if item["hasUncollectVigours"]:
                vigour = self._stealVigours(index)
                vigours.append(vigour)
            time.sleep(1)
        msg = "遍历好友完成，共获取[{}]金币、[{}]元气".format(sum(coins), sum(vigours))
        self.msg_signal.emit(msg)

    def _clickItem(self, i):
        userId = self.pet.listFriends[i]["id"]
        coins = self.pet.listFriends[i].get("coins", 0)
        if not coins:
            coins = self.pet.getBankCoins(userId)
            self.pet.listFriends[i]["coins"] = coins
        vigoursNum = len(self.pet.listFriends[i].get("vigours", []))
        if not vigoursNum:
            vigours = self.pet.getListVigours(userId)
            self.pet.listFriends[i]["vigours"] = vigours
            vigoursNum = len(vigours)

        info = "昵称：{nick}\n等级：{level}\n金币：{coins}/{maxCoins}\n元气：{vigoursNum}块".format(
            nick=self.listName[i],
            level=self.pet.listFriends[i]["pet"]["level"],
            coins=coins[0],
            maxCoins=coins[1],
            vigoursNum=vigoursNum
            )
        self.label_info.setText(info)
        self.pushButton_captures.setEnabled(self.pet.listFriends[i]["canCapture"])
        self.pushButton_stealCoins.setEnabled(self.pet.listFriends[i]["hasCoins"])
        self.pushButton_stealVigours.setEnabled(self.pet.listFriends[i]["hasUncollectVigours"])

    def clickItem(self, index):
        Thread(target=self._clickItem, args=(index,)).start()

    def boss(self):
        Thread(target=self._boss).start()

    def sendGifts(self, hastotal):
        index = self.listWidget_friends.currentRow()
        Thread(target=self._sendGifts, args=(index, hastotal)).start()

    def captures(self):
        index = self.listWidget_friends.currentRow()
        Thread(target=self._captures, args=(index,)).start()

    def stealCoins(self):
        index = self.listWidget_friends.currentRow()
        Thread(target=self._stealCoins, args=(index,)).start()

    def stealVigours(self):
        index = self.listWidget_friends.currentRow()
        Thread(target=self._stealVigours, args=(index,)).start()



class Mall(QWidget, QObject):
    '''加载商店窗口'''
    mall_signal = pyqtSignal()
    pet_signal = pyqtSignal(Qpet)
    msg_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        loadUi("UI/mall.ui", self)
        self.lineEdit_goodsId.setValidator(QIntValidator())
        # 窗口是否被展示
        self.flag = False

        # 链接槽函数
        self.pet_signal.connect(self.getSignal)
        self.pushButton_boss.clicked.connect(self.boss)
        self.pushButton_exchange.clicked.connect(lambda :Thread(target=self._exchange).start())
        self.pushButton_bargain.clicked.connect(lambda :Thread(target=self._bargain, args=(False,)).start())
        self.pushButton_record.clicked.connect(self._reward)
        self.pushButton_goodsId.clicked.connect(self._goodsId)

    # 重写moveEvent事件
    def moveEvent(self, e):
        self.mall_signal.emit()

    def closeEvent(self, e):
        self.flag = False

    def getSignal(self, pet):
        if not self.flag:
            self.flag = True
            self.pet = pet
            # 登录获取登录信息
            msg = self.pet.mallLogin()
            if msg:
                self.msg_signal.emit(msg)
            # 判断并签到
            if not self.pet.mallHasSign:
                msg = self.pet.mallSignIn()
                self.msg_signal.emit(msg)
            # 获取商品列表
            msg = self.pet.getGoods()
            if msg:
                self.msg_signal.emit(msg)
            else:
                # 简化商品列表，只包括价格小于5位数的商品。并转换格式设置为标签提示
                self.listSimpleGoods = [{key: value for key,value in item.items()} for item in self.pet.listGoods if len(str(item["price"]))<=5]
                txt = ["--".join(item.values()) for item in self.listSimpleGoods]
                # 每三组商品占一行，设置提示信息
                msg = ""
                for index,item in enumerate(txt):
                    if (index+1)%3:
                        msg += item+"、"
                    elif index == len(txt)-1:
                        msg += item
                    else:
                        msg += item+"\n"
                self.label.setToolTip(msg)

    def _lookAd(self):
        '''看广告'''
        flag = True
        while flag:
            dictMsg = self.pet.mallAd()
            print(dictMsg)
            if not dictMsg["msg"]:
                msg = "看广告进度【{}/{}】".format(dictMsg["progress"][0], dictMsg["progress"][1])
                self.msg_signal.emit(msg)
                if dictMsg["progress"][0]==dictMsg["progress"][1]:
                    flag = False
            else:
                msg = dictMsg["msg"]
                self.msg_signal.emit(msg)
                if msg == "已达每日播放上限":
                    flag = False


    def _luckDraw(self):
        '''幸运抽奖'''
        gifts = []
        flag = True
        while flag:
            msg = self.pet.mallLuckDraw()
            if msg == "每天只可抽奖20次":
                flag = False
                if gifts:
                    self.msg_signal.emit("今日幸运抽奖 {}".format("、".join(gifts)))
            else:
                gifts.append(msg)


    def _bargain(self,isfinish):
        '''砍价'''
        if isfinish:
            msg = self.pet.mallBargain(51, 10)
            self.msg_signal.emit(msg)
        else:
            id = self.lineEdit_goodsId.text()
            if id:
                for i in range(10):
                    msg = self.pet.mallBargain(id, i+1)
                    self.msg_signal.emit(msg)
                    if msg == "库存不足(1)":
                        break
            else:
                QMessageBox.information(self, "错误", "请在商品输入框输入商品id", QMessageBox.Yes)

    def _exchange(self):
        '''兑奖'''
        id = self.lineEdit_goodsId.text()
        if id:
            msg = self.pet.mallExchange(id)
            self.msg_signal.emit(msg)
        else:
            QMessageBox.information(self, "错误", "请在商品输入框输入商品id", QMessageBox.Yes)

    def _reward(self):
        '''历史订单'''
        msg = self.pet.mallRecord()
        if msg:
            self.msg_signal.emit(msg)
        else:
            txt = "\n".join(["----".join(item.values()) for item in self.pet.listRecord])
            QMessageBox.about(self, "历史订单", txt)

    def _goodsId(self):
        '''商品id'''
        txt = ["--".join(item.values()) for item in self.pet.listGoods]
        # 每三组商品占一行，设置提示信息
        msg = ""
        for index,item in enumerate(txt):
            if (index+1)%2:
                msg += item+"、"
            elif index == len(txt)-1:
                msg += item
            else:
                msg += item+"\n"
        QMessageBox.about(self, "商品信息(id--name--price)", msg)


    def boss(self):
        '''一键商店'''
        Thread(target=self._lookAd).start()
        Thread(target=self._luckDraw).start()
        Thread(target=self._bargain, args=(True,)).start()


class MyWebEngineView(QWebEngineView):
    def __init__(self):
        super().__init__()
        self.cookies = {}
        # 绑定cookie被添加的信号槽
        QWebEngineProfile.defaultProfile().cookieStore().cookieAdded.connect(self.onCookieAdd)

    # 槽函数
    def onCookieAdd(self, cookie):
        key = cookie.name().data().decode('utf-8')
        value = cookie.value().data().decode('utf-8')
        self.cookies[key] = value

    def getCookie(self):
        '''获取拼接后储存cookie'''
        return '; '.join(["=".join(item) for item in self.cookies.items()])



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec_()
