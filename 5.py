import telebot
import requests
import json
import os
import socket
import threading
import time
from datetime import datetime

TOKEN = '8150060907:AAEV7a5Q1cnO41bcMBVRCtRLHOqWeZGj3Ow'
bot = telebot.TeleBot(TOKEN)
data_file_path = 'djezzy_data.json'

def load_user_data():
    if os.path.exists(data_file_path):
        with open(data_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(data_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@bot.message_handler(commands=['start'])
def handle_start(msg):
    chat_id = msg.chat.id
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton('📱 إرسال رقم الهاتف 📱', callback_data='send_number')
    )
    
    try:
        bot.send_message(chat_id, '''👋 مرحبًا! بك في بوت الذي سيقدم لك مساعدة في تفعيل العروض في الشرائح التالية: 

جيزي-Djezzy(متوفر حاليا✅)
اوريدو-Ooredoo(سيتم توفيره عما قريب🕑) 
موبيليس-Mobillis(غير متوفر❌) 

و كما نعلمكم ان البوت غير تابع لاي شركة اتصالات و غير مسؤول عن اي رصيد او استخدام خاطئ للبوت💢

و نتمنى حسن استعمال البوت و نحن دائما تحت الخدمة💗

لاستعمال البوت اظغط الزر👇''', reply_markup=markup)
        
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 403:
            print(f"المستخدم {chat_id} حظر البوت - تجاهل الرسالة.")
        else:
            print(f"خطأ غير متوقع مع {chat_id}: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'send_number')
def handle_send_number(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, '📱 الرجاء إرسال رقم Djezzy الذي يبدأ بـ 07:')
    bot.register_next_step_handler_by_chat_id(chat_id, handle_phone_number)

@bot.message_handler(func=lambda m: m.text and m.text.startswith('07') and len(m.text) == 10)
def handle_phone_number(msg):
    chat_id = msg.chat.id
    text = msg.text.strip()
    msisdn = '213' + text[1:]
    user_data = load_user_data()
    if str(chat_id) in user_data and user_data[str(chat_id)]['msisdn'] == msisdn:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("✅ استمرار", callback_data=f'use_saved_{msisdn}'),
            telebot.types.InlineKeyboardButton("🔁 إعادة تسجيل", callback_data=f'reregister_{msisdn}')
        )
        bot.send_message(chat_id, '📌 رقمك مسجل مسبقًا. ماذا تريد؟', reply_markup=markup)
    else:
        start_otp_process(chat_id, msisdn)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith('use_saved_'))
def handle_use_saved(c):
    chat_id = c.message.chat.id
    msisdn = c.data.split('_')[2]
    user_data = load_user_data()
    if str(chat_id) in user_data and user_data[str(chat_id)]['msisdn'] == msisdn:
        bot.send_message(chat_id, '✅ تم استرجاع الحساب.')
        show_main_menu(chat_id)
    else:
        bot.send_message(chat_id, '⚠️ لم نعثر على بياناتك.')

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith('reRegister'.lower()) or c.data.startswith('reregister_'))
def handle_reregister(c):
    chat_id = c.message.chat.id
    msisdn = c.data.split('_')[1]
    start_otp_process(chat_id, msisdn)

def start_otp_process(chat_id, msisdn):
    if send_otp(msisdn):
        bot.send_message(chat_id, '🔢 تم إرسال OTP، أدخل الرمز:')
        bot.register_next_step_handler_by_chat_id(chat_id, lambda m: handle_otp(m, msisdn))
    else:
        bot.send_message(chat_id, '⚠️ خطأ بإرسال OTP، أعد المحاولة.')

def handle_otp(msg, msisdn):
    chat_id = msg.chat.id
    otp = msg.text.strip()
    tokens = verify_otp(msisdn, otp)
    if tokens:
        user_data = load_user_data()
        user_data[str(chat_id)] = {
            'telegram_id': chat_id,
            'msisdn': msisdn,
            'access_token': tokens['access_token'],
            'refresh_token': tokens.get('refresh_token'),
            'last_applied': datetime.now().isoformat()
        }
        save_user_data(user_data)
        bot.send_message(chat_id, '🎉 تم التحقق بنجاح!')
        show_main_menu(chat_id)
    else:
        bot.send_message(chat_id, '⚠️ OTP غير صحيح، حاول مجددًا.')

