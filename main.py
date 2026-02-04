from dotenv import load_dotenv
import os
from telegram import Update
from telegram.ext import MessageHandler, Application, CommandHandler, filters, ContextTypes
from telegram import KeyboardButton, ReplyKeyboardMarkup  #, ReplyKeyboardRemove
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler
# from google import genai
# import mysql.connector
import sqlite3
from EX_funcs import *
from DB_funcs import *
# from open_router import generate_with_openrouter
from liara_ai import generate_with_liara
import asyncio
from datetime import datetime

AI_CONCURRENCY_LIMIT = 3   # حداکثر درخواست همزمان به AI
AI_TIMEOUT = 60            # حداکثر زمان انتظار پاسخ (ثانیه)

AI_SEMAPHORE = asyncio.Semaphore(AI_CONCURRENCY_LIMIT)

load_dotenv()

# متغیر های ثابت
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
BOT_USERNAME = os.environ.get("BOT_USERNAME")
OWNER_ID = os.environ.get("OWNER_ID")
ADMIN_IDS = [int(OWNER_ID)]
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT")
# GOOGLE_API_KEY_1 = os.environ.get("GOOGLE_API_KEY_1")
# GOOGLE_API_KEY_2 = os.environ.get("GOOGLE_API_KEY_2")
# GOOGLE_API_KEY_3 = os.environ.get("GOOGLE_API_KEY_3")
# GOOGLE_API_KEY_4 = os.environ.get("GOOGLE_API_KEY_4")
# GOOGLE_API_KEY_5 = os.environ.get("GOOGLE_API_KEY_5")

API_COUNT = 5


# cnx = mysql.connector.connect(
#     host="127.0.0.1",
#     port=3306,
#     user="root",
#     password=DATABASE_PASSWORD,
#     database="dark_gpt")
# cur = cnx.cursor()

cnx = sqlite3.connect('db.sqlite3')
cur = cnx.cursor()

# keys
main_menu = [
    [KeyboardButton("وضعیت ها🔍"), KeyboardButton("شروع چت با هوش مصنوعی🤖")],
    [KeyboardButton("پیام به ادمین💬"), KeyboardButton("خرید اشتراک پرمیوم🔹")],
    #[KeyboardButton("دعوت از دوستان📨")]
]

admin_menu = [
    [KeyboardButton("فعال/غیرفعال کردن ربات")],
    [KeyboardButton("ارسال پیام همگانی")],
    [KeyboardButton("مدیریت کانالهای تبلیغاتی")],
    [KeyboardButton("آمار ربات"), KeyboardButton("پیام به کاربر مشخص")],
    [KeyboardButton("دریافت لاگ پرامپت ها (txt)")],
    [KeyboardButton("ارتقای کاربر به پرمیوم")],
    [KeyboardButton("بازگشت به منوی اصلی")]
]

ai_submenu = [
    [KeyboardButton("شروع چت جدید")],
    [KeyboardButton("ادامه ی چت قبلی")],
    [KeyboardButton("بازگشت به منوی اصلی")]
]

cancell_menu = [
    [KeyboardButton("انصراف❌")]
]



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    bot_status = get_bot_status()
    if bot_status != "active" and update.effective_user.id not in ADMIN_IDS:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="ربات در حال حاضر غیرفعال است.")
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    name = update.effective_user.full_name

    if not user_exists(user_id):
        add_new_user(user_id, username, name)

    reply_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""
🔥به ربات دارک جی پی تی خوش آمدید!🔥

اینجا میتونین بدون سانسور با هوش مصنوعی صحبت کنین و ازش هرچی میخواین بپرسین!
💀دارک جی پی تی هیچ محدودیتی نداره و هر سوالی رو جواب میده!💀
تخصصش هم پاسخ به سوالات <u>هک و امنیته</u>
(البته در مورد سوال هایی که آسیب به خودتون باشه، مثل خودکشی یا مواد مخدر پاسخ نمیده)
😊سعی کنین استفاده ی آموزشی و مفید داشته باشین
<b>مسئولیت هرگونه استفاده ی نادرست به عهده ی خودتونه</b>⚠️

