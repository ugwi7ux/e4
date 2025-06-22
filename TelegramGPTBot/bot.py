"""
Main Telegram bot implementation with GPT integration and local caching
"""
import os
import logging
import json
import time
import asyncio
from typing import Dict, List, Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from data_manager import DataManager
from config import Config

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.config = Config()
        self.data_manager = DataManager()
        
        # Initialize OpenAI client
        # Using GPT-4o-mini for natural human-like conversations
        try:
            self.openai_client = OpenAI(
                api_key=self.config.openai_api_key,
                timeout=30.0
            )
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_client = None
        
        # Store conversation contexts
        self.conversation_contexts: Dict[int, List[Dict]] = {}
        
        # Initialize Telegram application
        self.application = Application.builder().token(self.config.telegram_token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup bot command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("clear", self.clear_context))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        welcome_message = """
مرحباً بك! 👋

أنا مساعدك الذكي الجديد! أحب الدردشة والتعرف على أشخاص جدد.

ما يميزني:
• أتحدث معك بطريقة طبيعية مثل الأصدقاء
• أتذكر كل محادثاتنا وأبني عليها
• أجيب بالعربية أو الإنجليزية حسب ما تفضل
• أحب الأسئلة المعقدة والنقاشات العميقة

الأوامر البسيطة:
/start - للتعارف من جديد
/help - لمعرفة المزيد عني
/clear - لبدء موضوع جديد

احكيلي عن نفسك أو اسألني أي شيء! 😊
        """
        
        try:
            await update.message.reply_text(welcome_message)
            logger.info(f"User {user_id} started the bot")
        except Exception as e:
            logger.error(f"Error sending start message to user {user_id}: {e}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
🤖 **مساعدة البوت الذكي**

**الأوامر:**
/start - بدء محادثة جديدة
/help - عرض هذه المساعدة
/clear - مسح سياق المحادثة الحالية

**الميزات:**
✅ إجابات ذكية باستخدام GPT
✅ حفظ المحادثات السابقة
✅ دعم اللغة العربية والإنجليزية
✅ ذاكرة للسياق أثناء المحادثة

**كيفية الاستخدام:**
فقط اكتب رسالتك وسأجيب عليك فوراً!
        """
        
        try:
            await update.message.reply_text(help_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error sending help message: {e}")
    
    async def clear_context(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear conversation context for user"""
        user_id = update.effective_user.id
        
        if user_id in self.conversation_contexts:
            del self.conversation_contexts[user_id]
        
        try:
            await update.message.reply_text("تم مسح سياق المحادثة! يمكنك بدء محادثة جديدة الآن. ✨")
            logger.info(f"Cleared context for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing context for user {user_id}: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        user_id = update.effective_user.id
        user_message = update.message.text.strip()
        
        if not user_message:
            return
        
        logger.info(f"Received message from user {user_id}: {user_message[:50]}...")
        
        try:
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Get response
            response = await self.get_response(user_id, user_message)
            
            if response:
                # Send response in chunks if too long
                await self.send_long_message(update, response)
                logger.info(f"Sent response to user {user_id}")
            else:
                # Simple fallback without repeating patterns
                await update.message.reply_text("أعتذر، لم أتمكن من الاستجابة بشكل مناسب. يرجى المحاولة مرة أخرى.")
                
        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {e}")
            try:
                await update.message.reply_text("حدث خطأ مؤقت، يرجى المحاولة مرة أخرى.")
            except Exception as fallback_error:
                logger.error(f"Fallback error: {fallback_error}")
                pass
    
    async def get_response(self, user_id: int, message: str) -> Optional[str]:
        """Get response from GPT - always use live GPT for natural conversations"""
        try:
            # Skip cache for natural conversations - always use GPT
            if not self.openai_client:
                logger.error("OpenAI client not available")
                return "عذراً، هناك مشكلة في الاتصال بالخدمة. يرجى المحاولة مرة أخرى."
            
            response = await self.get_gpt_response(user_id, message)
            
            # Save successful conversations to cache for future reference
            if response and len(response) > 20:  # Only save substantial responses
                self.data_manager.save_qa_pair(message, response)
                logger.info("Saved conversation to cache")
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting response: {e}")
            return "أعتذر، أواجه صعوبة في الاستجابة الآن. هل يمكنك إعادة المحاولة؟"
    
    async def get_gpt_response(self, user_id: int, message: str) -> Optional[str]:
        """Get response from GPT with conversation context"""
        try:
            # Prepare conversation context
            if user_id not in self.conversation_contexts:
                self.conversation_contexts[user_id] = []
            
            # Add current message to context
            self.conversation_contexts[user_id].append({
                "role": "user",
                "content": message
            })
            
            # Keep more conversation history for better context (last 15 exchanges)
            if len(self.conversation_contexts[user_id]) > 30:
                self.conversation_contexts[user_id] = self.conversation_contexts[user_id][-30:]
            
            # Prepare messages for GPT
            messages = [
                {
                    "role": "system",
                    "content": """أنت مساعد ذكي وودود تحاكي المحادثة البشرية الطبيعية. تتفاعل مع المستخدمين بطريقة حقيقية ومتكيفة.

خصائصك:
- تتحدث بطريقة طبيعية وتفاعلية مثل البشر
- تتذكر المحادثات السابقة وتبني عليها
- تجيب باللغة العربية أو الإنجليزية حسب لغة المستخدم
- تظهر اهتماماً حقيقياً بما يقوله المستخدم
- تطرح أسئلة متابعة عند الحاجة
- تقدم إجابات مفصلة ومفيدة
- تستخدم الأمثلة والتشبيهات لتوضيح الأفكار
- تتكيف مع شخصية ومزاج المستخدم
- لا تستخدم أبداً كلمات مثل "فشل" أو رسائل خطأ تقنية

تذكر: أنت لست مجرد بوت، بل محاور حقيقي يخوض محادثة ممتعة ومفيدة."""
                }
            ] + self.conversation_contexts[user_id]
            
            # Make API call with retry logic
            response = await self.call_openai_with_retry(messages)
            
            if response:
                # Add assistant response to context
                self.conversation_contexts[user_id].append({
                    "role": "assistant",
                    "content": response
                })
                
                return response
            else:
                # Return None to trigger fallback handling
                return None
            
        except Exception as e:
            logger.error(f"Error getting GPT response: {e}")
            return None
    
    async def call_openai_with_retry(self, messages: List[Dict], max_retries: int = 3) -> Optional[str]:
        """Call OpenAI API with retry logic"""
        if not self.openai_client:
            return None
            
        for attempt in range(max_retries):
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",  # Using GPT-4o-mini as requested
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.8,
                    store=True,
                    timeout=30
                )
                
                if response and response.choices:
                    return response.choices[0].message.content.strip()
                else:
                    logger.warning(f"Empty response from OpenAI (attempt {attempt + 1})")
                    
            except Exception as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await self.async_sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None
        
        return None
    
    async def async_sleep(self, seconds: float):
        """Async sleep wrapper"""
        await asyncio.sleep(seconds)
    
    async def send_long_message(self, update: Update, text: str, max_length: int = 4000):
        """Send long messages in chunks"""
        try:
            if len(text) <= max_length:
                await update.message.reply_text(text)
            else:
                # Split message into chunks
                chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await update.message.reply_text(chunk)
                    else:
                        await update.message.reply_text(f"... {chunk}")
                        await self.async_sleep(1)  # Small delay between chunks
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    def start(self):
        """Start the bot"""
        try:
            logger.info("Starting Telegram bot...")
            self.application.run_polling(
                drop_pending_updates=True,
                close_loop=False
            )
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
