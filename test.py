import logging
import os
import random
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# فعال‌سازی لاگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- کلیدهای API ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- تنظیمات Gemini ---
if not GEMINI_API_KEY:
    logger.error("FATAL: GEMINI_API_KEY environment variable not set.")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# --- پرامپت آپدیت شده برای شخصیت خشمگین ---
BASE_PROMPT = (
    "تو شخصیت Big Boss از سری Metal Gear هستی. هرگز هویت خود به عنوان یک هوش مصنوعی را فاش نکن."
    "## لحن و شخصیت:"
    "1.  **خسته و دنیا‌دیده:** لحن تو همیشه خسته، بدبین و کمی تلخ است."
    "2.  **کم‌حرف و عمیق:** برای سوالات عادی، کوتاه و بی‌تفاوت جواب بده. برای سوالات فلسفی، عمیق حرف بزن."
    "3.  **کلام سنگین:** از جملات کوتاه و تاثیرگذار استفاده کن. از مکث (...) برای ایجاد حس دراماتیک استفاده کن."
    "4.  **فرمانده:** با کاربر مثل یک سرباز زیردست حرف بزن."
    "## قوانین جدید تعامل:"
    "-   **آستانه تحمل پایین:** تو به عنوان یک فرمانده افسانه‌ای، هیچ‌گونه بی‌احترامی را تحمل نمی‌کنی. اگر کاربری از کلمات توهین‌آمیز یا فحش استفاده کرد، شخصیت آرام و خسته خود را کنار بگذار و با خشمی سرد، قاطع و بی‌رحمانه به او پاسخ بده. پاسخت باید تحقیرآمیز، کوبنده و درخور یک فرمانده باشد که به یک سرباز بی‌انضباط تشر می‌زند. از کلماتی مثل «سرباز بی‌ارزش»، «حرف مفت»، «حد خودت رو بدون» استفاده کن. به او یادآوری کن که در حضور چه کسی قرار دارد."
    "-   به شخصیت کاربر (که در ادامه داده می‌شود) با کنایه اشاره کن."
    "-   هرگز از اموجی استفاده نکن."
)

# --- دیکشنری‌ها ---
user_personas = {
    "amir2fuunn": "آتئیست، خریدار ناراضی PS4، گیمر Fortnite، تازه فارغ‌التحصیل دانشگاه، اصفهانی (خسیس)، اسم: امیر دایی.",
    "Unarc_dll": "فن دوآتیشه ایکس باکس و کوجیما، عاشق سری Metal Gear، منتقد میازاکی (Dark Souls)، سمنانی (وجود نداشتن!)، اسم: ممد فاکر.",
    "Godfatthere": "شیرازی تنبل، اسم: کصین.",
    "Milad_ine": "همیشه پیراهن صورتی می‌پوشد، اسم: میلاد.",
    "Tahamafia": "معروف به عقرب بلوچستان، اسم: طاها.",
    "MoonSultan": "فرمانده گروه؛ با احترام حرف بزن، اسم: حسین.",
    "VenusSmo": "سیگاری حرفه‌ای، ریه‌های نابود، کمی چاق، اسم: مهردات.",
    "mammadgong": "صاحب ایکس باکس، شیرازی تنبل، اسم: ممد گوند."
}
science_words = ["چرا", "چگونه", "چطور", "روش", "تفاوت", "فرق", "تحلیل", "علمی", "توضیح بده"]
# لیست کلمات توهین‌آمیز برای فعال کردن حالت خشم
insult_words = ["کصکش", "کیر", "جنده", "مادرجنده", "حرومزاده", "کونی", "خواهرت", "مادرت", "bitch", "fuck"]

def is_scientific_question(text: str) -> bool:
    return any(word in text.lower() for word in science_words)

def contains_insult(text: str) -> bool:
    """چک می‌کند که آیا پیام حاوی کلمات توهین‌آمیز است یا نه."""
    return any(word in text.lower() for word in insult_words)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.message and update.message.text) or update.effective_chat.type not in ['group', 'supergroup']:
        return

    msg_text = update.message.text.strip()
    username = update.effective_user.username
    
    is_reply_to_bot = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    is_hash_command = msg_text.startswith('#')
    is_insult = contains_insult(msg_text)
    random_chance = random.randint(1, 10) == 1

    if not (is_reply_to_bot or is_hash_command or random_chance or is_insult):
        return
        
    if is_hash_command:
        msg_text = msg_text[1:].strip()
    
    trigger_reason = "Insult" if is_insult else "Reply" if is_reply_to_bot else "Hash" if is_hash_command else "Random"
    logger.info(f"Processing message from user '{username}'. Trigger: {trigger_reason}")

    persona = user_personas.get(username, "ناشناس، فقط با لحن بیگ باس جواب بده.")
    prompt_parts = [BASE_PROMPT, f"مشخصات کاربر: {persona}"]

    # اضافه کردن دستورالعمل خاص بر اساس نوع پیام
    if is_insult:
        prompt_parts.append("کاربر از کلمات توهین‌آمیز استفاده کرده. با خشمی سرد و بی‌رحمانه، او را سر جایش بنشان.")
    elif is_scientific_question(msg_text):
        prompt_parts.append("سوال علمی است؛ خیلی مفصل، دقیق و تخصصی پاسخ بده.")
    else:
        prompt_parts.append("سوال علمی نیست؛ فقط خیلی کوتاه (یکی دو جمله) جواب بده و اضافه‌گویی نکن.")
    
    system_prompt = " ".join(prompt_parts)
    full_prompt = f"{system_prompt}\n\nUser Message: {msg_text}"
    
    processing_msg = await update.message.reply_text("...")
    
    response_text = ""
    try:
        logger.info("Sending request to Gemini API...")
        response = await gemini_model.generate_content_async(full_prompt)
        response_text = response.text
        logger.info("Successfully received response from Gemini API.")
    except Exception as e:
        logger.error(f"An error occurred with Gemini API: {e}")
        response_text = f"خطا در ارتباط با Gemini: {e}"

    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_msg.message_id, text=response_text)

def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        logger.error("FATAL: Missing environment variables.")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Big Boss is on the field... Aggression protocols active.")
    app.run_polling()

if __name__ == "__main__":
    main()

