import asyncio
import io
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import signal
import sys

# ===== YENİ AYARLAR =====
api_id = 32778223
api_hash = "ff44a946dbb1dcfd979409f41a69afc9"
BOT_TOKEN = "8752355725:AAGqj0UGi5yRRt0F87eJxlcHW2hbJ53Kaf4"  # YENİ TOKEN
TARGET_BOT = "inzegosorgubot"

ADMINS = {8685981899, 6322020905}

# ===== DURUM =====
banned_users = set()
current_user = None

# ===== İZİN VERİLEN TXT DOSYALARI =====
ALLOWED_TXT_FILES = {
    "Gsmtc_Bilgileri.txt",
    "Adres_Bilgileri.txt",
    "toplu_sonuc.txt",
    "Kisi_Bilgileri.txt",
    "Aile_Bilgileri.txt"
}

# ===== YASAKLI KELİMELER =====
blocked_phrases = [
    "abdurrahman miran karabulak diyarbakır",
    "miray karabulak diyarbakır",
    "erol karabulak diyarbakır",
    "/gsmtc 5337311021"
]

def is_blocked(text: str) -> bool:
    t = text.lower().replace("+", " ")
    return any(b in t for b in blocked_phrases)

# ===== USERBOT =====
userbot = TelegramClient("31userbot_session", api_id, api_hash)

# === YENİ: Graceful shutdown için sinyal işleyici ===
def signal_handler(sig, frame):
    print('\n🛑 Kapatılıyor...')
    loop = asyncio.get_event_loop()
    loop.create_task(shutdown())
    # 3 saniye sonra zorla kapat
    loop.call_later(3, lambda: sys.exit(0))

async def shutdown():
    """Bot'u düzgün şekilde kapat"""
    try:
        # Bot'u durdur
        if bot_app:
            await bot_app.updater.stop()
            await bot_app.stop()
            await bot_app.shutdown()
        
        # Userbot'u durdur
        if userbot and userbot.is_connected():
            await userbot.disconnect()
        
        print("✅ Bot başarıyla kapatıldı")
    except Exception as e:
        print(f"❌ Kapatma hatası: {e}")
    finally:
        # Tüm görevleri iptal et
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
        sys.exit(0)

# === YENİ: Her 6 saatte bir /start gönderecek fonksiyon ===
async def send_start_periodically():
    while True:
        try:
            if userbot and userbot.is_connected():
                await userbot.send_message(TARGET_BOT, "/start")
                print("✅ /start mesajı gönderildi")
            else:
                print("⚠️ Userbot bağlı değil, /start gönderilemedi")
        except Exception as e:
            print("❌ /start gönderme hatası:", e)
        await asyncio.sleep(6 * 60 * 60)  # 6 saat bekle

@userbot.on(events.NewMessage(from_users=TARGET_BOT))
async def target_bot_handler(event):

    global current_user

    if not current_user:
        return

    try:

        # DOSYA GELİRSE
        if event.message.file:

            filename = event.message.file.name

            if not filename:
                return

            if filename not in ALLOWED_TXT_FILES:
                return

            buffer = io.BytesIO()
            await event.download_media(buffer)
            buffer.seek(0)

            await bot_app.bot.send_document(
                chat_id=current_user,
                document=InputFile(buffer, filename=filename),
                caption=event.raw_text or ""
            )

        # METİN GELİRSE
        elif event.raw_text:

            await bot_app.bot.send_message(
                chat_id=current_user,
                text=event.raw_text
            )

    except Exception as e:
        print("Gönderme hatası:", e)


@userbot.on(events.CallbackQuery)
async def callback_handler(event):

    try:

        response = await userbot(GetBotCallbackAnswerRequest(
            peer=TARGET_BOT,
            msg_id=event.message.id,
            data=event.data
        ))

        if response.message:

            await bot_app.bot.send_message(
                event.sender_id,
                response.message
            )

        else:
            await event.answer("✅ İşlem tamamlandı", alert=True)

    except Exception as e:

        await bot_app.bot.send_message(
            event.sender_id,
            f"Callback hatası: {e}"
        )

# ===== BOT =====

async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global current_user

    user_id = update.effective_chat.id
    text = update.message.text

    if user_id in banned_users:
        await update.message.reply_text("🚫 Bu botu kullanmanız yasaklandı.")
        return

    if is_blocked(text):
        await update.message.reply_text("🚫 Bu sorgu engellendi.")
        return

    current_user = user_id

    await userbot.send_message(TARGET_BOT, text)


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMINS:
        return

    try:
        uid = int(context.args[0])
        banned_users.add(uid)
        await update.message.reply_text(f"✅ {uid} banlandı.")
    except:
        await update.message.reply_text("Kullanım: /ban kullanıcı_id")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMINS:
        return

    try:
        uid = int(context.args[0])
        banned_users.discard(uid)
        await update.message.reply_text(f"✅ {uid} banı kaldırıldı.")
    except:
        await update.message.reply_text("Kullanım: /unban kullanıcı_id")


async def komutlar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🔎 SORGU KOMUTLARI\n\n"
        "/sorgu mehmet demir İstanbul\n"
        "/sorgu mehmet+akif demir İstanbul\n\n"
        "/gsmtc 5555555555\n"
        "/ipsorgu 1.1.1.1\n"
        "/operator 5555555555\n"
        "/isyeri 11111111110\n"
        "/tcpro 11111111110\n\n"
        "📌 TOPLU\n"
        "/toplu 11111111110\n"
        "/toplu 5555555555"
    )

# ===== BOT BAŞLAT =====

bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

bot_app.add_handler(CommandHandler("ban", ban))
bot_app.add_handler(CommandHandler("unban", unban))
bot_app.add_handler(CommandHandler("komutlar", komutlar))

bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_message))
bot_app.add_handler(MessageHandler(filters.COMMAND, user_message))


async def main():

    global bot_app
    
    print("🔹 Userbot başlatılıyor")
    await userbot.start()
    print("✅ Userbot aktif")

    # === YENİ: Webhook'u temizle ===
    try:
        # Önce webhook'u temizle
        await bot_app.bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook temizlendi, bekleyen güncellemeler silindi")
    except Exception as e:
        print(f"⚠️ Webhook temizleme hatası: {e}")

    # === YENİ: 6 saatte bir /start gönderen görevi başlat ===
    asyncio.create_task(send_start_periodically())
    print("⏰ 6 saatte bir /start gönderme görevi başlatıldı")

    print("🔹 Bot başlatılıyor")
    await bot_app.initialize()
    await bot_app.start()
    
    # === YENİ: Polling başlat (drop_pending_updates=True ile) ===
    await bot_app.updater.start_polling(drop_pending_updates=True)
    print("✅ Bot aktif")

    # Sinyal işleyicilerini ayarla
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Sonsuza kadar bekle
        await asyncio.Future()
    except asyncio.CancelledError:
        print("🛑 Ana görev iptal edildi")
    finally:
        await shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
