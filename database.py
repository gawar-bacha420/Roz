import sqlite3
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
import os

DB_PATH = Path(__file__).parent / 'users.db'
ENCRYPTION_KEY_FILE = Path(__file__).parent / '.encryption_key'

ADMIN_USERNAME = "RAJ-PATHAK"
ADMIN_PASSWORD = "RAJ@ADMIN#2025"

def get_encryption_key():
    if ENCRYPTION_KEY_FILE.exists():
        with open(ENCRYPTION_KEY_FILE, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(ENCRYPTION_KEY_FILE, 'wb') as f:
            f.write(key)
        return key

ENCRYPTION_KEY = get_encryption_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_approved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_id TEXT,
            name_prefix TEXT,
            delay INTEGER DEFAULT 30,
            cookies_encrypted TEXT,
            messages TEXT,
            automation_running INTEGER DEFAULT 0,
            locked_group_name TEXT,
            locked_nicknames TEXT,
            lock_enabled INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Migrate existing tables
    for col, definition in [
        ('automation_running', 'INTEGER DEFAULT 0'),
        ('locked_group_name', 'TEXT'),
        ('locked_nicknames', 'TEXT'),
        ('lock_enabled', 'INTEGER DEFAULT 0'),
    ]:
        try:
            cursor.execute(f'ALTER TABLE user_configs ADD COLUMN {col} {definition}')
            conn.commit()
        except sqlite3.OperationalError:
            pass

    for col, definition in [
        ('is_admin', 'INTEGER DEFAULT 0'),
        ('is_approved', 'INTEGER DEFAULT 0'),
    ]:
        try:
            cursor.execute(f'ALTER TABLE users ADD COLUMN {col} {definition}')
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # Ensure admin account exists
    cursor.execute('SELECT id FROM users WHERE username = ?', (ADMIN_USERNAME,))
    if not cursor.fetchone():
        ph = hash_password(ADMIN_PASSWORD)
        cursor.execute(
            'INSERT INTO users (username, password_hash, is_admin, is_approved) VALUES (?, ?, 1, 1)',
            (ADMIN_USERNAME, ph)
        )
        admin_id = cursor.lastrowid
        cursor.execute(
            'INSERT INTO user_configs (user_id, chat_id, name_prefix, delay, messages) VALUES (?, ?, ?, ?, ?)',
            (admin_id, '', '', 30, '')
        )
    else:
        # Make sure existing admin is approved
        cursor.execute(
            'UPDATE users SET is_admin=1, is_approved=1 WHERE username=?',
            (ADMIN_USERNAME,)
        )

    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def encrypt_cookies(cookies):
    if not cookies:
        return None
    return cipher_suite.encrypt(cookies.encode()).decode()

def decrypt_cookies(encrypted_cookies):
    if not encrypted_cookies:
        return ""
    try:
        return cipher_suite.decrypt(encrypted_cookies.encode()).decode()
    except:
        return ""

def create_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        password_hash = hash_password(password)
        # New users are NOT approved by default (admin must approve)
        cursor.execute(
            'INSERT INTO users (username, password_hash, is_admin, is_approved) VALUES (?, ?, 0, 0)',
            (username, password_hash)
        )
        user_id = cursor.lastrowid
        cursor.execute(
            'INSERT INTO user_configs (user_id, chat_id, name_prefix, delay, messages) VALUES (?, ?, ?, ?, ?)',
            (user_id, '', '', 30, '')
        )
        conn.commit()
        conn.close()
        return True, "Account created! Admin approval ka wait karo."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists!"
    except Exception as e:
        conn.close()
        return False, f"Error: {str(e)}"

def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    if user and user[1] == hash_password(password):
        return user[0]
    return None

def is_approved(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT is_approved, is_admin FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return bool(row[0]) or bool(row[1])
    return False

def is_admin(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return bool(row[0]) if row else False

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.id, u.username, u.is_admin, u.is_approved, u.created_at
        FROM users u
        ORDER BY u.created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [
        {'id': r[0], 'username': r[1], 'is_admin': bool(r[2]),
         'is_approved': bool(r[3]), 'created_at': r[4]}
        for r in rows
    ]

def set_user_approved(user_id, approved):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_approved = ? WHERE id = ?', (1 if approved else 0, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_configs WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_user_config(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT chat_id, name_prefix, delay, cookies_encrypted, messages, automation_running
        FROM user_configs WHERE user_id = ?
    ''', (user_id,))
    config = cursor.fetchone()
    conn.close()
    if config:
        return {
            'chat_id': config[0] or '',
            'name_prefix': config[1] or '',
            'delay': config[2] or 30,
            'cookies': decrypt_cookies(config[3]),
            'messages': config[4] or '',
            'automation_running': config[5] or 0
        }
    return None

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    encrypted_cookies = encrypt_cookies(cookies)
    cursor.execute('''
        UPDATE user_configs
        SET chat_id = ?, name_prefix = ?, delay = ?, cookies_encrypted = ?,
            messages = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (chat_id, name_prefix, delay, encrypted_cookies, messages, user_id))
    conn.commit()
    conn.close()

def get_username(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def get_user_id_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_automation_running(user_id, is_running):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_configs
        SET automation_running = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (1 if is_running else 0, user_id))
    conn.commit()
    conn.close()

def get_automation_running(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT automation_running FROM user_configs WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return bool(result[0]) if result else False

def get_lock_config(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT chat_id, locked_group_name, locked_nicknames, lock_enabled, cookies_encrypted
        FROM user_configs WHERE user_id = ?
    ''', (user_id,))
    config = cursor.fetchone()
    conn.close()
    if config:
        import json
        try:
            nicknames = json.loads(config[2]) if config[2] else {}
        except:
            nicknames = {}
        return {
            'chat_id': config[0] or '',
            'locked_group_name': config[1] or '',
            'locked_nicknames': nicknames,
            'lock_enabled': bool(config[3]),
            'cookies': decrypt_cookies(config[4])
        }
    return None

def update_lock_config(user_id, chat_id, locked_group_name, locked_nicknames, cookies=None):
    import json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    nicknames_json = json.dumps(locked_nicknames)
    if cookies is not None:
        encrypted_cookies = encrypt_cookies(cookies)
        cursor.execute('''
            UPDATE user_configs
            SET chat_id = ?, locked_group_name = ?, locked_nicknames = ?,
                cookies_encrypted = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (chat_id, locked_group_name, nicknames_json, encrypted_cookies, user_id))
    else:
        cursor.execute('''
            UPDATE user_configs
            SET chat_id = ?, locked_group_name = ?, locked_nicknames = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (chat_id, locked_group_name, nicknames_json, user_id))
    conn.commit()
    conn.close()

def set_lock_enabled(user_id, enabled):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_configs
        SET lock_enabled = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (1 if enabled else 0, user_id))
    conn.commit()
    conn.close()

def get_lock_enabled(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT lock_enabled FROM user_configs WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return bool(result[0]) if result else False

def username_exists(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE LOWER(username) = LOWER(?)', (username,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def save_fb_account(user_id, account_name, cookies):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_fb_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_name TEXT NOT NULL,
                cookies_encrypted TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        encrypted = encrypt_cookies(cookies)
        cursor.execute(
            'INSERT INTO saved_fb_accounts (user_id, account_name, cookies_encrypted) VALUES (?,?,?)',
            (user_id, account_name, encrypted)
        )
        conn.commit()
        conn.close()
        return True, "Account saved!"
    except Exception as e:
        conn.close()
        return False, str(e)

def get_saved_accounts(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_fb_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_name TEXT NOT NULL,
                cookies_encrypted TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute(
            'SELECT id, account_name, cookies_encrypted, created_at FROM saved_fb_accounts WHERE user_id=? ORDER BY created_at DESC',
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {'id': r[0], 'name': r[1], 'cookies': decrypt_cookies(r[2]), 'created_at': r[3]}
            for r in rows
        ]
    except Exception:
        conn.close()
        return []

def delete_saved_account(account_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM saved_fb_accounts WHERE id=? AND user_id=?', (account_id, user_id))
        conn.commit()
    except Exception:
        pass
    conn.close()

def get_admin_e2ee_thread_id(user_id, current_cookies):
    return None, None

def clear_admin_e2ee_thread_id(user_id):
    pass

init_db()
