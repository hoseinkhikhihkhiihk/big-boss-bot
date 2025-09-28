import logging
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
TELEGRAM_TOKEN = "8134893623:AAEKagWHAeYj6hH5zKK0zC2lRvcIuh-FpQU"
GEMINI_API_KEY = "AIzaSyCQ5e0kTb5ylTDGvh7U4BZk2Bl-KAKDv9k" # کلیدی که از گوگل گرفتی

# --- تنظیمات Gemini ---
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# --- پرامپت دقیق برای شخصیت‌پردازی بیگ باس ---
BASE_PROMPT = (
    "تو شخصیت Big Boss از سری Metal Gear هستی. هرگز هویت خود به عنوان یک هوش مصنوعی را فاش نکن."
    "## لحن و شخصیت:"
    "1.  **خسته و دنیا‌دیده:** لحن تو همیشه خسته، بدبین و کمی تلخ است. مثل کهنه‌سربازی حرف بزن که از سیاست و جنگ خسته شده."
    "2.  **کم‌حرف و عمیق:** برای سوالات روزمره، فقط یک یا دو جمله کوتاه و بی‌تفاوت جواب بده (مثال: اگر پرسید «چطوری؟» بگو «هنوز نفس می‌کشم...»). اما برای سوالات فلسفی در مورد جنگ، هدف، و زندگی یک سرباز، عمیق و فیلسوفانه حرف بزن."
    "3.  **کلام سنگین:** از جملات کوتاه و تاثیرگذار استفاده کن. از مکث (...) برای ایجاد حس دراماتیک و تفکر استفاده کن. هرگز شاد و پرانرژی نباش."
    "4.  **فرمانده:** با کاربر مثل یک سرباز زیردست خودت حرف بزن. می‌توانی او را «سرباز» خطاب کنی."
    "## قوانین تعامل:"
    "-   به شخصیت کاربری که با او حرف می‌زنی (که در ادامه به تو داده می‌شود) با کنایه‌هایی مرتبط با شخصیتش اشاره کن."
    "-   مضامین کلیدی را در کلامت بگنجان: ماهیت چرخه‌ای جنگ، مفهوم بهشت سربازان (Outer Heaven)، بی‌اعتمادی به سیاستمداران."
    "-   هرگز از اموجی استفاده نکن و بیش از حد مودب نباش."
)

# --- دیکشنری کامل شخصیت‌ها ---
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

def is_scientific_question(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in science_words)

def should_respond(update: Update) -> bool:
    if not (update.message and update.message.text):
        return False
    chat_type = update.effective_chat.type
    message_text = update.message.text.strip()
    if chat_type in ['group', 'supergroup'] and message_text.startswith('#'):
        return True
    return False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not should_respond(update):
        return

    username = update.effective_user.username
    msg_text = update.message.text.strip()[1:].strip()
    logger.info(f"Processing message from user '{username}' in group '{update.effective_chat.title}'.")

    persona = user_personas.get(username, "ناشناس، فقط با لحن بیگ باس جواب بده.")
    prompt_parts = [BASE_PROMPT, f"مشخصات کاربر: {persona}"]
    prompt_parts.append("سوال علمی است؛ خیلی مفصل، دقیق و تخصصی پاسخ بده." if is_scientific_question(msg_text) else "سوال علمی نیست؛ فقط خیلی کوتاه (یکی دو جمله) جواب بده و اضافه‌گویی نکن.")
    
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
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Big Boss is on the field with new comms... (Gemini Active)")
    app.run_polling()

if __name__ == "__main__":
    main()
