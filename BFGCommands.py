# meta developer: @Anime12345686
# meta pic: https://img.icons8.com/fluency/256/money-bag.png

from .. import loader
import asyncio
import re

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

    SUFFIX_TO_EXP = {
        "тысяч": 3, "тыс": 3, "миллион": 6, "млн": 6,
        "миллиард": 9, "млрд": 9, "триллион": 12, "трлн": 12,
        "квадриллион": 15, "квдр": 15, "квинтиллион": 18, "квнт": 18,
        "секстиллион": 21, "скст": 21, "септиллион": 24, "септ": 24,
        "октиллион": 27, "окт": 27, "октл": 27, "нониллион": 30, "нон": 30,
        "дециллион": 33, "дец": 33, "ундецил": 36, "додецил": 39,
        "трейдецил": 42, "кваттдецил": 45, "квиндецил": 48,
        "сексдецил": 51, "септдецил": 54, "октодецил": 57,
        "нондецил": 60, "вигинтил": 63, "унвигинтил": 66,
        "довигинтил": 69, "трейвигинтил": 72, "кваттвигинтил": 75,
        "квинвигинтил": 78, "сексвигинти": 81
    }

    def __init__(self):
        self.bot_name = "@bfgproject"
        self.wait_timeout = 10
        self.poll_interval = 1.0
        self.mining_task = None
        self.mining_active = False
        self.auto_farm_task = None
        self.auto_farm_active = False

    def _to_e_notation(self, text):
        """Преобразует '122.6октл$' в '1.226e29'"""
        text = text.strip().lower()
        for ch in ['$', '₽', '€', '¥', '฿']:
            text = text.replace(ch, '')
        text = text.strip()
        
        if 'e' in text:
            return text
        
        match = re.match(r'([\d.]+)\s*([а-я]+)', text)
        if not match:
            return text
        
        try:
            number = float(match.group(1))
        except:
            return text
        
        suffix = match.group(2).rstrip('ов')
        
        exp = None
        for suf, e_val in self.SUFFIX_TO_EXP.items():
            if suffix.startswith(suf):
                exp = e_val
                break
        
        if exp is not None:
            result = number * (10 ** exp)
            e_exp = 0
            while result >= 10:
                result /= 10
                e_exp += 1
            return f"{result:.3f}e{e_exp}"
        
        return text

    async def выдатьcmd(self, message):
        client = message._client
        chat_id = message.chat.id
        await message.delete()

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
        await message.delete()

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
            formatted = self._to_e_notation(money)
            await self._temp_msg(client, chat_id, f"💰 {user_str}: {formatted}", delay=10)
        else:
            await self._temp_msg(client, chat_id, "❌ Не удалось найти деньги", delay=10)

    async def bfgautofarmcmd(self, message):
        client = message._client
        chat_id = message.chat.id
        await message.delete()

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