def show_main_menu(chat_id):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton('🎁 تفعيل 2جيغا مجانا', callback_data='send_gift'),
        telebot.types.InlineKeyboardButton('🛒 4جيغا-24ساعة-70Da', callback_data='send_4go'),
        telebot.types.InlineKeyboardButton('🛒 فيسبوك غير محدود-4ساعات-50da', callback_data='send_fb'),
        telebot.types.InlineKeyboardButton('📲 عرض معلومات الرقم و الرصيد و الانترنت', callback_data='check_balance'),
        telebot.types.InlineKeyboardButton('👥 دعوة صديق - 1جيغا', callback_data='invite_friend')
    )
    bot.send_message(chat_id, '⬇️ اختر من القائمة:', reply_markup=markup)

# عرض تأكيد تفعيل 2جيغا
@bot.callback_query_handler(func=lambda c: c.data == 'send_gift')
def handle_send_gift(c):
    chat_id = c.message.chat.id
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ تأكيد", callback_data='confirm_gift'),
        telebot.types.InlineKeyboardButton("❌ إلغاء", callback_data='cancel')
    )
    bot.send_message(chat_id, "هل أنت متأكد أنك تريد تفعيل عرض 2جيغا؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == 'confirm_gift')
def confirm_gift(c):
    chat_id = c.message.chat.id
    user_data = load_user_data()
    if str(chat_id) in user_data:
        user = user_data[str(chat_id)]
        send_gift(chat_id, user['msisdn'], user['access_token'])

# عرض تأكيد تفعيل 4جيغا
@bot.callback_query_handler(func=lambda c: c.data == 'send_4go')
def handle_send_4go(c):
    chat_id = c.message.chat.id
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ تأكيد", callback_data='confirm_4go'),
        telebot.types.InlineKeyboardButton("❌ إلغاء", callback_data='cancel')
    )
    bot.send_message(chat_id, "هل أنت متأكد أنك تريد تفعيل عرض 4جيغا 70DA؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == 'confirm_4go')
def confirm_4go(c):
    chat_id = c.message.chat.id
    user_data = load_user_data()
    if str(chat_id) in user_data:
        user = user_data[str(chat_id)]
        send_4go_offer(chat_id, user['msisdn'], user['access_token'])

# عرض تأكيد تفعيل فيسبوك غير محدود
@bot.callback_query_handler(func=lambda c: c.data == 'send_fb')
def handle_send_fb(c):
    chat_id = c.message.chat.id
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ تأكيد", callback_data='confirm_fb'),
        telebot.types.InlineKeyboardButton("❌ إلغاء", callback_data='cancel')
    )
    bot.send_message(chat_id, "هل تريد تفعيل فيسبوك غير محدود 4ساعات مقابل 50DA؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == 'confirm_fb')
def confirm_fb(c):
    chat_id = c.message.chat.id
    user_data = load_user_data()
    if str(chat_id) in user_data:
        user = user_data[str(chat_id)]
        send_fb_offer(chat_id, user['msisdn'], user['access_token'])

@bot.callback_query_handler(func=lambda c: c.data == 'invite_friend')
def handle_invite_friend(c):
    chat_id = c.message.chat.id
    bot.send_message(chat_id, '📞 أرسل رقم الصديق الذي تريد دعوته (ابدأ بـ 07):')
    bot.register_next_step_handler_by_chat_id(chat_id, process_invite_number)        

# عند اختيار إلغاء
@bot.callback_query_handler(func=lambda c: c.data == 'cancel')
def cancel_action(c):
    bot.send_message(c.message.chat.id, "❌ تم إلغاء العملية.")
        

@bot.callback_query_handler(func=lambda c: c.data == 'check_balance')
def handle_check_balance(c):
    chat_id = c.message.chat.id
    user_data = load_user_data()
    if str(chat_id) in user_data:
        user = user_data[str(chat_id)]
        bal_msg = check_balance(user['msisdn'], user['access_token'])
        bot.send_message(chat_id, bal_msg)
    else:
        bot.send_message(chat_id, '⚠️ سجل أولاً.')

def send_gift(chat_id, msisdn, access_token):
    url = f'https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{msisdn}/subscription-product'
    payload = {
        'data': {
            'id': 'GIFTWALKWIN',
            'type': 'products',
            'meta': {
                'services': {'steps':10000, 'code':'GIFTWALKWIN2GO','id':'WALKWIN'}
            }
        }
    }
    headers = {
        'User-Agent':'Djezzy/2.6.7',
        'Authorization':f'Bearer {access_token}',
        'Content-Type':'application/json; charset=utf-8'
    }
    try:
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code == 200:
            bot.send_message(chat_id, '✅ 2جيغا تم تفعيلها!')
        else:
            bot.send_message(chat_id, f'لم ينتهي الاسبوع حاول لاحقا🕑')
    except Exception as e:
        bot.send_message(chat_id, f'خطأ من السرفر💢')

def send_4go_offer(chat_id, msisdn, access_token):
    url = f'https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{msisdn}/subscription-product'
    payload = {'data':{'id':'BTLINTSPEEDDAY2Go','type':'products'}}
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Content-Type':'application/json',
        'Authorization':f'Bearer {access_token}'
    }
    try:
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code == 200:
            bot.send_message(chat_id, '✅ 4جيغا 70DA تفعيل ناجح!')
        elif r.status_code == 402:
            bot.send_message(chat_id, '❌ رصيد غير كافٍ.')
        elif r.status_code == 403:
            if '402' in r.text or 'your balance is not enough to subscribe to the product BTLINTSPEEDDAY2Go' in r.text:
                bot.send_message(chat_id, '❌ رصيد غير كافٍ.')
            else:
                bot.send_message(chat_id, f'⛔ خطأ من سرفر جيزي حاول تسجيل الرقم و اعد المحاولة')
        else:
            bot.send_message(chat_id, f'❌خطأ في السرفر')
    except Exception as e:
        bot.send_message(chat_id, f'حاول مجددا💢')
        
