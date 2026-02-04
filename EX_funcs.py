# import mysql.connector
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")

# cnx = mysql.connector.connect(
#     host="127.0.0.1",
#     port=3306,
#     user="root",
#     password=DATABASE_PASSWORD,
#     database="dark_gpt")
# cur = cnx.cursor()

cnx = sqlite3.connect('db.sqlite3')
cur = cnx.cursor()


async def send_long_message(update, context, text: str, chunk_size: int = 4000):
    """پیام های طولانی را به اندازه ی پیام های تلگرام میشکند و در چند پیام ارسال میکند

    Args:
        update (=update): از آپدیت تلگرام به این تابع پاس داده میشود
        text (str): متن مورد نظر
        chunk_size (int, optional): در هر پیام چند کاراکتر وجود داشته باشد. Defaults to 4000.
    """
    for i in range(0, len(text), chunk_size):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text=text[i:i+chunk_size],
                                        parse_mode="HTML")


async def history_length(user_id):
    """تعداد پیام های تاریخچه چت کاربر را برمیگرداند

    Args:
        user_id (int): شناسه کاربر

    Returns:
        int: تعداد پیام های تاریخچه چت
    """
    query = "SELECT COUNT(*) FROM user_prompts WHERE user_id = ?"
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    return result[0] if result else 0

def create_invite_link(user_id: int) -> str:
    """لینک دعوت اختصاصی برای کاربر ایجاد میکند

    Args:
        user_id (int): شناسه کاربر

    Returns:
        str: لینک دعوت
    """
    BOT_USERNAME = os.environ.get("BOT_USERNAME")
    invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    return invite_link