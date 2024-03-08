'''
Database Wrapper - MongoDB
Made by: June8th (Lumine)

Thư viện cần thiết:
pymongo
disnake
validators
unidecode
colorama
asigref
'''

# Import một số thứ cần thiết
import pymongo
from pymongo import MongoClient

import disnake
import json
import validators
from unidecode import unidecode
import json
import colorama
from colorama import Fore, Style
# from utils.user.Key.Keyutils import KeyUtils
import random
from random import randint

from asgiref.sync import sync_to_async as s2a

# Load env để lấy MongoDB URI
from os import environ
from dotenv import load_dotenv
load_dotenv()
import aiosqlite

# Lấy link cơ sở dữ liệu từ env
MONGODB_URI = environ.get("MONGOUSER") # Hell nah, I won't show you my database link

# Load một vài file linh tinh và ko cần thiết cho lắm <(")
with open("etc/ratelimit_basic.json", "r", encoding="utf-8") as f: ratelimit_basic = json.load(f)
with open("etc/owner_ratelimit.json", "r", encoding="utf-8") as f: owner_ratelimit = json.load(f)
with open("etc/ratelimit_premium.json", "r", encoding="utf-8") as f: ratelimit_premium = json.load(f)
with open("utils/user/Key/Premium_keys.json", "r", encoding="utf-8") as f: premium_key = json.load(f)