def send_fb_offer(chat_id, msisdn, access_token):
    url = f'https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{msisdn}/subscription-product'
    payload = {'data':{'id':'ImtiyazSurpriseData2hfbPRE','type':'products'}}
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Content-Type':'application/json',
        'Authorization':f'Bearer {access_token}'
    }
    try:
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code == 200:
            bot.send_message(chat_id, '✅ تم تفعيل فيسبوك غير محدود 4سا بنجاح!')
        elif r.status_code == 402:
            bot.send_message(chat_id, '❌ رصيد غير كافٍ.')
        elif r.status_code == 403:
            if '402' in r.text or 'your balance is not enough to subscribe to the product BTLINTSPEEDDAY2Go' in r.text:
                bot.send_message(chat_id, '❌ رصيد غير كافٍ.')
            else:
                bot.send_message(chat_id, f'⛔ خطأ من سرفر جيزي حاول تسجيل الرقم و اعد المحاولة')
        else:
            bot.send_message(chat_id, f'❌خطأ في السرفر')
    except Exception as e:
        bot.send_message(chat_id, f'حاول مجددا💢')


import json

def process_invite_number(msg):
    chat_id = msg.chat.id
    friend_number = msg.text.strip()
    if not (friend_number.startswith('07') and len(friend_number) == 10):
        bot.send_message(chat_id, '⚠️ الرقم غير صحيح. تأكد أنه يبدأ بـ 07 ويتكون من 10 أرقام.')
        return

    user_data = load_user_data()
    if str(chat_id) not in user_data:
        bot.send_message(chat_id, '⚠️ يجب تسجيل رقمك أولاً.')
        return

    inviter = user_data[str(chat_id)]
    msisdn = inviter['msisdn']
    access_token = inviter['access_token']
    b_number = '213' + friend_number[1:]

    url = f"https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{msisdn}/member-get-member?include="
    payload = {
        "data": {
            "id": "MGM-BONUS",
            "type": "products",
            "meta": {
                "services": {
                    "b-number": b_number,
                    "id": "MemberGetMember"
                }
            }
        }
    }

    headers = {
        'User-Agent': "Djezzy/2.6.10",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json; charset=utf-8",
        'Authorization': f"Bearer {access_token}"
    }

    try:
        max_retries = 5
        for attempt in range(max_retries):
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            response_text = response.text.strip()
            print(response_text)

            if response_text == '{}' or response_text == '':
                if attempt < max_retries - 1:
                    continue
                else:
                    bot.send_message(chat_id, '⚠️ فشل في تفعيل الدعوة بعد عدة محاولات حاول لاحقا🕑')
                    return

            try:
                res_json = json.loads(response_text)
            except json.JSONDecodeError:
                bot.send_message(chat_id, '⚠️ فشل في السرفر حاول لاحقا')
                return

            code = res_json.get("code")
            message = res_json.get("message", "")

            if code == 200 and message == "OK":
                bot.send_message(chat_id, f'✅ تمت دعوة الصديق {friend_number} بنجاح!')
                return
            elif code == 429 and message == "INVITATIONS_LIMIT_REACHED":
                bot.send_message(chat_id, '⚠️ لقد استخدمت الدعوة مسبقاً. يجب الانتظار أسبوعاً قبل دعوة صديق آخر.')
                return
            else:
                bot.send_message(chat_id, f'❌ فشل في إرسال الدعوة. ')
                return

    except Exception as e:
        bot.send_message(chat_id, '⚠️ حدث خطأ أثناء محاولة دعوة الصديق.')
        



