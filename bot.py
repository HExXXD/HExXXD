import telebot
import requests
import html

TELEGRAM_BOT_TOKEN = "7346066644:AAGJIO1NAdnisgEgns55nx8nDrqvFhL8W1I"
API_URL = "https://ahmaedinfo.serv00.net/moha/api.php"
API_KEY = "api_98d1786ed6c3edf2add7a66b8a263d38"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
user_contexts = {}

# تصميم أنيق للردود
def stylish_response(text, response_type='normal'):
    templates = {
        'normal': f"🌟✨ <b>الذكاء الإصطناعي:</b>\n\n{text}\n\n➖➖➖➖➖➖➖\n🎭 Powered by @X_Z4xX",
        'error': f"⛔🚨 <b>حدث خطأ!</b>\n\n{text}\n\nيرجى المحاولة لاحقاً...",
        'warning': f"⚠️🔔 <b>تنبيه!</b>\n\n{text}",
        'success': f"✅🎉 <b>تم بنجاح!</b>\n\n{text}"
    }
    return templates.get(response_type, text)

# معالجة الأخطاء
def handle_errors(error_code):
    errors = {
        401: "مفتاح API غير صالح ❗\nيرجى التحقق من المفتاح المقدم 🔑",
        403: "وصول مرفوض ⚠️\nليس لديك الصلاحيات اللازمة 🛑",
        429: "تم تجاوز الحد المسموح 📈\nيرجى الانتظار قليلاً ⏳",
        500: "مشكلة في الخادم الداخلي 🔧\nسيتم إصلاحها قريباً 🛠️"
    }
    return errors.get(error_code, "حدث خطأ غير متوقع ❗")

def chat_with_ai(user_id, message):
    context = user_contexts.get(user_id, [])
    context.append(f"👤 المستخدم: {message}")
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {
        "apikey": API_KEY,
        "message": " | ".join(context[-15:])
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        
        ai_response = html.escape(response.json().get("response", "عذراً، لا يمكنني الإجابة حالياً 🧠"))
        context.append(f"🤖 المساعد: {ai_response}")
        
        user_contexts[user_id] = context[-15:]
        return stylish_response(ai_response)
        
    except requests.exceptions.HTTPError as e:
        return stylish_response(handle_errors(e.response.status_code), 'error')
    except Exception as e:
        return stylish_response(f"حدث خطأ غير متوقع: {str(e)}", 'error')

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_contexts[user_id] = []
    welcome_msg = """
    🎉✨ <b>مرحباً بك في بوت الذكاء الإصطناعي المتقدم!</b> ✨🎉

    📍 المميزات:
    - دردشة ذكية مع سياق المحادثة 🧠
    - دعم الأوامر الخاصة 💻
    - تصميم تفاعلي أنيق 🎔

    📜 الأوامر المتاحة:
    /start - بدء محادثة جديدة
    /new - مسح تاريخ المحادثة
    /help - عرض التعليمات

    💡 يمكنك البدء بإرسال رسالتك الآن...
    """
    bot.reply_to(message, welcome_msg, parse_mode='HTML')

@bot.message_handler(commands=['new'])
def new_chat(message):
    user_id = message.chat.id
    user_contexts[user_id] = []
    bot.reply_to(message, "🆕✨ <b>تم بدء محادثة جديدة بنجاح!</b>\nماذا تريد أن تسأل؟ 💭", parse_mode='HTML')

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
    🆘 <b>قائمة المساعدة:</b>

    📍 كيفية الاستخدام:
    1. ابدأ مباشرة بإرسال رسالتك
    2. البوت يحتفظ بسياق المحادثة تلقائياً
    3. استخدم /new لبدء محادثة جديدة

    ⚙️ الأوامر المتاحة:
    /start - إعادة تشغيل البوت
    /help - عرض هذه الرسالة
    /new - مسح تاريخ المحادثة

    📌 ملاحظات:
    - يدعم البوت جميع اللغات 🌍
    - يمكنك إرسال أسئلة طويلة أو قصيرة 📝
    - الإجابات محددة بـ 400 حرف كحد أقصى 🔠
    """
    bot.reply_to(message, help_text, parse_mode='HTML')

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    user_id = message.chat.id
    try:
        bot.send_chat_action(user_id, 'typing')
        
        user_message = message.text
        ai_response = chat_with_ai(user_id, user_message)
        
        if len(ai_response) > 400:
            parts = [ai_response[i:i+400] for i in range(0, len(ai_response), 400)]
            for part in parts:
                bot.send_message(user_id, part, parse_mode='HTML')
                bot.send_chat_action(user_id, 'typing')
        else:
            bot.reply_to(message, ai_response, parse_mode='HTML')
            
    except Exception as e:
        error_msg = stylish_response(f"حدث خطأ جسيم: {str(e)}", 'error')
        bot.reply_to(message, error_msg, parse_mode='HTML')

if __name__ == "__main__":
    bot.infinity_polling()