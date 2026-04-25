# meta developer: @Anime12345686
# meta pic: https://img.icons8.com/fluency/256/money-bag.png

from .. import loader
import asyncio
import re

@loader.tds
class BFGCommandsMod(loader.Module):
    """BFGCommands — выдача валюты, фарм, шахта через @bfgproject
    
    Разработчик: Капранов Олег (@Anime12345686)
    Бета-тестер: @Sun_bright_fit
    Discord: dimonq195
    Email: kapoleg98@gmail.com
    
    Команды:
    .выдать @user <сумма> — выдать валюту
    .bfgfarm <число> — купить N видеокарт
    .bfgfarm <время> — автофарм (10с/5м/1ч/2д)
    .bfgfarm шахта — копать материю
    .bfgfarm стоп — остановить фарм
    """
    strings = {"name": "BFGCommands"}

    OWNER_ID = 6488468088

    def __init__(self):
        self.bot_name = "@bfgproject"
        self.wait_timeout = 10
        self.poll_interval = 1.0
        self.farm_cycle_task = None
        self.mining_task = None
        self.mining_active = False

    def _check_access(self, message):
        sender = self._get_sender_id(message)
        if sender == self.OWNER_ID:
            return True
        try:
            protect = self.lookup("BFGProtect")
            if protect:
                if not protect.is_owner(sender) and protect.is_blacklisted(sender):
                    return False
        except:
            pass
        return True

    async def выдатьcmd(self, message):
        """.выдать @user <сумма> — выдать валюту"""
        client = message._client
        chat_id = message.chat.id

        if not self._check_access(message):
            await self._temp_msg(client, chat_id, (
                "🚫 <b>ДОСТУП ЗАБЛОКИРОВАН</b>\n\n"
                "Вы в чёрном списке.\n"
                "Причина: нарушение авторских прав.\n\n"
                "📩 @Anime12345686 | dimonq195 | kapoleg98@gmail.com"
            ), delay=10)
            return

        args_text = message.text.split(maxsplit=1)
        await message.delete()

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
                await self._temp_msg(client, chat_id, "❌ Имя пользователя не указано")
                return
            amount = self._extract_number(parts[1])
            if amount is None:
                await self._temp_msg(client, chat_id, "❌ Неверная сумма")
                return

            target = await client.get_entity(username)
            tg_id = target.id

            await client.send_message(self.bot_name, f"профиль {tg_id}")
            profile_id, raw_answer = await self._wait_for_profile_id(client, tg_id)

            if profile_id is None:
                if raw_answer:
                    await self._temp_msg(client, chat_id, f"❌ ID не найден:\n{raw_answer[:200]}", delay=10)
                else:
                    await self._temp_msg(client, chat_id, "❌ Бот не ответил")
                return

            await client.send_message(chat_id, f"Выдать {amount} {profile_id}")

        except Exception as e:
            await self._temp_msg(client, chat_id, f"🚫 Ошибка: {str(e)}", delay=10)

    async def bfgfarmcmd(self, message):
        """.bfgfarm <число>/<время>/шахта/стоп"""
        client = message._client
        chat_id = message.chat.id

        if not self._check_access(message):
            await self._temp_msg(client, chat_id, (
                "🚫 <b>ДОСТУП ЗАБЛОКИРОВАН</b>\n\n"
                "Вы в чёрном списке.\n"
                "Причина: нарушение авторских прав.\n\n"
                "📩 @Anime12345686 | dimonq195 | kapoleg98@gmail.com"
            ), delay=10)
            return

        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await self._temp_msg(client, chat_id, "❌ Укажите: число, время (10с/5м/1ч/2д), шахта или стоп")
            return

        arg = args[1].strip().lower()

        if arg == "шахта":
            if self.mining_active:
                self.mining_active = False
                if self.mining_task:
                    self.mining_task.cancel()
                    self.mining_task = None
                await self._temp_msg(client, chat_id, "⛏ Шахта остановлена", delay=4)
            else:
                self.mining_active = True
                self.mining_task = asyncio.ensure_future(self._mining_loop(client))
                await self._temp_msg(client, chat_id, "⛏ Шахта запущена", delay=4)
            return

        if arg in ("стоп", "stop"):
            if self.farm_cycle_task:
                self.farm_cycle_task.cancel()
                self.farm_cycle_task = None
                await self._temp_msg(client, chat_id, "🔄 Ферма остановлена", delay=4)
            else:
                await self._temp_msg(client, chat_id, "❌ Нет активного цикла")
            return

        if arg.isdigit():
            await self._farm_buy_cards(client, chat_id, int(arg))
            return

        time_seconds = self._parse_time(arg)
        if time_seconds is not None:
            if self.farm_cycle_task:
                self.farm_cycle_task.cancel()
            self.farm_cycle_task = asyncio.ensure_future(
                self._farm_cycle_loop(client, chat_id, time_seconds)
            )
            await self._temp_msg(client, chat_id, f"🔁 Ферма-цикл: интервал {arg}", delay=4)
            return

        await self._temp_msg(client, chat_id, "❌ Неверный аргумент")

    async def _farm_buy_cards(self, client, chat_id, count):
        await client.send_message(self.bot_name, "моя ферма")
        bot_msg = await self._wait_for_bot_response(client, self.bot_name)
        if not bot_msg:
            await self._temp_msg(client, chat_id, "❌ Бот не ответил")
            return

        if not await self._click_button(bot_msg, "💰Собрать прибыль"):
            await self._temp_msg(client, chat_id, "⚠ Кнопка сбора не найдена")
        else:
            await asyncio.sleep(0.5)
            bot_msg = await self._get_msg(client, self.bot_name, bot_msg.id)
            if not bot_msg:
                return

        bought = 0
        for _ in range(count):
            if not await self._click_button(bot_msg, "⬆️Купить видеокарту"):
                break
            bought += 1
            await asyncio.sleep(0.4)
            bot_msg = await self._get_msg(client, self.bot_name, bot_msg.id)
            if not bot_msg:
                break

        await self._temp_msg(client, chat_id, f"✅ Видеокарт: {bought}/{count}", delay=5)

    async def _farm_cycle_loop(self, client, chat_id, interval):
        while True:
            try:
                await self._farm_buy_cards(client, chat_id, 1)
            except Exception as e:
                await self._temp_msg(client, chat_id, f"🚫 Ошибка: {e}", delay=8)
            await asyncio.sleep(interval)

    async def _mining_loop(self, client):
        while self.mining_active:
            try:
                await client.send_message(self.bot_name, "Копать материю")
            except:
                pass
            await asyncio.sleep(1)

    async def _click_button(self, msg, text):
        if not msg or not msg.reply_markup:
            return False
        for row in msg.reply_markup.inline_keyboard:
            for btn in row:
                if btn.text == text:
                    try:
                        await msg.click(btn.data)
                        return True
                    except:
                        return False
        return False

    async def _wait_for_bot_response(self, client, chat_id, timeout=10):
        try:
            bot = await client.get_entity(self.bot_name)
            bot_id = bot.id
        except:
            return None
        pre = await client.get_messages(chat_id, limit=1)
        pre_id = pre[0].id if pre else 0
        for _ in range(timeout * 2):
            await asyncio.sleep(0.5)
            msgs = await client.get_messages(chat_id, limit=5)
            if not msgs:
                continue
            for m in msgs:
                if m.id > pre_id and m.from_user and m.from_user.id == bot_id:
                    return m
                s = self._get_sender_id(m)
                if s == bot_id and m.id > pre_id:
                    return m
            pre_id = max(m.id for m in msgs)
        return None

    async def _get_msg(self, client, chat_id, msg_id):
        try:
            return await client.get_messages(chat_id, msg_id)
        except:
            return None

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
    def _parse_time(s):
        match = re.fullmatch(r'(\d+)\s*([смчд])', s)
        if not match:
            return None
        num = int(match.group(1))
        mult = {'с': 1, 'м': 60, 'ч': 3600, 'д': 86400}
        return num * mult.get(match.group(2), 0)

    @staticmethod
    async def _temp_msg(client, chat_id, text, delay=5):
        msg = await client.send_message(chat_id, text)
        await asyncio.sleep(delay)
        try:
            await msg.delete()
        except:
            pass