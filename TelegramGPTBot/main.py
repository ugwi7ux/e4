"""
Main entry point for the Telegram bot with Flask server integration
Keeps the bot running continuously on Replit
"""
import os
import threading
import logging
from flask import Flask
from bot import TelegramBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app for keeping Replit alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "active"}

def run_flask():
    """Run Flask server in a separate thread"""
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")

def run_bot():
    """Run Telegram bot"""
    try:
        bot = TelegramBot()
        bot.start()
    except Exception as e:
        logger.error(f"Bot startup error: {e}")

if __name__ == "__main__":
    logger.info("Starting Telegram Bot with Flask server...")
    
    # Start Flask server in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask server started on port 5000")
    
    # Start bot in main thread
    run_bot()
