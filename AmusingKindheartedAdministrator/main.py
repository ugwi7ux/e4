import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, PicklePersistence
import asyncio
import threading
from waitress import serve

app = Flask(__name__, template_folder='templates', static_folder='static')

GROUP_ID = -1002445433249
ADMIN_ID = 6243639789
BOT_TOKEN = os.getenv('BOT_TOKEN')


def init_db():
    with sqlite3.connect('interactions.db') as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            message_count INTEGER DEFAULT 0,
            last_interaction TEXT
        )
        ''')


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/dashboard')
def dashboard_redirect():
    return render_template('dashboard.html')


@app.route('/api/top_members')
def api_top_members():
    try:
        with sqlite3.connect('interactions.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
            SELECT user_id, username, first_name, last_name, message_count 
            FROM users 
            ORDER BY message_count DESC 
            LIMIT 20
            ''')
            members = [dict(row) for row in cursor.fetchall()]
        return jsonify(members)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id == GROUP_ID:
        await update.message.reply_text('مرحباً بكم في بوت تفاعل SM 1%!')


async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    user = update.effective_user
    now = datetime.now().isoformat()

    with sqlite3.connect('interactions.db') as conn:
        conn.execute('''
        INSERT OR IGNORE INTO users 
        (user_id, username, first_name, last_name, message_count, last_interaction)
        VALUES (?, ?, ?, ?, 0, ?)
        ''', (user.id, user.username, user.first_name, user.last_name, now))

        conn.execute('''
        UPDATE users SET 
            message_count = message_count + 1,
            username = ?,
            first_name = ?,
            last_name = ?,
            last_interaction = ?
        WHERE user_id = ?
        ''', (user.username, user.first_name, user.last_name, now, user.id))


async def top_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    with sqlite3.connect('interactions.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
        SELECT username, first_name, last_name, message_count 
        FROM users 
        ORDER BY message_count DESC 
        LIMIT 10
        ''')

        response = "\ud83c\udfc6 \u0623\u0641\u0636\u0644 10 \u0623\u0639\u0636\u0627\u0621 \u0645\u062a\u0641\u0627\u0639\u0644\u064a\u0646:\n\n"
        for idx, row in enumerate(cursor.fetchall(), 1):
            name = f"@{row['username']}" if row['username'] else f"{row['first_name']} {row['last_name']}".strip()
            response += f"{idx}. {name} - {row['message_count']} \u0631\u0633\u0627\u0644\u0629\n"

    await update.message.reply_text(response)


async def my_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    user = update.effective_user
    with sqlite3.connect('interactions.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT message_count FROM users WHERE user_id = ?', (user.id,))
        user_data = cursor.fetchone()

        if not user_data:
            await update.message.reply_text("\u0644\u0645 \u064a\u062a\u0645 \u0627\u0644\u0639\u062b\u0648\u0631 \u0639\u0644\u0649 \u0628\u064a\u0627\u0646\u0627\u062a \u062a\u0641\u0627\u0639\u0644 \u0644\u0643.")
            return

        cursor.execute('SELECT COUNT(*) FROM users WHERE message_count > ?', (user_data[0],))
        rank = cursor.fetchone()[0] + 1

    await update.message.reply_text(f"\ud83d\udcca \u062a\u0631\u062a\u064a\u0628\u0643: {rank}\n\u2709\ufe0f \u0639\u062f\u062f \u0627\u0644\u0631\u0633\u0627\u0626\u0644: {user_data[0]}")


async def run_bot():
    init_db()
    persistence = PicklePersistence(filepath='bot_data')
    application = Application.builder().token(BOT_TOKEN).persistence(persistence).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("top", top_members))
    application.add_handler(CommandHandler("my", my_rank))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))

    print("\ud83e\udd16 \u0628\u062f\u0621 \u062a\u0634\u063a\u064a\u0644 \u0628\u0648\u062a \u0627\u0644\u062a\u0644\u064a\u062c\u0631\u0627\u0645...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.wait_until_shutdown()


def run_flask():
    port = int(os.getenv('PORT', 8080))
    print(f"\ud83c\udf10 \u0628\u062f\u0621 \u062e\u0627\u062f\u0645 \u0627\u0644\u0648\u064a\u0628 \u0639\u0644\u0649 \u0627\u0644\u0645\u0646\u0641\u0630 {port}")
    serve(app, host="0.0.0.0", port=port)


def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\ud83d\udd1a \u062a\u0645 \u0625\u064a\u0642\u0627\u0641 \u0627\u0644\u0628\u0648\u062a")
    except Exception as e:
        print(f"\ud83d\udd25 \u062e\u0637\u0623 \u063a\u064a\u0631 \u0645\u062a\u0648\u0642\u0639: {str(e)}")


if __name__ == '__main__':
    main()