def format_data_amount(mb):
    if mb >= 1024:
        return f"{mb / 1024:.2f} جيغا"
    else:
        return f"{mb} ميغا"

def format_datetime(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        months_ar = {
            "January": "جانفي", "February": "فيفري", "March": "مارس", "April": "أبريل",
            "May": "ماي", "June": "جوان", "July": "جويلية", "August": "أوت",
            "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر"
        }
        formatted = dt.strftime('%d %B %Y - %H:%M')
        for en, ar in months_ar.items():
            formatted = formatted.replace(en, ar)
        return formatted
    except:
        return 'غير متوفر'

def format_number(msisdn):
    if msisdn.startswith('213'):
        return '0' + msisdn[3:]
    return msisdn

def check_balance(msisdn, access_token):
    url = f'https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{msisdn}'
    params = {'include': 'connected-products,supplementary-informations'}
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Authorization': f'Bearer {access_token}'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            return f'⚠️ خطأ في جلب البيانات: {response.status_code}'

        data = response.json()
        sub_data = data['data']
        included = data.get('included', [])

        # اسم الشريحة
        sim_type = 'غير معروف'
        for item in included:
            if item['type'] == 'subscription-types':
                sim_type = item['attributes']['name']['text'].get('ar', 'غير معروف')
                break

        activation_time = format_datetime(sub_data['attributes'].get('activation-time', ''))
        balance = sub_data['attributes'].get('balance', 'غير متوفر')

        # معالجة العروض
        offers_info = ''
        count = 0
        for item in included:
            if item['type'] == 'connected-products':
                for product in item['attributes'].get('products', []):
                    offer_name = product['name']['text'].get('ar', 'غير متوفر')
                    offer_expiry = format_datetime(product.get('expiry-at', ''))
                    total_data = remaining_data = used_data = 0

                    for b in product.get('balances', []):
                        if b['bundle-type'] == 'data':
                            total_data = b.get('total-amount', 0)
                            remaining_data = b.get('remaining-amount', 0)
                            used_data = max(total_data - remaining_data, 0)
                            espace = '      '
                            break
                    
                    count += 1
                    offers_info += (                        
                        f'🛒 العرض {count}: {offer_name}\n'
                        f'🔴 المستخدم: {format_data_amount(remaining_data)}\n'
                        f'🟢 المتبقي: {format_data_amount(used_data)}\n'
                        f'📦 الإجمالي: {format_data_amount(total_data)}\n'
                        f'⏳ الانتهاء: {offer_expiry}\n'
                        f' {espace}\n'
                        
                    )

        user_number = format_number(msisdn)

        return (
            f'📱 معلومات الرقم:\n'            
            f'📞 رقم الهاتف: {user_number}\n'
            f'💳 نوع الشريحة: {sim_type}\n'
            f'📅 تاريخ التفعيل: {activation_time}\n'
            f'💰 الرصيد: {balance} DZD\n\n'
            f'🎈 العروض المفعلة ({count}):\n'
            f'{offers_info if offers_info else "لا توجد عروض مفعلة"}'
        )

    except Exception as e:
        return f'⚠️ حدث خطأ أثناء الاتصال'

def send_otp(msisdn):
    url = 'https://apim.djezzy.dz/oauth2/registration'
    payload = f'msisdn={msisdn}&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&scope=smsotp'
    headers = {
        'User-Agent':'Djezzy/2.6.7',
        'Content-Type':'application/x-www-form-urlencoded'
    }
    try:
        r = requests.post(url, data=payload, headers=headers)
        return r.status_code == 200
    except:
        return False

def verify_otp(msisdn, otp):
    url = 'https://apim.djezzy.dz/oauth2/token'
    payload = f'otp={otp}&mobileNumber={msisdn}&scope=openid&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&client_secret=MVpXHW_ImuMsxKIwrJpoVVMHjRsa&grant_type=mobile'
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        response = requests.post(url, data=payload, headers=headers)
        return response.json() if response.status_code == 200 else None
    except:
        return None
   



def fake_web_server():
    port = int(os.environ.get("PORT", 10000))  # أي رقم آمن وهمي
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', port))
    s.listen(1)
    print(f"Fake server running on port {port}")
    while True:
        conn, addr = s.accept()
        conn.close()

# تشغيل الخادم الوهمي في خيط منفصل
threading.Thread(target=fake_web_server, daemon=True).start()

def run_bot():
    while True:
        try:
            print('🚀 البوت شغال...')
            bot.infinity_polling()
        except Exception as e:
            print(f'⚠️ خطأ: {e}')
            time.sleep(5)

if __name__ == '__main__':
    run_bot()
    