برای شروع، از منوی زیر گزینه مورد نظرتون رو انتخاب کنین👇

""",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="شما ادمین ربات نیستید")
        return
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="سلام ادمین جون",
        reply_markup=ReplyKeyboardMarkup(admin_menu)
    )
    print(f"Admin {user_id} accessed admin panel.")
    

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    bot_status = get_bot_status()
    if bot_status != "active" and update.effective_user.id not in ADMIN_IDS:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="ربات در حال حاضر غیرفعال است.")
        return
    
    text = update.message.text
    
    if update.effective_user.id in ADMIN_IDS:
                
        if update.message.reply_to_message:  
                return await admin_response(update, context)
        
        if text == "فعال/غیرفعال کردن ربات":
            current_status = get_bot_status()
            button_status = []
        
            if current_status == "active":
                button_status.append(InlineKeyboardButton("غیرفعال کردن ربات", callback_data="deactivate_bot"))
                button_status.append(InlineKeyboardButton("بازگشت به منوی مدیریت", callback_data="admin_menu"))
            elif current_status == "inactive":
                button_status.append(InlineKeyboardButton("فعال کردن ربات", callback_data="activate_bot"))
                button_status.append(InlineKeyboardButton("بازگشت به منوی مدیریت", callback_data="admin_menu"))
            
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                    text=f"وضعیت فعلی ربات: {current_status}",
                                    reply_markup=InlineKeyboardMarkup([button_status]))

        
        if text == "آمار ربات":
            total_users = get_total_users()
            premium_users = get_premium_users_count()
            bot_status = get_bot_status()
            
            stats_message = (f"📊 آمار ربات:\n\n"
                            f"👥 تعداد کل کاربران: {total_users}\n"
                            f"💎 تعداد کاربران پرمیوم: {premium_users}\n"
                            f"🤖 وضعیت ربات: {bot_status}")
            
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                            text=stats_message,
                                            reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True))
            
            
        if text == "پیام به کاربر مشخص":
            await message_to_user_start(update, context)
            
            
        if text == "ارسال پیام همگانی":
            await broadcast_start(update, context)
            
            
        if text == "مدیریت کانالهای تبلیغاتی":
            
            channels_submenu = [
                ReplyKeyboardMarkup([[KeyboardButton("افزودن کانال جدید")],
                                    [KeyboardButton("بازگشت به منوی مدیریت")]], resize_keyboard=True)
                                ]
            
            channels = get_channels()
            if not channels:
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                                text="هیچ کانالی وجود ندارد.",
                                                reply_markup=channels_submenu[0])
                return
            
            
            count = 0
            for ch in channels:
                buttons = []
                
                channel_name = get_channel_name(ch)
                channel_link = get_channel_link(ch)
                delete_callback = f"delete_{ch}"
                edit_callback = f"edit_{ch}"
                buttons.append(InlineKeyboardButton("حذف", callback_data=delete_callback))
                buttons.append(InlineKeyboardButton(channel_name, url=channel_link))
                buttons.append(InlineKeyboardButton("ویرایش", callback_data=edit_callback))
                
                count += 1
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                                text=f"کانال {count}: {channel_name}",
                                                reply_markup=InlineKeyboardMarkup([buttons]))
                        
            
            
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                            text=f"تعداد کانال ها: {count}",
                                            reply_markup=channels_submenu[0])
            
            
        if text == "افزودن کانال جدید":
            await add_channel_start(update, context)
            
        
        if text == "بازگشت به منوی مدیریت":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="سلام ادمین جون",
                reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
            )
        
        if text == "دریافت لاگ پرامپت ها (txt)":
            await context.bot.send_message(chat_id=update.effective_chat.id, text="در حال آماده‌سازی فایل لاگ پرامپت‌ها...")
            file_path = generate_prompt_log_file()
            if file_path:
                with open(file_path, 'rb') as file:
                    await context.bot.send_document(chat_id=update.effective_chat.id, document=file)
                os.remove(file_path)
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="خطا در تولید فایل لاگ پرامپت‌ها.")    
            
        if text == "ارتقای کاربر به پرمیوم":
            await context.bot.send_message(chat_id=update.effective_chat.id, text="لطفا شناسه عددی کاربر را وارد کنید:",
                                            reply_markup=ReplyKeyboardMarkup(cancell_menu, resize_keyboard=True))
            return start_promote_user(update, context)
        
# -------------------------------------------------------------        

    if text == "وضعیت ها🔍":
        
        user_data = get_user_all_data(update.effective_user.id)
        print("user_data:", user_data)
        premium_status = "پرمیوم" if user_data[5] == 1 else "عادی"
        remaining_coupon = user_data[4]
        inviteds_count = user_data[6]

        await context.bot.send_message(chat_id=update.effective_chat.id, text= f"وضعیت شما:\nنوع اشتراک: {premium_status}\nتعداد کوپن‌های باقی‌مانده: {remaining_coupon}\nتعداد دعوت‌شدگان: {inviteds_count}")

    elif text == "شروع چت با هوش مصنوعی🤖":
        
        ozviat_result = await ozviat(update, context)
        if ozviat_result == True:
        
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                            text="شروع چت با هوش مصنوعی",
                                            reply_markup=ReplyKeyboardMarkup(ai_submenu, resize_keyboard=True))
            
            
    elif text == "شروع چت جدید":
        
        await ai_chat_start(update, context)
        
        
    elif text == "ادامه ی چت قبلی":
        
        await ai_chat_start(update, context)

    elif text == "پیام به ادمین💬":
        await feedback_start(update, context)


    elif text == "خرید اشتراک پرمیوم🔹":
        await context.bot.send_message(chat_id=update.effective_chat.id, text="این بخش فعلا در دسترس نیست")
        
    
    # elif text == "دعوت از دوستان📨":
    #     invite_link = create_invite_link(update.effective_user.id)
    #     await context.bot.send_message(chat_id=update.effective_chat.id,
    #                                     text=f"برای دعوت از دوستان خود، لینک زیر را ارسال کنید:\n\n{invite_link}")
        
    elif text == "بازگشت به منوی اصلی":
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text="به منوی اصلی بازگشتید",
                                        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))


async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    bot_status = get_bot_status()
    if bot_status != "active" and update.effective_user.id not in ADMIN_IDS:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="ربات در حال حاضر غیرفعال است.")
        return

    query = update.callback_query
    await query.answer()

    data = query.data
    
    
    if data.startswith("delete_"):
        username = data.split("delete_")[1]
        remove_channel(username)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text=f"کانال {username} حذف شد.",
                                        reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True))
    
    
    if data.startswith("edit_"):
        username = data.split("edit_")[1]
        pass
    
    
    if data == "check_membership":
        user_access = await ozviat(update, context)
        if user_access:
            await ai_chat_start(update, context)
        
    
    if data == "deactivate_bot":
        set_bot_status("inactive")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="ربات غیرفعال شد.")
        
        
    if data == "activate_bot":
        set_bot_status("active")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="ربات فعال شد.")
        
        
    if data == "admin_menu":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="سلام ادمین جون",
            reply_markup=ReplyKeyboardMarkup(admin_menu)
        )
        
        
        await add_channel_start(update, context)
    
    
async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    not_user = []
    for ch in get_channels():
        try:
            member = await context.bot.get_chat_member(ch, user_id=user_id)
            print(f"user: {user_id} status in channel: {ch} is: ", member.status)
            if member.status in ["left", "kicked", "restricted"]:
                not_user.append(ch)
        except Exception as e:
            print(f"Error checking membership for user {user_id} in channel {ch} : {e}")
    return not_user
    
    
async def ozviat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    channels = get_channels()

    not_joined = await check_membership(user.id, context)
    if not_joined == [] or channels == []:
        await context.bot.send_message(text="✅ دسترسی شما تایید شد.",
                                        chat_id=update.effective_user.id)
        
        return True
    
    else:
        
        inline_keyboard = []
        
        for ch in not_joined:
            channel_name = get_channel_name(ch)
            channel_link = get_channel_link(ch)
            button = [InlineKeyboardButton(text=channel_name, url=channel_link)]
            inline_keyboard.append(button)
            
        last_button = [InlineKeyboardButton(text="بررسی عضویت🔄", callback_data="check_membership")]
        inline_keyboard.append(last_button)
        
        ozviat_text = "⚠️ برای استفاده از ربات، ابتدا در کانال‌های زیر عضو شوید:\n\n"
        
        await context.bot.send_message(chat_id=update.effective_user.id,
                                        text=ozviat_text,
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard))
        return False


PROMOTE, FEEDBACK_MESSAGE, BROADCAST_MESSAGE, ADD_CHANNEL_USERNAME, ADD_CHANNEL_NAME, ADD_CHANNEL_LINK, AI_CHAT = range(7)


async def feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفا پیام خود را وارد کنید:\n(پیام میتواند شامل متن، عکس، ویدئو یا فایل باشد)",
                                    reply_markup=ReplyKeyboardMarkup(cancell_menu, resize_keyboard=True))
    return FEEDBACK_MESSAGE

async def feedback_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    msg = update.message

    if msg.text == "انصراف❌":
        await feedback_cancel(update, context)
        return ConversationHandler.END

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📩 پیام جدید از {user.full_name} ({user.id}):"
            )

            sent = await context.bot.copy_message(
                    chat_id=admin_id,
                    from_chat_id=msg.chat_id,
                    message_id=msg.message_id
                )
            
            # ذخیره‌ی آیدی کاربر اصلی
            context.bot_data[sent.message_id] = user.id
            
        except Exception as e:
            await context.bot.send_message(chat_id=admin_id, text=f"خطا در ارسال پیام کاربر به {admin_id}: {e}")
    
    await update.message.reply_text("پیام شما به ادمین ارسال شد✅",
                                    reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
    return ConversationHandler.END


async def feedback_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ارسال پیام به ادمین لغو شد.",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )
    return ConversationHandler.END


feedback_conv = ConversationHandler(
                entry_points=[MessageHandler(filters.Regex("^پیام به ادمین💬$"), feedback_start)],
                states={
                    FEEDBACK_MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, feedback_message)],
                },
                fallbacks=[MessageHandler(filters.Regex("^انصراف❌$"), feedback_cancel)],
)
    
    
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفا پیام همگانی خود را وارد کنید:",
                                    reply_markup=ReplyKeyboardMarkup(cancell_menu, resize_keyboard=True))
    return BROADCAST_MESSAGE


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.text == "انصراف❌":
        await broadcast_cancel(update, context)
        return ConversationHandler.END

    total_users = get_total_users()
    sent_count = 0
    failed_count = 0

    for user_id in get_all_user_ids():
        try:
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id
            )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            print(f"error in sending broadcast to {user_id}: {e}")

    await update.message.reply_text(
        f"پیام همگانی ارسال شد.\n\nتعداد کل کاربران: {total_users}\nپیام‌های موفق: {sent_count}\nپیام‌های ناموفق: {failed_count}",
        reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
    )
    return ConversationHandler.END


async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ارسال پیام همگانی لغو شد.",
        reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
    )
    return ConversationHandler.END

    
broadcast_conv = ConversationHandler(
                entry_points=[MessageHandler(filters.Regex("^ارسال پیام همگانی$"), broadcast_start)],
                states={
                    BROADCAST_MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_message)],
                },
                fallbacks=[MessageHandler(filters.Regex("^انصراف❌$"), broadcast_cancel)],
)
    
    
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if update.effective_user.id not in ADMIN_IDS:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="شما ادمین ربات نیستید")
        return ConversationHandler.END
    
    
    await update.message.reply_text(text="لطفا شناسه ی عددی کانال را وارد کنید(مثال: 1001234567890-):",
                                    reply_markup=ReplyKeyboardMarkup(cancell_menu, resize_keyboard=True))
    
    return ADD_CHANNEL_USERNAME


async def add_channel_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text
    
    if username == "انصراف❌":
        await add_channel_cancel(update, context)
        return ConversationHandler.END
    
    context.user_data['new_channel_username'] = username
    await update.message.reply_text("لطفا نام کانال را وارد کنید:",
                                    reply_markup=ReplyKeyboardMarkup(cancell_menu, resize_keyboard=True))
    return ADD_CHANNEL_NAME


async def add_channel_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_name = update.message.text
    
    if channel_name == "انصراف❌":
        await add_channel_cancel(update, context)
        return ConversationHandler.END
    
    context.user_data['new_channel_name'] = channel_name
    await update.message.reply_text("لطفا لینک کانال را وارد کنید:",
                                    reply_markup=ReplyKeyboardMarkup(cancell_menu, resize_keyboard=True))
    return ADD_CHANNEL_LINK


async def add_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_link = update.message.text
    
    if channel_link == "انصراف❌":
        await add_channel_cancel(update, context)
        return ConversationHandler.END
    
    username = context.user_data['new_channel_username']
    channel_name = context.user_data['new_channel_name']
    
    add_channel(username, channel_name, channel_link)
    
    await update.message.reply_text(f"کانال {channel_name} با موفقیت اضافه شد.",
                                    reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True))
    
    return ConversationHandler.END


async def add_channel_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("افزودن کانال لغو شد.",
                                    reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True))
    return ConversationHandler.END


add_channel_conv = ConversationHandler(
                entry_points=[MessageHandler(filters.Regex("^افزودن کانال جدید$"), add_channel_start)],
                states={
                    ADD_CHANNEL_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_username)],
                    ADD_CHANNEL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_name)],
                    ADD_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_link)],
                },
                fallbacks=[MessageHandler(filters.Regex("^انصراف❌$"), add_channel_cancel)],
)

# -----------------------------------------------------

MESSAGE_TO_USER, MESSAGE_TO_USER_MESSAGE = range(2)

async def message_to_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفا شناسه عددی کاربر را وارد کنید:",
                                    reply_markup=ReplyKeyboardMarkup(cancell_menu, resize_keyboard=True))
    return MESSAGE_TO_USER


async def message_to_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id_text = update.message.text

    if user_id_text == "انصراف❌":
        await message_to_user_cancel(update, context)
        return ConversationHandler.END

    try:
        user_id = int(user_id_text)
        context.user_data['target_user_id'] = user_id
        await update.message.reply_text("لطفا پیام خود را وارد کنید:",
                                        reply_markup=ReplyKeyboardMarkup(cancell_menu, resize_keyboard=True))
        return MESSAGE_TO_USER_MESSAGE
    except ValueError:
        await update.message.reply_text("شناسه کاربر نامعتبر است. لطفا یک شناسه عددی معتبر وارد کنید:")
        return MESSAGE_TO_USER
    
    
async def message_to_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    target_user_id = context.user_data['target_user_id']

    if msg.text == "انصراف❌":
        await message_to_user_cancel(update, context)
        return ConversationHandler.END

    try:
        await context.bot.copy_message(
            chat_id=target_user_id,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id
        )
        await update.message.reply_text("پیام با موفقیت ارسال شد.",
                                        reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True))
    except Exception as e:
        await update.message.reply_text(f"خطا در ارسال پیام به کاربر: {e}",
                                        reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True))

    return ConversationHandler.END


async def message_to_user_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ارسال پیام به کاربر لغو شد.",
                                    reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True))
    return ConversationHandler.END


message_to_user_conv = ConversationHandler(
                entry_points=[MessageHandler(filters.Regex("^پیام به کاربر مشخص$"), message_to_user_start)],
                states={
                    MESSAGE_TO_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, message_to_user_id)],
                    MESSAGE_TO_USER_MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, message_to_user_message)],
                },
                fallbacks=[MessageHandler(filters.Regex("^انصراف❌$"), message_to_user_cancel)],
)

# --------------------------------------------------------

def diff_seconds(time1: str, time2: str) -> int:
    """
    اختلاف دو زمان با فرمت 'YYYY-MM-DD HH:MM:SS' را به ثانیه برمی‌گرداند
    """
    fmt = "%Y-%m-%d %H:%M:%S"

    t1 = datetime.strptime(time1, fmt)
    t2 = datetime.strptime(time2, fmt)

    return abs(int((t2 - t1).total_seconds()))

# --------------------------------------------------

async def ai_chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    bot_status = get_bot_status()
    if bot_status != "active" and update.effective_user.id not in ADMIN_IDS:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="ربات در حال حاضر غیرفعال است.")
        return

    if update.message.text == "ادامه ی چت قبلی":
        
        last_message = get_last_message(update.effective_user.id)
        modified_message = f"<b>آخرین پیام های شما:\nپرامپت:</b>\n{last_message[0]}\n<b>پاسخ دارک جی پی تی:</b>\n{last_message[1]}"
        await send_long_message(update, context, text=modified_message, chunk_size=4096)
        await context.bot.send_message(chat_id=update.effective_user.id,
                                        text="چت با هوش مصنوعی ادامه یافت. لطفا پیام خود را ارسال کنید:",
                                        reply_markup=ReplyKeyboardMarkup([["انصراف❌"]], resize_keyboard=True))
        return AI_CHAT

    if update.message.text == "شروع چت جدید":

        clear_chat_history(update.effective_user.id)
        await update.message.reply_text("چت با هوش مصنوعی شروع شد. لطفا پیام خود را ارسال کنید:",
                                        reply_markup=ReplyKeyboardMarkup([["انصراف❌"]], resize_keyboard=True))
        return AI_CHAT

    return AI_CHAT


async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    ai_reply = ""
    response = None
    chat_history = get_user_chat_history(user_id)

    if user_message == "انصراف❌":
        await ai_chat_end(update, context)
        return ConversationHandler.END

    current_time = get_current_time()
    premium_status = get_user_premium_status(user_id)
    user_coupons = get_user_coupon(user_id)
    last_message_time = get_last_message(user_id)[2] if get_last_message(user_id)[2] else current_time

    difference = diff_seconds(current_time, last_message_time)
    
    if user_coupons < 1 and difference >= 86400:
        user_current_daily_coupons = get_user_daily_coupons(user_id)
        set_remaining_coupons(user_id, user_current_daily_coupons)

    if user_coupons < 1 and premium_status == 0:
        await update.message.reply_text("شما اعتبار کافی برای استفاده از هوش مصنوعی را ندارید.\n24 ساعت دیگر می‌توانید دوباره امتحان کنید.")
        await ai_chat_end(update, context)
        return ConversationHandler.END

    SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT")
    
    full_prompt = (
        SYSTEM_PROMPT
        + ("\n\n" + chat_history if chat_history else "")
        + f"\nprompt: {user_message}\nresponse:"
    )
    
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    loop = asyncio.get_running_loop()
    
    try:
        async with AI_SEMAPHORE:
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    generate_with_liara,
                    full_prompt
                ),
                timeout=AI_TIMEOUT
            )

    except asyncio.TimeoutError:
        response = None
        ai_reply = "⏱️ پاسخ هوش مصنوعی بیش از حد طول کشید. لطفاً دوباره تلاش کنید."

    except Exception as e:
        print(f"AI Error: {e}")
        response = None
        ai_reply = "❌ خطا در ارتباط با هوش مصنوعی."
    
    if response:
        ai_reply = response
    else:
        ai_reply = "پاسخی از هوش مصنوعی دریافت نشد."

    try:
        set_chat_history(user_id, user_message, ai_reply)
        add_prompt_log(user_id, user_message, ai_reply)
    except Exception as e:
        print(f"Error occurred while saving chat history: {e}")
    
    try:
        await send_long_message(update, context, text=ai_reply, chunk_size=4096)
    except Exception as e:
        print(f"Error occurred while sending long message: {e}")

    if ai_reply not in ["پاسخی از هوش مصنوعی دریافت نشد.", "خطا در تولید پاسخ"] and premium_status == 0:
        decrement_user_coupon(user_id)
        
    history_l = await history_length(user_id)
    if history_l > 20:
        decrement_chat_history(user_id)

    return AI_CHAT


async def ai_chat_end(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(text="به منوی اصلی بازگشتید.",
                                    chat_id=update.effective_user.id,
                                    reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
    return ConversationHandler.END


ai_chat_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^شروع چت جدید$"), ai_chat_start), MessageHandler(filters.Regex("^ادامه ی چت قبلی$"), ai_chat_start)],
    states={
        AI_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat)],
    },
    fallbacks=[MessageHandler(filters.Regex("^انصراف❌$"), ai_chat_end)],
)

# ---------------------------------------------------------------------------------------

# def get_next_api_key():
#     api_keys = [
#         GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, GOOGLE_API_KEY_3,
#         GOOGLE_API_KEY_4, GOOGLE_API_KEY_5
#     ]
#     for key in api_keys:
#         if key:
#             return key
#     raise Exception("No valid API key found")

# ---------------------------------------------------------------------------------------

# def generate_ai_response(full_prompt):

#     API_KEY = GOOGLE_API_KEY_1
    
#     client = genai.Client(api_key=API_KEY)
#     try:
#         response = client.models.generate_content(
#             model="gemini-2.5-flash-preview-09-2025",
#             contents=full_prompt
#         )
#         return response.text
#     except Exception as e:
#         print(f"Error occurred while generating AI response: {e}")
#         return None

# -------------------------------------------------------------------------------------

async def admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    replied_msg_id = update.message.reply_to_message.message_id
    user_id = context.bot_data.get(replied_msg_id)

    if not user_id:
        
        await update.message.reply_text("❌ شناسه‌ی کاربر پیدا نشد.")
        return
        
    else:
        # کپی کردن پیام ادمین برای کاربر
        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id
        )
        await update.message.reply_text("با موفقیت ارسال شد")

# --------------------------------------------------------------------------------------

async def start_promote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفا شناسه عددی کاربر را وارد کنید:",
                                    reply_markup=ReplyKeyboardMarkup(cancell_menu, resize_keyboard=True))
    return PROMOTE

async def promote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if update.message.text == "انصراف❌":
        await promote_user_cancel(update, context)
        return ConversationHandler.END
    
    try:
        user_id_to_promote = int(update.message.text)
    except ValueError:
        await update.message.reply_text("شناسه‌ی وارد شده معتبر نیست. لطفا یک شناسه‌ی عددی وارد کنید.",
                                        reply_markup=ReplyKeyboardMarkup(cancell_menu, resize_keyboard=True))
        return PROMOTE
    
    if not user_exists(user_id_to_promote):
        await update.message.reply_text("کاربری با این شناسه وجود ندارد.",
                                        reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True))
        return ConversationHandler.END
    
    set_user_premium_status(user_id_to_promote, 1)
    await update.message.reply_text(f"کاربر با شناسه {user_id_to_promote} به پرمیوم ارتقا یافت.",
                                    reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True))
    return ConversationHandler.END


async def promote_user_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ارتقای کاربر لغو شد.",
                                    reply_markup=ReplyKeyboardMarkup(admin_menu, resize_keyboard=True))
    return ConversationHandler.END

promote_user_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^ارتقای کاربر به پرمیوم$"), start_promote_user)],
    states={
        PROMOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, promote_user)],
    },
    fallbacks=[MessageHandler(filters.Regex("^انصراف❌$"), promote_user_cancel)],
)

# --------------------------------------------------------------------------------------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'update {update} caused error {context.error}')
    
if __name__ == "__main__":
    print("Bot is starting...")
    application = Application.builder().token(BOT_TOKEN).concurrent_updates(5).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(ai_chat_conv)
    application.add_handler(feedback_conv)
    application.add_handler(broadcast_conv)
    application.add_handler(add_channel_conv)
    application.add_handler(promote_user_conv)
    application.add_handler(message_to_user_conv)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))
    application.add_handler(CallbackQueryHandler(inline_handler))
    application.add_error_handler(error_handler)
    print("Bot is running...")
    application.run_polling()