import os
import json
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ======== CONFIG ========
api_id = 28069133
api_hash = "5ca91588221d1dd9c46d0df1dd4768f0"
string = "1BJWap1sBu3S7VzzCfs5ehWqeK_V6m-6y6tXVMqJ-XGBnSIvNpCcLnfTp78NJuWpPsFA1rhgwMWq3JjWoceV0h7FGYwZkhFmwPj0ssvEjNMRBfs6UsCY_NGADx28bmCHtrunULcdwrmkvYEcJvuouZLJXF9sh0Xs2mbIjnoSTKXVaT8NfPOyp8-3la_l3uYfff1MfZ8muINNcHxkO1wAjfS9f77pDCbSUOItqTOaut9XdciD2p37h4UDyQ18Sgid2hlN1gLXLO51Vg8a0VSQLTuPl6v8IlA2SAs5g6FcMZR6O3r9KItHFmVoYiK7hsOXhBDcXeG0BeCLGG8pMjVl29aA07uuZiWw="  # رشته session خودت
save_path = "SavedMessages"
cache_file = "message_cache.json"
os.makedirs(save_path, exist_ok=True)
# =======================

client = TelegramClient(StringSession(string), api_id, api_hash)

# بارگذاری cache از دیسک
if os.path.exists(cache_file):
    with open(cache_file, "r", encoding="utf-8") as f:
        message_cache = json.load(f)
else:
    message_cache = {}

# ذخیره cache روی دیسک
async def save_cache():
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(message_cache, f, ensure_ascii=False, indent=2)

# =======================

@client.on(events.NewMessage(incoming=True))
async def save_message(event):
    if event.is_private:
        sender = await event.get_sender()
        sender_name = sender.first_name or "کاربر ناشناس"
        sender_username = f"@{sender.username}" if sender.username else "❌ بدون نام کاربری"

        message_text = event.message.text or "[Media]"
        is_self_destruct = (getattr(event.message, 'self_destruct_time', None) is not None) or \
                           (getattr(getattr(event.message, 'media', None), 'ttl_seconds', None) is not None)

        file_path = None
        if event.message.photo or event.message.video or event.message.voice:
            ext = ".jpg" if event.message.photo else (".mp4" if event.message.video else ".ogg")
            file_name = f"{event.message.id}{ext}"
            file_path = os.path.join(save_path, file_name)
            await client.download_media(event.message, file=file_path)

            # ارسال فایل تایم‌دار یا self-destruct با تاخیر ۵ ثانیه
            if is_self_destruct:
                await asyncio.sleep(5)  # ⬅️ اضافه شد
                await client.send_file("me", file_path, caption=f"📥 فایل تایم‌دار از {sender_name} ({sender_username})")

        message_cache[str(event.message.id)] = {
            "chat_id": event.chat_id,
            "sender_id": sender.id,
            "sender_name": sender_name,
            "sender_username": sender_username,
            "message": message_text,
            "media_path": file_path,
            "is_self_destruct": is_self_destruct
        }
        await save_cache()

# =======================

@client.on(events.MessageDeleted)
async def deleted_handler(event):
    for msg_id in event.deleted_ids:
        str_id = str(msg_id)
        if str_id in message_cache:
            data = message_cache[str_id]
            sender_name = data["sender_name"]
            sender_username = data["sender_username"]
            deleted_msg = data["message"]
            media_path = data["media_path"]

            # ارسال متن پیام حذف شده
            msg_text = f'''🚨 *یک پیام حذف شد!*

👤 فرستنده: {sender_name}
🔗 آیدی: {sender_username}
📩 متن پیام:
"{deleted_msg}"'''
            await client.send_message("me", msg_text)

            # ارسال فایل با تاخیر ۵ ثانیه
            if media_path and os.path.exists(media_path):
                await asyncio.sleep(5)  # ⬅️ اضافه شد
                await client.send_file("me", media_path, caption=f"📥 فایل حذف‌شده از {sender_name}")

            del message_cache[str_id]
            await save_cache()

# =======================

async def main():
    await client.start()
    print("✅ ربات در حال اجرا است...")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
