import os
import sqlite3
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import threading
from waitress import serve

# Initialize Flask app with CORS
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Bot configuration from environment variables
GROUP_ID = int(os.getenv('GROUP_ID', '-1002445433249'))
ADMIN_ID = int(os.getenv('ADMIN_ID', '6243639789'))
BOT_TOKEN = os.getenv('BOT_TOKEN', '6037757983:AAG5qtoMZrIuUMpI8-Mta3KtjW1Qu2Y2iO8')

# Initialize database
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

# API endpoint for top members
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
        return jsonify({
            'status': 'success',
            'data': members,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Bot handlers
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

async def run_bot():
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))
    
    print("🤖 Telegram bot is running...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

def run_flask():
    port = int(os.getenv('PORT', 8000))
    print(f"🌐 Web server running on port {port}")
    serve(app, host="0.0.0.0", port=port)

def main():
    # Run Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run the bot
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("🛑 Bot stopped")
    except Exception as e:
        print(f"🔥 Unexpected error: {str(e)}")

if __name__ == '__main__':
    main()
