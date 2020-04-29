import random
import time
import requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Qpet():
    '''请求接口'''

    def __init__(self):
        self._openid = None
        self._openkey = None
        self._token = None
        self._session = None
        self.userId = None

        self.nick = None            # 用户昵称
        self.avatar = None          # 头像网址
        self.level = 0              # 等级
        self.experience = 0         # 经验
        self.coins = 0              # 金币
        self.vigours = 0            # 元气
        self.feedCountdown = 0      # 进食剩余时间（s）
        self.bankCoins = 0          # 储蓄罐金币
        self.bankMaxCoins = 0       # 储蓄罐最大金币数
        self.perCoins = 0           # 储蓄罐每秒金币数
        self.listVigours = []       # 元气id列表[id]
        self.listFoods = []         # 食物列表[{id, name, count, ad}]
        self.listMissions = []      # 任务列表{id, title, taked, progress[,]}
        self.listFriends = []       # 好友列表
        self.listGoods = []         # 商品列表{id, name, price}
        self.listRecord = []        # 往期兑换订单列表{creat_time, name}
        self.listGameXcx = []       # 小程序完成列表

        self.hasFeed = False        # 是否正在进食
        self.hasFinished = False    # 是否可以速食
        self.isCapturedBy = False   # 是否被抓
        self.isDirty = False        # 是否脏
        self.hasClick = True        # 是否还能点击
        self.hasSign = False        # 是否已签到
        self.mallHasSign = False    # 商店是否签到

        self.urls = {
            "LOGIN": "https://qqpet.jwetech.com/api/authorizations",            # 获取token
            "PETINFO": "https://qqpet.jwetech.com/api/users/profile",           # 宠物信息
            "SIGNIN": "https://qqpet.jwetech.com/api/v2/daily_signs",           # 签到
            "COLLECTEDCOINS": "https://qqpet.jwetech.com/api/counters",         # 领取金币、偷取金币
            "FREE": "https://qqpet.jwetech.com/api/captures/free",              # 脱离捕获
            "ITEMS": "https://qqpet.jwetech.com/api/cards/{}",                  # 使用道具、送礼物
            "VIEWFOODS": "https://qqpet.jwetech.com/api/user_foods",            # 查询食物信息
            "FEEDS": "https://qqpet.jwetech.com/api/pet_feeds",                 # 喂食
            "FEEDSFINISH": "https://qqpet.jwetech.com/api/pet_feeds/finish",    # 速食
            "VIGOURS": "https://qqpet.jwetech.com/api/vigours",                 # 元气列表、收元气、偷元气
            "GAME": "https://qqpet.jwetech.com/api/minigames",                  # 做游戏
            "GAMEXCX": "https://qqpet.jwetech.com/api/games",                   # 浏览小程序
            "TASK": "https://qqpet.jwetech.com/api/daily_missions",             # 任务列表、做任务、领取任务奖励
            "CLICKPLAYS": "https://qqpet.jwetech.com/api/click_plays",          # 互动奖励
            "DECORATE": "https://qqpet.jwetech.com/api/dresses",                   # 购买装饰

            "FRIENDLSIT": "https://qqpet.jwetech.com/api/rankings",             # 获取好友列表
            # "FRIENDINFO": "https://qqpet.jwetech.com/api/users/{}",             # 获取好友信息
            "CAPTURE": "https://qqpet.jwetech.com/api/captures",                # 抓捕好友

            "MALL_LOGIN": "https://qqstore.jwetech.com/mall/login/index",       # 登录商店
            "MALL_GOODS": "http://qqstore.jwetech.com/mall/award/list",         # 获取商品id
            "MALL_SIGNIN": "https://qqstore.jwetech.com/mall/vitality/sign-in", # 商店签到
            "MALL_AD": "https://qqstore.jwetech.com/guess/home/ad{}",           # 商店广告操作
            "MALL_LUCKDRAW": "https://qqstore.jwetech.com/mall/vitality/play",  # 元气抽奖
            "MALL_BARGAIN": "https://qqstore.jwetech.com/mall/award/bargain",   # 砍价
            "MALL_EXCHANGE": "https://qqstore.jwetech.com/mall/award/exchange", # 兑奖
            "MALL_RECORD": "https://qqstore.jwetech.com/mall/vitality/record"   # 获取订单
        }
        self.headers = {
            "Authorization": "Bearer {}".format(self._token),
            "Content-Type": "application/json"
            # "User-Agent": "Mozilla/5.0 (Linux; U; Android 8.0.0; zh-cn; Mi Note 2 Build/OPR1.170623.032) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/61.0.3163.128 Mobile Safari/537.36 XiaoMi/MiuiBrowser/10.1.1"
        }


    def _request(self, url, method='GET', params=None, data=None, json=None, headers=None):
        '''
        @param url: 请求地址
        @param method: 请求方式
        @param data: from表单请求参数
        @param json: json格式请求参数
        @return: 返回数据
        @请求默认重定向
        '''
        if method.upper() == "GET":
            res = requests.get(url, params=params, headers=headers, 
                               verify=False, allow_redirects=True)
        elif method.upper() == "POST":
            res = requests.post(
                url, data=data, json=json, headers=headers, verify=False, allow_redirects=True)
        elif method.upper() == "PUT":
            res = requests.put(url, json=json, headers=headers, verify=False, allow_redirects=True)
        res.encoding = "utf-8"
        return res

    def getdata(self, cookies):
        '''
        @return: 是否成功获取openid和openkey
        '''
        if "=" in cookies and ";" in cookies:
            cookies = {item.split("=")[0]: item.split("=")[1]
                            for item in cookies.strip().split("; ")}
            res = requests.get("https://1108057289.urlshare.cn/home?_proxy=1&app_display=2&_wwv=2048&_wv=2147628839&app_display=2&src=518",
                               cookies=cookies)
            data = res.content.decode()

            i = data.find(r'"openid":"')+10
            j = data.find(r'"openkey":"')+11
            self._openid = data[i:i+32]
            self._openkey = data[j:j+32]
            if self._openid.isalnum() and self._openkey.isalnum():
                return True
        return False

    def login(self):
        data = {
            "data": {"openid": self._openid, "openkey": self._openkey},
            "provider": "qzone"
        }
        res = requests.post(self.urls["LOGIN"], json=data, verify=False)
        self._token = res.json()["token"]
        self.headers["Authorization"] = "Bearer {}".format(self._token)
        print("token：", self._token)
        self.userId = res.json()["id"]
        self.coins = res.json()["coins"]
        self.vigours = res.json()["vigours"]
        self.nick = res.json()["nick"]
        self.avatar = res.json()["avatar"]
        self.level = res.json()["pet"]["level"]
        self.experience = res.json()["pet"]["expirenece"]
        self.feedCountdown = res.json()["pet"]["feed"]["countdown"]
        self.hasFeed = bool(res.json()["pet"]["feed"]["food"])
        self.hasFinished = bool(res.json()["pet"]["feed"]["ad"])
        self.isCapturedBy = bool(res.json()["pet"]["isCapturedBy"])
        self.isDirty = bool(res.json()["pet"]["state"][0] if res.json()[
                            "pet"]["state"] else 0)
        # self.captureCount = res.json()p["captureCount"]       #剩余抓捕次数

    def getInfo(self):
        res = self._request(self.urls["PETINFO"], headers=self.headers)
        self.userId = res.json()["id"]
        self.coins = res.json()["coins"]
        self.vigours = res.json()["vigours"]
        self.nick = res.json()["nick"]
        self.avatar = res.json()["avatar"]
        self.level = res.json()["pet"]["level"]
        self.experience = res.json()["pet"]["expirenece"]
        self.feedCountdown = res.json()["pet"]["feed"]["countdown"]
        self.hasFeed = bool(res.json()["pet"]["feed"]["food"])
        self.hasFinished = bool(res.json()["pet"]["feed"]["ad"])
        self.isCapturedBy = bool(res.json()["pet"]["isCapturedBy"])
        self.isDirty = bool(res.json()["pet"]["state"][0] if res.json()[
                            "pet"]["state"] else 0)

    def signIn(self):
        '''
        @return: 未签到，奖品信息；已签到，None
        '''
        # 判断是否签到
        res = self._request(self.urls["SIGNIN"], headers=self.headers)
        day = res.json()["day"]
        self.hasSign = bool(res.json()["sign"][day])
        if not self.hasSign:
            # 签到
            json = {
                "ad": True,
                "day": "{}".format(day)
            }
            res = self._request(self.urls["SIGNIN"], method="POST",
                           json=json, headers=self.headers)
            if res.json():
                name = []
                for i in res.json()["items"]:
                    if i.get("type") == "coin":
                        self.coins += i["count"]
                    elif i.get("type") == "vigour":
                        self.vigours += i["count"]
                    name.append(i["name"])
                gifts = "签到奖励 [{}]".format("&".join(name))
                self.hasSign = True
                return gifts
            else:
                return
 
    def capturesFree(self):
        '''
        脱离捕获
        '''
        res = self._request(self.urls["FREE"], method="POST", headers=self.headers)
        self.isCapturedBy = bool(res.json()["pet"]["isCapturedBy"])
        return self.isCapturedBy

    def getBankCoins(self, userId):
        '''
        @param userId: 获取金币的用户id
        @return: (储蓄罐金币数, 最大金币数)
        '''
        params = {"userId": userId}
        res = self._request(self.urls["COLLECTEDCOINS"],
                       params=params, headers=self.headers)
        if userId == self.userId:
            self.bankCoins = res.json()["count"]
            self.bankMaxCoins = res.json()["maximum"]
            self.perCoins = res.json()["secondsPerCoin"]
        return (res.json()["count"], res.json()["maximum"])

    def collectedCoins(self, userId):
        '''
        @param userId: 获取金币的用户id
        @return: 信息
        '''
        json = {
            "userId": userId,
            "ad": True
        }
        res = self._request(self.urls["COLLECTEDCOINS"],
                       method="POST", json=json, headers=self.headers)
        if res.json().get("code"):
            if userId == self.userId:
                nick = "自己"
            else:
                for item in self.listFriends:
                    if item["id"] == userId:
                        nick = item["nick"]
                        break
            return "【{}】{}".format(nick, res.json()["message"])
        else:
            self.coins = res.json()["coins"]
            collectedCoins = res.json()["collected"]
            if userId == self.userId:
                self.bankCoins = 0
                nick = "自己"
                # 遍历任务修改金币任务进度
                for item in self.listMissions:
                    if int(item["id"]) == 100:
                        item["progress"][1] += collectedCoins
                        if item["progress"][1] > item["progress"][0]:
                            item["progress"][1] == item["progress"][0]
                        print("金币任务",item["progress"])
                        break
            else:
                # 遍历friends修改hasCoins
                for item in self.listFriends:
                    if item["id"] == userId:
                        item["hasCoins"] = False
                        nick = item["nick"]
                        break
            return "在【{}】家获取[{}]金币".format(nick, collectedCoins)

    def getListVigours(self, userId):
        '''
        获取待收取元气列表
        @param: 用户的userid
        @return: 由所有id的列表
        '''
        params = {"userId": userId} if userId != self.userId else None
        res = self._request(self.urls["VIGOURS"],
                       params=params, headers=self.headers)
        list = [i["id"] for i in res.json()["uncollectedVigours"]]
        if userId == self.userId:
            self.listVigours = list
        return list

    def collectedVigours(self, id, userId):
        '''
        @param userId: 用户id
        @param id: 元气id
        @return: 元气数
        '''
        url = self.urls["VIGOURS"] + "/" + str(id)
        json = {
            "userId": userId,
            "ad": True
        }
        countdown = True
        while countdown:
            res = self._request(url, method="PUT", json=json, headers=self.headers)
            countdown = res.json().get("countdown", 0)
        vigours = res.json().get("count", 0)
        self.vigours += vigours
        if userId == self.userId:
            nick = "自己"
            self.listVigours.remove(id)
        else:
            # 遍历friends修改hasUncollectVigours
            for item in self.listFriends:
                if item["id"] == userId:
                    item["hasUncollectVigours"] = False
                    break
        return vigours

    def clickStatus(self):
        '''
        更新hasClick是否还有奖励
        '''
        res = self._request(self.urls["CLICKPLAYS"], headers=self.headers)
        if res.json().get("code"):
            self.hasClick = False
        else:
            self.hasClick = True

    def clickPlays(self):
        '''
        @return: 奖品名
        需要和clickStatus()一同使用
        '''
        res = self._request(self.urls["CLICKPLAYS"],
                       method="POST", json={}, headers=self.headers)
        if res.json():
            type = res.json()["type"]
            if type == "vigour":
                self.vigours += res.json()["count"]
            elif type == "coins":
                self.coins += res.json()["count"]
            elif type == "expirenece":
                self.experience += res.json()["count"]
            return res.json()["name"]

    def useItem(self, id, userId):
        '''
        使用道具
        @param userId: 用户id
        @param id: 道具id。加速(10)[1000]、自动(11)[6000]、洗澡(12)[240]；亲密草(50)[1000]
        @return: 文本信息
        '''
        json = {"userId": userId}
        res = self._request(self.urls["ITEMS"].format(
            id), method="PUT", json=json, headers=self.headers)
        items = ("喂食加速卡", "爆米花喂食", "肥皂", "亲密草")
        if userId == self.userId:
            name = "自己"
        else:
            for i in self.listFriends:
                if i["id"] == userId:
                    name = i["nick"]
                    break
        if res.json().get("code"):
            return res.json()["message"]
        else:
            if id == 10:
                self.feedCountdown -= 3600
                msg = ""
            elif id == 50:
                msg = " 亲密度[{}]".format(res.json()["cp"]["points"])
            else:
                msg = ""
            coin = res.json()["cost"]
            self.coins -= coin
            return "对【{}】使用[{}]，消耗{}金币{}".format(name, items[id-10 if id != 50 else 3], coin, msg)

    def viewFoods(self):
        '''
        查询食物
        @return: 食品数量的列表[{id, name, count, ad}]
        '''
        res = self._request(self.urls["VIEWFOODS"], headers=self.headers)
        self.listFoods = [{key: value for key,value in item.items() if key=="id" or key=="name" or key=="count" or key=="ad"} for item in res.json()["foods"]]

    def feeds(self, id):
        '''
        @param id: 食物id。爆米花(1)、招财饺子(2)、团圆汤圆(3)
        @return: 文字说明
        '''
        json = {
            "foodId": id,
            "ad": True
        }
        res = self._request(self.urls["FEEDS"], method="POST",
                       json=json, headers=self.headers)
        if res.json().get("code"):
            return res.json()["message"]
        else:
            price = ("480", "480[萌宠贵族]", "2000")
            self.feedCountdown = 14400
            self.hasFeed = True
            return "投喂了一个{name}（{price}）".format(
                name=self.listFoods[id-1]["name"],
                price=price[id-1]
                )

    def feedsFinish(self):
        '''速食'''
        res = self._request(self.urls["FEEDSFINISH"],
                       method="POST", json={}, headers=self.headers)
        if len(res.text) < 300:
            self.feedsFinish = False
            return True
        else:
            return False

    def game(self):
        '''
        打工，企鹅店员
        @return: 金币数
        '''
        json = {"game": "mcd"}
        res = self._request(self.urls["GAME"], method="POST",
                       json=json, headers=self.headers)
        gameid = res.json().get("id", 0)
        if gameid:
            url = self.urls["GAME"] + "/" + str(gameid)
            json = {
                "game": "mcd",
                "score": random.randint(80, 99),
                "ad": False
            }
            res = self._request(url, method="PUT", json=json, headers=self.headers)
            coins = sum(res.json()["coins"])
            self.coins += coins
            return coins
        else:
            print("打工", res.json()["message"])
            return 0

    def getListgameXcx(self):
        '''
        获取小程序今日打卡列表[{id, title, todayCompleted}]
        '''
        res = self._request(self.urls["GAMEXCX"], headers=self.headers)
        if res.json().get("code"):
            msg = res.json()["message"]
            return msg
        else:
            self.listGameXcx = [{key:value for key,value in item.items() if key=="id" or key=="title" or key=="todayCompleted"} for item in res.json()["games"]]

    def gameXcx(self, id):
        '''
        打工，小程序
        @param id: 小程序id。夺宝赛车场(1000)、K歌夺宝(1001)、魔力碎片(1002)、爱江山更爱美人(1003)
        @return: 获取金币数
        '''
        if int(id) == 1000:
            url = "https://microqqmall.crosscp.com/mall/vitality/game-mission"
            data = {
                "pet_id": self.userId,
                "game_id": 1000,
                "user_id": 11667,
                "sessid": self._session,
                "version": "2.12.0",
                "source": "qq",
                "from": 1
            }
            res = self._request(url, method="POST",data=data, headers=self.headers)
        else:
            json = {"gameId": str(id)}
            res = self._request(self.urls["GAMEXCX"], method="POST",
                       json=json, headers=self.headers)
        if res.json():
            coins = res.json().get("coins", 0)
            self.coins += coins
            return coins
        else:
            return 0

    def getListTask(self):
        '''
        更新任务列表[{id, title, taked, progress[,]}]
        '''
        res = self._request(self.urls["TASK"], headers=self.headers)
        if res.json().get("code"):
            print(res.json()["message"])
        else:
            list = res.json()["missions"]
            self.listMissions = [{key: value for key,value in item.items() if key=="id" or key=="title" or key=="taked" or key=="progress"} for item in list]

    def doTask(self, id):
        '''
        做任务
        @param id: 任务id。收取达人(100)、喂食达人(101)、打工达人(102)、抓捕达人(103)、※广告达人(105※)、每日金币(106※)、运动达人(107※)、游戏达人(108※)、\
            碎片达人(109※)、夺宝赛车场(110)、魔力碎片(111)、K歌夺宝(112)、K歌达人(113)、走路达人(114)、厘米秀达人(115※)
        @return: 信息
        '''
        if int(id) >= 104:
            url = self.urls["TASK"] + "/" + str(id)
            res = self._request(url, method="PUT", json={}, headers=self.headers)
            for item in self.listMissions:
                if item["id"] == int(id):
                    title = item["title"]
                    item["progress"] = res.json()["progress"]
                    break
            msg = "【{}】 完成进度（{}/{}）".format(
                res.json()["title"],
                res.json()["progress"][0],
                res.json()["progress"][1]
            )
            return msg
        else:
            return "这个任务需要自己完成"


    def getReward(self, id):
        '''
        领取任务奖励
        @param id: 任务id
        @return: 信息
        '''
        json = {"missionId": int(id)}
        res = self._request(self.urls["TASK"], method="POST",
                       json=json, headers=self.headers)
        if res.json().get("code"):
            return res.json()["message"]
        else:
            self.experience = res.json()["pet"]["expirenece"]
            self.coins += res.json().get("coins", 0)
            self.isCapturedBy = bool(res.json()["pet"]["isCapturedBy"])
            self.isDirty = bool(res.json()["pet"]["state"][0] if res.json()[
                                "pet"]["state"] else 0)
            for item in self.listMissions:
                if item["id"] == int(id):
                    title = item["title"]
                    item["taked"] = True
                    break
            msg = "【{title}】 {msg1}{msg2}"
            if res.json().get("expirenece"):
                msg1 = "获取[{}]经验 ".format(res.json()["expirenece"])
            else:
                msg1 = ""
            if res.json().get("coins"):
                msg2 = "获取[{}]金币".format(res.json()["coins"])
            else:
                msg2 = ""
            return msg.format(title=title, msg1=msg1, msg2=msg2)

    def payDecoration(self, id):
        '''
        购买衣服
        @param id: 装饰id
        @return: 兑换信息
        '''
        json = {"dressId": str(id)}
        res = self._request(self.urls["DECORATE"], method="POST",
            json=json, headers=self.headers)
        if res.json().get("code"):
            msg = res.json()["message"]
        else:
            expireAt = res.json()["dresses"][0]["expiredAt"][:10]
            msg = "购买成功，{expireAt}到期"
        return msg


    def getListFriends(self):
        '''
        更新好友列表[{id, nick, avatar, pet{level}, hasCoins, hasUncollectVigours, canCapture}]
        '''
        res = self._request(self.urls["FRIENDLSIT"], headers=self.headers)
        self.level = res.json()["me"]["pet"]["level"]
        self.listFriends = res.json()["friends"]

    def capture(self, userId):
        '''
        随机抓捕打工类型。烤鱼(0)、挖矿(1)、淘金(2)
        @param userid: 好友id
        @return: 信息
        '''
        id = random.randint(0, 2)
        json = {
            "userId": userId,
            "type": id,
            "ad": True
        }
        res = self._request(self.urls["CAPTURE"], method="POST",
                       json=json, headers=self.headers)
        if res.json().get("message"):
            return res.json()["message"]
        else:
            # 遍历找出friends列表对应键值
            for item in self.listFriends:
                if item["id"] == userId:
                    item["canCapture"] = False
                    break
            type = ("烤鱼", "挖矿", "淘金")
            msg = "成功抓捕 【{}({})】 {}".format(
                res.json()["user"]["nick"],
                res.json()["pet"]["level"],
                type[id]
            )
            return msg

    def mallLogin(self):
        '''
        登录商店，获取session参数
        @return: 相关信息或True
        '''
        data = {
            "openudid": self.userId,
            "token": self._token,
            "nick": self.nick,
            "avatar": self.avatar
        }
        res = self._request(self.urls["MALL_LOGIN"],
                       method="POST", data=data)
        if res.json()["iRet"] == 1:
            self._session = res.json()["data"]["sessid"]
            self.vigours = res.json()["data"]["amount"]
            self.mallHasSign = bool(res.json()["data"]["isSignIn"])
        else:
            return res.json()["sMsg"]

    def mallSignIn(self):
        '''
        商店签到
        @return: 信息
        '''
        data = {
            "type": 1,
            "openudid": self.userId,
            "token": self._token,
            "sessid": self._session
        }
        res = self._request(self.urls["MALL_SIGNIN"], method="POST", data=data)
        if res.json()["iRet"] == 1:
            amount = res.json()["data"]["amount"]
            self.vigours += amount
            return "商店签到获得{}元气".format(amount)
        else:
            return res.json()["sMsg"]

    def getGoods(self):
        '''
        更新商品列表[{id, name, price}]
        '''
        data = {
            "openudid": self.userId,
            "token": self._token,
            "sessid": self._session
        }
        res = self._request(self.urls["MALL_GOODS"], method="POST", data=data)
        if res.json()["iRet"] == 1:
            self.listGoods = [{key if key!="abbreviation" else "name": value for key, value in item.items() if key == "id" or key ==
                               "abbreviation" or key == "price"} for item in res.json()["data"]["list"]]
        else:
            return res.json()["sMsg"]

    def mallAd(self):
        '''
        看广告
        @return: {msg,progress}
        '''
        url = {"play": self.urls["MALL_AD"].format("-play"),
               "close": self.urls["MALL_AD"].format("-close")}
        data = {
            "ad_type": 0,
            "openudid": self.userId,
            "token": self._token,
            "sessid": self._session
        }
        # 打开广告
        res = self._request(url["play"], method="POST", data=data)
        if res.json()["iRet"] == 1:
            progress = [res.json()["data"]["play_times"],
                        res.json()["data"]["limit"]]
            time.sleep(1)
        else:
            msg = res.json()["sMsg"]
            return {"msg": msg, "progress": []}
        # 关闭广告
        res = self._request(url["close"], method="POST", data=data)
        if res.json()["iRet"] == 1:
            self.vigours += 10
            progress[0] += 1
            msg = ""
        else:
            msg = res.json()["sMsg"]
        return {"msg": msg, "progress": progress}

    def mallLuckDraw(self):
        '''
        幸运抽奖
        @return: 奖品名或错误信息
        '''
        data = {
            "openudid": self.userId,
            "token": self._token,
            "sessid": self._session
        }
        res = self._request(self.urls["MALL_LUCKDRAW"], method="POST", data=data)
        if res.json()["iRet"] == 1:
            gift = (500000, 50, 1000, 30, 25, 100, 5, 10000, 25)
            gid = res.json()["data"]["gid"]
            self.vigours += gift[gid-1]
            return "{}元气".format(gift[gid-1])
        else:
            return res.json()["sMsg"]

    def mallBargain(self, id, times):
        '''
        @param id: 砍价商品id
        @param times: 砍价次数，从1开始
        @return: 相关信息
        '''
        data = {
            "id": id,
            "times": times,
            "openudid": self.userId,
            "token": self._token,
            "sessid": self._session
        }
        res = self._request(self.urls["MALL_BARGAIN"], method="POST", data=data)
        if res.json()["iRet"] == 1:
            bargain = res.json()["data"]["bargain"]
            # 遍历找出listGoods列表对应键值
            name = "[商品]"
            price = "[价格]"
            for item in self.listGoods:
                if int(item["id"]) == int(id):
                    name = item["name"]
                    price = item["price"]
                    break
            msg = "{name}({price})砍价[{times}]至{bargain}元气 {msg}"
            if res.json()["data"]["bargain_msg"] == "恭喜获得100元气":
                self.vigours += 100
            return msg.format(
                name=name,
                price=price,
                times=times,
                bargain=bargain,
                msg=res.json()["data"]["bargain_msg"]
                )
        else:
            return res.json()["sMsg"]


    def mallExchange(self, id):
        '''
        @param id: 兑换奖品的id
        @return: 相关信息
        '''
        data = {
            "id": id,
            "openudid": self.userId,
            "token": self._token,
            "sessid": self._session
        }
        res = self._request(self.urls["MALL_EXCHANGE"], method="POST", data=data)
        if res.json()["iRet"] == 1:
            # 遍历找出listGoods列表对应键值
            for item in self.listGoods:
                if item["id"] == id:
                    name = item["name"]
                    price = item["price"]
                    break
            self.vigours -= int(price.replace("万", "0000") if "万" in price else price)
            msg = "消耗{price}元气 兑换了{name}"
            return msg.format(price=price, name=name)
        else:
            return res.json()["sMsg"]

    def mallRecord(self):
        '''
        更新订单，只有最新一页[name, creat_time]
        '''
        data = {
            "openudid": self.userId,
            "token": self._token,
            "sessid": self._session
        }
        res = self._request(self.urls["MALL_RECORD"], method="POST", data=data)
        if res.json()["iRet"] == 1:
            self.listRecord = [{key if key!="abbreviation" else "name": value for key,value in item.items() if key=="abbreviation" or key=="create_time"} for item in res.json()["data"]["list"]]
        else:
            return res.json()["sMsg"]



if __name__ == '__main__':
    ck = 'pt2gguin=; pt2gguin=o3115492626; ETK=; uin=o3115492626; skey=@16WFxfbTC; superuin=o3115492626; supertoken=1638296115; superkey=l6VDDRbevHEK4NWSVBOQHtu9hORgjjsKqXScHp80uzo_; pt_recent_uins=f3ce8d7f330a34ccc27899390ff861ea035899c206f54bf141fa28b50a94c4318ae180c72c5c80a410d93f32e3c4ab3a40d50a7e8db80065; pt_guid_sig=53f060d067324937668570451e036887d3f8ef3157bf656c05f5dff3632ed160; ptnick_3115492626=e68898e4ba89; ptcz=a6c48392e111c55880b4e42ca71f45501e92d5146b90b7bb2c3fac460f87e612; ptcz='
    pet = Qpet()
    print(pet.getdata(ck))

