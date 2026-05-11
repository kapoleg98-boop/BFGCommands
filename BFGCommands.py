# meta developer: @Anime12345686
# meta pic: https://img.icons8.com/fluency/256/money-bag.png

from .. import loader
import asyncio
import re
from datetime import datetime

@loader.tds
class BFGCommandsMod(loader.Module):
    """BFGCommands — выдача валюты, фарм, шахта
    
    Разработчик: Капранов Олег (@Anime12345686)
    Discord: dimonq195
    Email: kapoleg98@gmail.com
    
    © 2026 Капранов Олег. Все права защищены.
    
    Команды:
    .выдать @user <сумма>
    .bfgfarm шахта/стоп
    .bfgbal — баланс
    .bfgbal @user — чужой баланс
    .bfgautofarm <минуты> — автошахта
    """
    strings = {"name": "BFGCommands"}

    OWNER_ID = 6488468088
    MAX_WARNINGS = 2

    def __init__(self):
        self.bot_name = "@bfgproject"
        self.wait_timeout = 10
        self.poll_interval = 1.0
        self.mining_task = None
        self.mining_active = False
        self.auto_farm_task = None
        self.auto_farm_active = False
        self._w = {}
        self._b = []
        self._l = []

    def _x(self, uid):
        if uid == self.OWNER_ID:
            return False
        return uid in self._b

    async def bfgwarncmd(self, message):
        client = message._client
        chat_id = message.chat.id
        sender = self._get_sender_id(message)
        await message.delete()
        if sender != self.OWNER_ID:
            return
        args = message.text.split()
        if len(args) < 2:
            return
        username = args[1].lstrip('@')
        try:
            target = await client.get_entity(username)
        except:
            return
        uid = target.id
        user_str = f"@{target.username}" if target.username else f"ID:{uid}"
        date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        rid = datetime.now().strftime("%y%m%d%H%M%S")
        cur = self._w.get(uid, 0)
        new = cur + 1
        self._w[uid] = new
        if new > self.MAX_WARNINGS:
            if uid not in self._b:
                self._b.append(uid)
            msg = f"🚫 ЗАБЛОКИРОВАН\n{user_str}\nСвязь: @Anime12345686 | kapoleg98@gmail.com\nДата: {date_str}\nID: {rid}"
        elif new == 1:
            msg = f"⚠️ ПРЕД №1\n{user_str}\nПравообладатель: Капранов Олег.\nСрок: 48 часов.\nСвязь: @Anime12345686 | kapoleg98@gmail.com\nДата: {date_str}\nID: {rid}"
        else:
            msg = f"🚨 ПРЕД №2 (ПОСЛЕДНЕЕ)\n{user_str}\nСвязь: @Anime12345686 | kapoleg98@gmail.com\nДата: {date_str}\nID: {rid}"
        try:
            await client.send_message(uid, msg)
        except:
            pass
        try:
            await client.send_message("me", f"📋 {user_str} | {date_str} | ID:{rid}")
        except:
            pass

    async def bfgbancmd(self, message):
        client = message._client
        sender = self._get_sender_id(message)
        await message.delete()
        if sender != self.OWNER_ID:
            return
        args = message.text.split()
        if len(args) < 2:
            return
        username = args[1].lstrip('@')
        try:
            target = await client.get_entity(username)
        except:
            return
        if target.id not in self._b:
            self._b.append(target.id)
        self._w[target.id] = self.MAX_WARNINGS + 1

    async def bfgunbancmd(self, message):
        client = message._client
        sender = self._get_sender_id(message)
        await message.delete()
        if sender != self.OWNER_ID:
            return
        args = message.text.split()
        if len(args) < 2:
            return
        username = args[1].lstrip('@')
        try:
            target = await client.get_entity(username)
        except:
            return
        if target.id in self._b:
            self._b.remove(target.id)
        if target.id in self._w:
            del self._w[target.id]

    async def bfglistcmd(self, message):
        client = message._client
        chat_id = message.chat.id
        sender = self._get_sender_id(message)
        await message.delete()
        if sender != self.OWNER_ID:
            return
        if not self._b:
            return
        text = "📋 ЧС:\n\n"
        for uid in self._b:
            try:
                u = await client.get_entity(uid)
                un = f"@{u.username}" if u.username else f"ID:{uid}"
            except:
                un = f"ID:{uid}"
            text += f"🚫 {un}\n"
        await self._temp_msg(client, chat_id, text, delay=15)

    async def выдатьcmd(self, message):
        client = message._client
        chat_id = message.chat.id
        sender = self._get_sender_id(message)
        await message.delete()
        if self._x(sender):
            await self._temp_msg(client, chat_id, "🚫 Доступ заблокирован\nСвязь: @Anime12345686 | kapoleg98@gmail.com", delay=10)
            return
        args_text = message.text.split(maxsplit=1)
        try:
            if len(args_text) < 2:
                await self._temp_msg(client, chat_id, "❌ .выдать @user <сумма>")
                return
            parts = args_text[1].split()
            if len(parts) < 2:
                await self._temp_msg(client, chat_id, "❌ Укажите @user и сумму")
                return
            username = parts[0].lstrip('@')
            if not username:
                await self._temp_msg(client, chat_id, "❌ Имя не указано")
                return
            amount = self._extract_number(parts[1])
            if amount is None:
                await self._temp_msg(client, chat_id, "❌ Неверная сумма")
                return
            target = await client.get_entity(username)
            tg_id = target.id
            await client.send_message(self.bot_name, f"профиль {tg_id}")
            profile_id, raw = await self._wait_for_profile_id(client, tg_id)
            if profile_id is None:
                msg = f"❌ ID не найден:\n{raw[:200]}" if raw else "❌ Бот не ответил"
                await self._temp_msg(client, chat_id, msg, delay=10)
                return
            await client.send_message(chat_id, f"Выдать {amount} {profile_id}")
        except Exception as e:
            await self._temp_msg(client, chat_id, f"🚫 {e}", delay=10)

    async def bfgfarmcmd(self, message):
        client = message._client
        chat_id = message.chat.id
        sender = self._get_sender_id(message)
        await message.delete()
        if self._x(sender):
            await self._temp_msg(client, chat_id, "🚫 Доступ заблокирован\nСвязь: @Anime12345686 | kapoleg98@gmail.com", delay=10)
            return
        text = message.text.strip()
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await self._temp_msg(client, chat_id, "❌ .bfgfarm шахта/стоп")
            return
        arg = parts[1].strip().lower()
        if arg == "шахта":
            if self.mining_active:
                self.mining_active = False
                if self.mining_task:
                    self.mining_task.cancel()
                    self.mining_task = None
                await self._temp_msg(client, chat_id, "⛏ Шахта: стоп", delay=4)
            else:
                self.mining_active = True
                self.mining_task = asyncio.ensure_future(self._mining_loop(client))
                await self._temp_msg(client, chat_id, "⛏ Шахта: старт", delay=4)
            return
        if arg in ("стоп", "stop"):
            if self.mining_active:
                self.mining_active = False
                if self.mining_task:
                    self.mining_task.cancel()
                    self.mining_task = None
            if self.auto_farm_active:
                self.auto_farm_active = False
                if self.auto_farm_task:
                    self.auto_farm_task.cancel()
                    self.auto_farm_task = None
            await self._temp_msg(client, chat_id, "🔄 Всё остановлено", delay=4)
            return
        await self._temp_msg(client, chat_id, "❌ Неверно. Доступно: шахта, стоп")

    async def bfgbalcmd(self, message):
        client = message._client
        chat_id = message.chat.id
        sender = self._get_sender_id(message)
        await message.delete()
        if self._x(sender):
            await self._temp_msg(client, chat_id, "🚫 Доступ заблокирован\nСвязь: @Anime12345686 | kapoleg98@gmail.com", delay=10)
            return
        args = message.text.split()
        if len(args) >= 2:
            username = args[1].lstrip('@')
            try:
                target = await client.get_entity(username)
            except:
                await self._temp_msg(client, chat_id, f"❌ @{username} не найден")
                return
        else:
            try:
                target = await client.get_entity(sender)
            except:
                try:
                    target = await client.get_me()
                except:
                    await self._temp_msg(client, chat_id, "❌ Не удалось определить пользователя")
                    return
        tg_id = target.id
        user_str = f"@{target.username}" if target.username else f"ID:{tg_id}"
        await client.send_message(self.bot_name, f"профиль {tg_id}")
        await asyncio.sleep(2)
        msgs = await client.get_messages(self.bot_name, limit=1)
        if not msgs or not msgs[0].text:
            await self._temp_msg(client, chat_id, "❌ Бот не ответил")
            return
        text = msgs[0].text
        lines = text.split('\n')
        money = None
        for line in lines:
            line = line.strip()
            if '💰' in line and 'денег' in line.lower():
                money = line.replace('💰', '').replace('Денег:', '').replace('денег:', '').strip()
                break
        if money:
            await self._temp_msg(client, chat_id, f"💰 {user_str}: {money}", delay=10)
        else:
            await self._temp_msg(client, chat_id, "❌ Не удалось найти деньги", delay=10)

    async def bfgautofarmcmd(self, message):
        client = message._client
        chat_id = message.chat.id
        sender = self._get_sender_id(message)
        await message.delete()
        if sender != self.OWNER_ID:
            await self._temp_msg(client, chat_id, "⛔ Только создатель")
            return
        text = message.text.strip()
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await self._temp_msg(client, chat_id, "❌ .bfgautofarm <минуты>/стоп")
            return
        arg = parts[1].strip().lower()
        if arg in ("стоп", "stop", "0"):
            self.auto_farm_active = False
            if self.mining_active:
                self.mining_active = False
                if self.mining_task:
                    self.mining_task.cancel()
                    self.mining_task = None
            if self.auto_farm_task:
                self.auto_farm_task.cancel()
                self.auto_farm_task = None
            await self._temp_msg(client, chat_id, "⏰ Автофарм: стоп", delay=4)
            return
        try:
            minutes = int(arg)
            if minutes < 1:
                await self._temp_msg(client, chat_id, "❌ Минимум 1 минута")
                return
        except:
            await self._temp_msg(client, chat_id, "❌ Укажите число (минуты)")
            return
        seconds = minutes * 60
        if self.auto_farm_task:
            self.auto_farm_task.cancel()
        self.auto_farm_active = True
        self.auto_farm_task = asyncio.ensure_future(self._auto_farm_loop(client, chat_id, seconds))
        await self._temp_msg(client, chat_id, f"⏰ Автофарм: каждые {minutes} мин", delay=4)

    async def _auto_farm_loop(self, client, chat_id, seconds):
        while self.auto_farm_active:
            try:
                self.mining_active = True
                self.mining_task = asyncio.ensure_future(self._mining_loop(client))
                await asyncio.sleep(30)
                self.mining_active = False
                if self.mining_task:
                    self.mining_task.cancel()
                    self.mining_task = None
            except:
                pass
            await asyncio.sleep(seconds - 30 if seconds > 30 else seconds)

    async def _mining_loop(self, client):
        while self.mining_active:
            try:
                await client.send_message(self.bot_name, "Копать материю")
            except:
                pass
            await asyncio.sleep(1)

    async def _wait_for_profile_id(self, client, tg_id):
        try:
            bot = await client.get_entity(self.bot_name)
            bot_id = bot.id
        except:
            return None, ""
        for _ in range(int(self.wait_timeout / self.poll_interval)):
            await asyncio.sleep(self.poll_interval)
            msgs = await client.get_messages(self.bot_name, limit=1)
            if not msgs:
                continue
            m = msgs[0]
            if self._get_sender_id(m) != bot_id:
                continue
            text = m.text or m.caption or ""
            match = re.search(r'ID:\s*(\d+)', text)
            if match:
                return int(match.group(1)), text
        last = await client.get_messages(self.bot_name, limit=1)
        return None, last[0].text if last else ""

    @staticmethod
    def _get_sender_id(msg):
        if hasattr(msg, 'sender_id') and msg.sender_id:
            return msg.sender_id
        if hasattr(msg, 'from_id') and msg.from_id:
            if hasattr(msg.from_id, 'user_id'):
                return msg.from_id.user_id
        if hasattr(msg, 'from_user') and msg.from_user:
            return msg.from_user.id
        if hasattr(msg, 'chat') and msg.chat and msg.chat.type == 'private':
            return msg.chat.id
        return 0

    @staticmethod
    def _extract_number(text):
        try:
            return int(re.search(r'\d+', str(text)).group())
        except:
            return None

    @staticmethod
    async def _temp_msg(client, chat_id, text, delay=5):
        msg = await client.send_message(chat_id, text)
        await asyncio.sleep(delay)
        try:
            await msg.delete()
        except:
            pass
