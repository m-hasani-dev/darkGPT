# import mysql.connector
import sqlite3
import os
from dotenv import load_dotenv
import time

load_dotenv()

# DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT")

# cnx = mysql.connector.connect(
#     host="127.0.0.1",
#     port=3306,
#     user="root",
#     password=DATABASE_PASSWORD,
#     database="dark_gpt")
# cur = cnx.cursor()

cnx = sqlite3.connect('db.sqlite3')
cur = cnx.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users_table (
    ID INTEGER PRIMARY KEY,
    name TEXT,
    username TEXT,
    user_coupons INTEGER,
    remaining_coupons INTEGER,
    premium INTEGER,
    inviteds INTEGER,
    entering_date TEXT,
    last_use TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS user_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    prompt TEXT,
    response TEXT,
    timestamp TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS settings_table (
    id INTEGER PRIMARY KEY,
    normal_daily_coupon INTEGER,
    bot_status TEXT,
    system_prompt TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS channels (
    username TEXT PRIMARY KEY,
    channel_name TEXT,
    channel_link TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS prompt_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    prompt TEXT,
    ai_response TEXT,
    log_time TEXT
)
""")

cur.execute("INSERT OR IGNORE INTO settings_table (id, normal_daily_coupon, bot_status, system_prompt) VALUES (1, 7, 'active', ?)", (SYSTEM_PROMPT,))
cnx.commit()

cur.execute("SELECT normal_daily_coupon FROM settings_table")
DAILY_COUPON = cur.fetchone()[0]


def get_user_all_data(user_id):
    query = "SELECT * FROM users_table WHERE ID = ?"
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    return result


def get_user_premium_status(user_id):
    query = "SELECT premium FROM users_table WHERE ID = ?"
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    return result[0] if result else None


def set_user_premium_status(user_id, status):
    query = "UPDATE users_table SET premium = ? WHERE ID = ?"
    cur.execute(query, (status, user_id))
    cnx.commit()
    

def add_new_user(user_id, username, name):
    query = "INSERT INTO users_table (ID, name, username, user_coupons, remaining_coupons, premium, inviteds, entering_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    cur.execute(query, (user_id, name, username, DAILY_COUPON, DAILY_COUPON, 0, 0, get_current_time()))
    cnx.commit()
    
    
def user_exists(user_id):
    query = "SELECT COUNT(*) FROM users_table WHERE ID = ?"
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    return result[0] > 0
    
    
def get_user_inviteds(user_id):
    query = "SELECT inviteds FROM users_table WHERE ID = ?"
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    return result[0] if result else None


def increment_user_inviteds(user_id):
    query = "UPDATE users_table SET inviteds = inviteds + 1 WHERE ID = ?"
    cur.execute(query, (user_id,))
    cnx.commit()
    
    
def set_user_last_use(user_id, last_use):
    query = "UPDATE users_table SET last_use = ? WHERE ID = ?"
    cur.execute(query, (last_use, user_id))
    cnx.commit(
    )
    
    
def get_user_last_use(user_id):
    query = "SELECT last_use FROM users_table WHERE ID = ?"
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    return result[0] if result else None


def get_current_time():
    """Returns the current time in a formatted string."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def close_connection():
    cur.close()
    cnx.close()
    
    
def get_channels():
    cur.execute("SELECT username FROM channels")
    channels = [row[0] for row in cur.fetchall()]
    return channels


def get_channel_name(username):
    cur.execute("SELECT channel_name FROM channels WHERE username = ?", (username,))
    result = cur.fetchone()
    return result[0] if result else None
    
    
def get_channel_link(username):
    cur.execute("SELECT channel_link FROM channels WHERE username = ?", (username,))
    result = cur.fetchone()
    return result[0] if result else None
    
    
def add_channel(username, channel_name, channel_link):
    try:
        cur.execute("INSERT INTO channels (username, channel_name, channel_link) VALUES (?, ?, ?)", (username, channel_name, channel_link))
        cnx.commit()
    except sqlite3.IntegrityError:
        print("Channel already exists.")
    
    
def remove_channel(username):
    cur.execute("DELETE FROM channels WHERE username = ?", (username,))
    cnx.commit()
    
    
def get_total_users():
    cur.execute("SELECT COUNT(*) FROM users_table")
    result = cur.fetchone()
    return result[0] if result else 0
    
    
def get_premium_users_count():
    cur.execute("SELECT COUNT(*) FROM users_table WHERE premium = 1")
    result = cur.fetchone()
    return result[0] if result else 0
    
    
def get_bot_status():
    cur.execute("SELECT bot_status FROM settings_table WHERE id = 1")
    result = cur.fetchone()
    return result[0] if result else ""


def set_bot_status(status):
    cur.execute("UPDATE settings_table SET bot_status = ? WHERE id = 1", (status,))
    cnx.commit()
    
    
def get_all_user_ids():
    cur.execute("SELECT ID FROM users_table")
    user_ids = [row[0] for row in cur.fetchall()]
    return user_ids


def get_system_prompt():
    query = "SELECT system_prompt FROM settings_table WHERE id = 1"
    cur.execute(query)
    result = cur.fetchone()
    return result[0] if result else ""


def get_user_coupon(user_id):
    query = "SELECT remaining_coupons FROM users_table WHERE ID = ?"
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    return result[0] if result else None


def decrement_user_coupon(user_id):
    query = "UPDATE users_table SET remaining_coupons = remaining_coupons - 1 WHERE ID = ?"
    cur.execute(query, (user_id,))
    cnx.commit()


def get_user_chat_history(user_id):
    query = "SELECT prompt, response FROM user_prompts WHERE user_id = ?"
    cur.execute(query, (user_id,))
    prompts = cur.fetchall()
    result = ""
    for prompt in prompts:
        result += f"Prompt: {prompt[0]}, Response: {prompt[1]}\n"
    return result


def set_chat_history(user_id, prompt, response):
    query = "INSERT INTO user_prompts (user_id, prompt, response, timestamp) VALUES (?, ?, ?, ?)"
    cur.execute(query, (user_id, prompt, response, get_current_time()))
    cnx.commit()


def clear_chat_history(user_id):
    cur.execute("DELETE FROM user_prompts WHERE user_id = ?", (user_id,))
    cnx.commit()
    return True
    
    
def decrement_chat_history(user_id):
    query = "DELETE FROM user_prompts WHERE user_id = ? ORDER BY id ASC LIMIT 1"
    cur.execute(query, (user_id,))
    cnx.commit()
    
    
def get_last_message(user_id):
    """returns a tuple of prompt and response

    Args:
        user_id (str): user id

    Returns:
        tuple: (prompt, response)
    """
    query = "SELECT prompt, response, timestamp FROM user_prompts WHERE user_id = ? ORDER BY id DESC LIMIT 1"
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    return result if result else (None, None, None)

def add_prompt_log(user_id, prompt, ai_response):
    query = "INSERT INTO prompt_logs (user_id, prompt, ai_response, log_time) VALUES (?, ?, ?, ?)"
    cur.execute(query, (user_id, prompt, ai_response, get_current_time()))
    cnx.commit()

def generate_prompt_log_file():
    """Generates a text file containing all prompt logs.

    Returns:
        str: The path to the generated text file.
    """
    cur.execute("SELECT user_id, prompt, ai_response, log_time FROM prompt_logs")
    logs = cur.fetchall()
    
    file_path = "prompt_logs.txt"
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            for log in logs:
                file.write(f"User ID: {log[0]}\nPrompt: {log[1]}\nAI Response: {log[2]}\nLog Time: {log[3]}\n\n")
        return file_path
    except Exception as e:
        print(f"Error generating log file: {e}")
        return None
    
def set_remaining_coupons(user_id, coupons):
    query = "UPDATE users_table SET remaining_coupons = ? WHERE ID = ?"
    cur.execute(query, (coupons, user_id))
    cnx.commit()
    
def set_user_daily_coupons(user_id, coupons):
    query = "UPDATE users_table SET user_coupons = ? WHERE ID = ?"
    cur.execute(query, (coupons, user_id))
    cnx.commit()
    
def get_user_daily_coupons(user_id):
    query = "SELECT user_coupons FROM users_table WHERE ID = ?"
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    return result[0] if result else None
    