class database_handler():
    def __init__(self):
        self.db = aiosqlite.Connection = None
    
    async def initalize(self, mongo_uri = MONGODB_URI):
        self.client = MongoClient(mongo_uri)
        self.users = self.client.db.users
        self.ratelimit = self.client.db.ratelimit
        self.banlist = self.client.db.banlist
        
    
    async def _initalize(self,db):
        self.db = db
        await db.execute("CREATE TABLE IF NOT EXISTS ratelimit (uid INTEGER, service TEXT, used INTEGER, time INTEGER)")
        await db.commit()

    async def is_banned(self, uid: int):
        "Kiểm tra xem người dùng có bị cấm hay không"
        data = await s2a(self.banlist.find_one)({"uid": uid})
        if data is None: return { "status": "notfound" }
        return {
            "status": "banned",
            "time": data["time"],
            "ban_reason": data["ban_reason"]
        }

    async def get_userinfo(self, uid: int):
        "Lấy thông tin người dùng từ cơ sở dữ liệu"
        data = await s2a(self.users.find_one)({"uid": uid})
        if data is None:
            return {
                "status": "notfound"
            }
        return {
            "status": "success",
            "coin": data["coin"],
            "money": data["money"],
            "creation_time": data["creation_time"],
            "premium": data["premium"],
            "uytin": data["uytin"],
            "activities": json.loads(data["activities"]),
            "signature": data["signature"],
            "link": data["link"]
        }
    
    async def fetch_money(self, uid: int):
        "Lấy thông tin tiền của người dùng"
        userinfo = await self.get_userinfo(uid)
        if userinfo["status"] == "success":
            coin = userinfo["coin"]
            return coin

    async def register(self, uid: int):
        "Đăng kí tài khoản trên hệ thống"
        ban_status = await self.is_banned(uid)
        if ban_status["status"] == "banned":
            return {
                "status": "banned",
                "time": ban_status["time"],
                "ban_reason": ban_status["ban_reason"]
            }
        userinfo = await self.get_userinfo(uid)
        if userinfo["status"] != "notfound":
            return {
                "status": "exist"
            }
        await s2a(self.users.insert_one)({
            "uid": uid,
            "coin": 0,
            "money": 0,
            "creation_time": int(disnake.utils.utcnow().timestamp()),
            "premium": 0,
            "uytin": 100,
            "activities": "[]",
            "signature": "",
            "link": "{}"
        })
        await self.write_history(uid, "Đăng ký tài khoản thành công.")
        return {
            "status": "success"
        }
    
    async def is_premium(self, uid: int):
        "Kiểm tra xem người dùng có phải là premium hay không"
        userinfo = await self.get_userinfo(uid)
        if userinfo["status"] == "success":
            premium_vaild_time = await self.get_userinfo(uid)
            premium_vaild_time = premium_vaild_time["premium"]
            if premium_vaild_time > int(disnake.utils.utcnow().timestamp()):
                return {
                    "status": True,
                    "valid_time": premium_vaild_time
                }
            else:
                return {
                    "status": False,
                }
        else:
            return False
     
    async def write_history(self, uid: int, content: str):
        "Ghi lịch sử hoạt động của người dùng vào database"
        userinfo = await self.get_userinfo(uid)
        if userinfo["status"] == "success":
            new_activity = {
                "timestamp": int(disnake.utils.utcnow().timestamp()),
                "activity": content
            }
            commit = [new_activity] + userinfo["activities"]
            if len(commit) > 6:
                commit = commit[:6]
            await s2a(self.users.update_one)({"uid": uid}, {"$set": {"activities": json.dumps(commit, ensure_ascii=False)}})
            return { "status": "success" }
        else:
            return { "status": "failed" }
    
    async def transaction(self, uid: int, coin: int, money: int, reason: str = None):
        "Thực hiện giao dịch"
        if not coin and not money:
            return {
                "status": "failed",
                "reason": "Tham số bất thường."
            }
        banned = await self.is_banned(uid)
        if banned["status"] == "banned":
            return {
                "status": "failed",
                "reason": f"Tài khoản đã bị cấm sử dụng bot từ <t:{banned['time']}:R>. Lý do: {banned['ban_reason']}"
            }
        userinfo = await self.get_userinfo(uid)
        if userinfo["status"] == "success":
            if userinfo["coin"] + coin < 0 or userinfo["money"] + money < 0:
                return {
                    "status": "failed",
                    "reason": "Số dư của bạn không đủ để thực hiện giao dịch này."
                }
            await s2a(self.users.update_one)({"uid": uid}, {"$set": {"coin": userinfo["coin"] + coin, "money": userinfo["money"] + money}})
            history = ""
            if coin > 0:
                history += f'+ {coin} xu '
            elif coin < 0:
                history += f'{coin} xu '
            if money > 0:
                history += f'+ {money}$ '
            elif money < 0:
                history += f'{money}$ '
            if reason:
                history += f'| Lý do: {reason}'
            await self.write_history(uid, history)
            return {
                "status": "success"
            }
        return {
            "status": "failed",
            "reason": "Tài khoản không tồn tại."
        }
    
    async def ban(self, uid: int, reason: str):
        "Cấm người dùng khỏi hệ thống"
        await s2a(self.banlist.insert_one)({
            "uid": uid,
            "time": int(disnake.utils.utcnow().timestamp()),
            "ban_reason": reason
        })
    
    async def extend_premium(self, uid: int, day: int):
        "Gia hạn premium"
        time = day * 86400
        userinfo = await self.get_userinfo(uid)
        if userinfo["status"] == "success":
            if userinfo["premium"] > int(disnake.utils.utcnow().timestamp()):
                await s2a(self.users.update_one)({"uid": uid}, {"$set": {"premium": userinfo['premium'] + time}})
            else:
                await s2a(self.users.update_one)({"uid": uid}, {"$set": {"premium": int(disnake.utils.utcnow().timestamp()) + time}})
            userinfo = await self.get_userinfo(uid)
            return {
                "status": "success",
                "valid_time": userinfo["premium"]
            }
        else:
            return {
                "status": "failed"
            }
        
    async def claim_code(self, uid: int, code: str):
        """Claim premium code"""
        userinfo = await self.get_userinfo(uid)
        if userinfo["status"] == "notfound":
            return {
                "status": "failed",
                "reason": "Tài khoản không tồn tại."
            }
        elif code not in premium_key:
            return {
                "status": "failed",
                "reason": "Mã code không hợp lệ hoặc đã bị sử dụng."
            }
        else:
            del premium_key[code]
            with open("utils/user/Key/Premium_Keys.json", "w", encoding="utf-8") as f:
                json.dump(premium_key, f, ensure_ascii=False, indent=4)
                f.close()
                
        await self.transaction(uid=uid, coin=30000, money=50, reason="Code claim (30d)")
        await self.uytin(uid=uid, uytin=10)
        return await self.extend_premium(uid=uid, day=30)
        
    async def signature(self, uid, signature):
        """Set signature"""
        userinfo = await self.get_userinfo(uid)
        if userinfo["status"] == "success":
            await s2a(self.users.update_one)({"uid": uid}, {"$set": {"signature": signature}})
            return {
                "status": "success"
            }
        else:
            return {
                "status": "failed"
            }

    async def edit_link(self, uid: int, platform: str, url: str, display_name: str = None):
        """Edit link"""
        if platform not in ["facebook", "tiktok", "github", "discord", "telegram", "website", "youtube"]:
            return {
                "status": "failed",
                "reason": "Nền tảng chưa được hỗ trợ."
            }
        premium_status = await self.is_premium(uid)
        if not premium_status["status"]:
            return {
                "status": "failed",
                "reason": "Chức năng này chỉ dành cho người dùng premium."
            }
        if not (unidecode(url) == url and url.strip().startswith("https://") and validators.url(url.strip())):
            return {
                "status": "failed",
                "reason": "URL không hợp lệ."
            }
        userinfo = await self.get_userinfo(uid)
        if userinfo["status"] == "success":
            current_link = userinfo["link"]
            current_link[platform] = {
                "url": url.strip(),
                "display_name": display_name if display_name else platform.capitalize(),
                "platform": platform
            }
            await s2a(self.users.update_one)({"uid": uid}, {"$set": {"link": current_link}})
            return {
                "status": "success"
            }
        elif userinfo["status"] == "notfound":
            return {
                "status": "notfound",
            }
        elif userinfo["status"] == "banned":
            return {
                "status": "banned",
                "time": userinfo["time"],
                "ban_reason": userinfo["ban_reason"]
            }
        
    async def uytin(self, uid: int, uytin: int):
        """Add uytin"""
        userinfo = await self.get_userinfo(uid)
        if userinfo["status"] == "success":
            await s2a(self.users.update_one)({"uid": uid}, {"$set": {"uytin": userinfo["uytin"] + uytin}})
            return {
                "status": "success",
                "uytin": userinfo["uytin"] + uytin
            }
        else:
            return {
                "status": "failed",
                "reason": "Tài khoản không tồn tại."
            }
        
    async def use(self, uid: int, service: str, ispremium: bool = False):
        """Use service"""
        ratelimit_data = owner_ratelimit if uid == 115369804288150738 or uid == 867040792463802389 else ratelimit_premium if ispremium else ratelimit_basic 
        if service not in ratelimit_data:
            return {
                "status": "failed",
                "reason": "Dịch vụ chưa được hỗ trợ." if ispremium else "Dịch vụ chưa được hỗ trợ.\nHãy nâng cấp lên premium để sử dụng."
            }
        cursor = await self.db.execute("SELECT used, time FROM ratelimit WHERE uid = ? AND service = ?", (uid, service))
        data = await cursor.fetchone()
        if data is None:
            await self.db.execute("INSERT INTO ratelimit (uid, service, used, time) VALUES (?, ?, 1, ?)", (uid, service, int(disnake.utils.utcnow().timestamp())))
            await self.db.commit()
            return {
                "status": "success",
                "used": 1,
                "left": ratelimit_data[service] - 1,
            }
        elif data[1] // 86400 != int(disnake.utils.utcnow().timestamp()) // 86400:
            await self.db.execute("UPDATE ratelimit SET used = 1, time = ? WHERE uid = ? AND service = ?", (int(disnake.utils.utcnow().timestamp()), uid, service))
            await self.db.commit()
            return {
                "status": "success",
                "used": 1,
                "left": ratelimit_data[service] - 1,
            }
        elif data[0] < ratelimit_data[service]:
            await self.db.execute("UPDATE ratelimit SET used = ?, time = ? WHERE uid = ? AND service = ?", (data[0] + 1, int(disnake.utils.utcnow().timestamp()), uid, service))
            await self.db.commit()
            return {
                "status": "success",
                "used": data[0] + 1,
                "left": ratelimit_data[service] - (data[0] + 1),
            }
        else:
            return {
                "status": "failed",
                "reason": "Bạn đã sử dụng hết lượt sử dụng cho dịch vụ này. Hãy thử lại sau." if ispremium else "Bạn đã sử dụng hết lượt sử dụng cho dịch vụ này.\nHãy nâng cấp lên premium để nhận thêm lượt sử dụng."
            }
