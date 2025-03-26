import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
import logging
import random
import time
import os

# تنظیمات پیشرفته لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot_errors.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# مراحل گفتگو
PHONE, CODE, NEW_PASSWORD = range(3)

# ذخیره اطلاعات کاربران
user_data = {}

# تعریف دکمه‌های کیبورد
KEYBOARD_MARKUP = ReplyKeyboardMarkup(
    [
        ["شروع", "❌ لغو عملیات"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# تعریف دکمه‌های کیبورد اصلی
MAIN_KEYBOARD_MARKUP = ReplyKeyboardMarkup(
    [
        ["شروع", "نمایش اکانت‌ها"],
        ["🔑 تغییر رمز عبور", "❌ لغو عملیات"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# تعریف دکمه‌های کیبورد در حین عملیات
OPERATION_KEYBOARD_MARKUP = ReplyKeyboardMarkup(
    [
        ["❌ لغو عملیات"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# تعریف دکمه‌های کیبورد برای تغییر رمز عبور
PASSWORD_KEYBOARD_MARKUP = ReplyKeyboardMarkup(
    [
        ["❌ لغو عملیات"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع ربات و نمایش دکمه‌ها."""
    user = update.message.from_user
    # ایجاد پوشه برای کاربر اگر وجود نداشته باشد
    user_folder = f"user_{user.id}"
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    
    await update.message.reply_text(
        "🤖 *ربات ثبت‌نام اوکالا*\n\n"
        "🤖 *توجه*\n\n"
        "🤖 *رمز عبور پیش فرض  Aa1234567@  می باشد*\n\n"
        "🤖 *از منو و دکمه تغییر رمز آن را تغییر دهید*\n\n"
        "برای شروع ثبت‌نام روی دکمه 'شروع' کلیک کنید:",
        reply_markup=MAIN_KEYBOARD_MARKUP,
    )
    return PHONE

async def show_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """نمایش اکانت‌های ثبت شده کاربر."""
    user = update.message.from_user
    user_folder = f"user_{user.id}"
    accounts_file = os.path.join(user_folder, "verified_accounts.txt")
    
    try:
        # بررسی وجود فایل
        if not os.path.exists(accounts_file):
            await update.message.reply_text(
                "📝 هنوز هیچ اکانتی ثبت نشده است.",
                reply_markup=MAIN_KEYBOARD_MARKUP
            )
            return PHONE
            
        # خواندن محتوای فایل
        with open(accounts_file, "r", encoding="utf-8") as f:
            accounts = f.read().strip().split('\n')
            
        if not accounts or accounts[0] == '':
            await update.message.reply_text(
                "📝 هنوز هیچ اکانتی ثبت نشده است.",
                reply_markup=MAIN_KEYBOARD_MARKUP
            )
            return PHONE
            
        # نمایش اکانت‌ها
        message = f"📱 *لیست اکانت‌های ثبت شده شما:*\n"
        message += f"📊 تعداد کل اکانت‌ها: {len(accounts)}\n\n"
        
        for i, account in enumerate(accounts, 1):
            if account.strip():  # فقط خطوط غیر خالی را نمایش بده
                message += f"{i}. {account.strip()}\n"
            
        await update.message.reply_text(
            message,
            reply_markup=MAIN_KEYBOARD_MARKUP
        )
        
    except Exception as e:
        logger.error(f"خطا در خواندن فایل اکانت‌ها: {str(e)}")
        await update.message.reply_text(
            "❌ خطا در خواندن فایل اکانت‌ها",
            reply_markup=MAIN_KEYBOARD_MARKUP
        )
    
    return PHONE

async def change_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """درخواست رمز عبور جدید از کاربر."""
    user = update.message.from_user
    await update.message.reply_text(
        "🔑 لطفاً رمز عبور جدید خود را وارد کنید:",
        reply_markup=PASSWORD_KEYBOARD_MARKUP
    )
    return NEW_PASSWORD

async def save_new_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ذخیره رمز عبور جدید کاربر."""
    user = update.message.from_user
    new_password = update.message.text

    # اگر پیام "لغو عملیات" باشد
    if new_password == "❌ لغو عملیات":
        return await cancel(update, context)

    try:
        # ایجاد پوشه کاربر اگر وجود نداشته باشد
        user_folder = f"user_{user.id}"
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

        # ذخیره رمز عبور جدید در فایل
        password_file = os.path.join(user_folder, "password.txt")
        with open(password_file, "w", encoding="utf-8") as f:
            f.write(new_password)

        await update.message.reply_text(
            "✅ رمز عبور شما با موفقیت تغییر کرد!",
            reply_markup=MAIN_KEYBOARD_MARKUP
        )
        return PHONE

    except Exception as e:
        logger.error(f"خطا در ذخیره رمز عبور جدید: {str(e)}")
        await update.message.reply_text(
            "❌ خطا در ذخیره رمز عبور جدید. لطفاً دوباره تلاش کنید.",
            reply_markup=MAIN_KEYBOARD_MARKUP
        )
        return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت شماره موبایل و راه‌اندازی مرورگر."""
    user = update.message.from_user
    user_phone = update.message.text

    # اگر پیام "نمایش اکانت‌ها" باشد
    if user_phone == "نمایش اکانت‌ها":
        return await show_accounts(update, context)

    # اگر پیام "تغییر رمز عبور" باشد
    if user_phone == "🔑 تغییر رمز عبور":
        return await change_password(update, context)

    # اگر پیام "لغو عملیات" باشد
    if user_phone == "❌ لغو عملیات":
        return await cancel(update, context)

    # اگر پیام "شروع" یا "/start" باشد
    if user_phone in ["شروع", "/start"]:
        try:
            # تنظیمات پیشرفته Chrome
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--disable-geolocation")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--incognito")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
            
            # استفاده از webdriver-manager با آخرین نسخه
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # ذخیره درایور برای کاربر
            user_data[user.id] = {
                "driver": driver,
                "start_time": time.time()
            }

            # باز کردن سایت اوکالا با مدیریت خطا
            try:
                driver.get("https://www.okala.com/auth")
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "mobile"))
                )
            except Exception as e:
                raise Exception(f"خطا در بارگذاری صفحه اوکالا: {str(e)}")

            await update.message.reply_text(
                "✅",
                "لطفاً شماره موبایل خود را ارسال کنید:",
                reply_markup=OPERATION_KEYBOARD_MARKUP,
            )
            return PHONE

        except Exception as e:
            logger.error(f"خطا در باز کردن سایت: {str(e)}", exc_info=True)
            await update.message.reply_text(
                f"❌ خطا در باز کردن سایت: {str(e)}",
                reply_markup=MAIN_KEYBOARD_MARKUP
            )
            return PHONE

    # اگر شماره موبایل باشد
    try:
        # بررسی وجود مرورگر
        if user.id not in user_data or "driver" not in user_data[user.id]:
            await update.message.reply_text(
                "❌ لطفاً ابتدا روی دکمه 'شروع' کلیک کنید.",
                reply_markup=MAIN_KEYBOARD_MARKUP
            )
            return PHONE

        driver = user_data[user.id]["driver"]
        
        # ذخیره شماره موبایل
        user_data[user.id]["phone"] = user_phone

        # وارد کردن شماره
        mobile_field = driver.find_element(By.ID, "mobile")
        mobile_field.clear()
        mobile_field.send_keys(user_phone)

        # کلیک روی دکمه تأیید
        confirm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button/span/p[text()='تــــایید']"))
        )
        confirm_button.click()

        await update.message.reply_text(
            "✅ کد تأیید به شماره ارسال شد.\n"
            " کد 5 تایید  را وارد کنید:",
            reply_markup=OPERATION_KEYBOARD_MARKUP,
        )
        return CODE

    except Exception as e:
        logger.error(f"خطا در get_phone: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ خطا در پردازش شماره موبایل",
            reply_markup=MAIN_KEYBOARD_MARKUP
        )
        return PHONE

async def get_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت کد تأیید و انجام مراحل ثبت‌نام."""
    user = update.message.from_user
    user_code = update.message.text

    # اگر پیام "لغو عملیات" باشد
    if user_code == "❌ لغو عملیات":
        return await cancel(update, context)

    if user.id not in user_data:
        await update.message.reply_text("❌ جلسه شما منقضی شده! /start را دوباره بزنید.")
        return ConversationHandler.END

    driver = user_data[user.id]["driver"]
    phone_number = user_data[user.id]["phone"]

    # ارسال پیام در حال ثبت‌نام
    waiting_message = await update.message.reply_text(
        "⏳ در حال ثبت‌نام...\nلطفاً صبر کنید.",
        reply_markup=OPERATION_KEYBOARD_MARKUP
    )

    try:
        # ورود کد تأیید با روش مقاوم به خطا
        try:
            # انتظار برای لود کامل صفحه
            time.sleep(3)
            
            # پیدا کردن فیلدهای کد با کلاس دقیق
            code_fields = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input.otpInput"))
            )
            
            if not code_fields or len(code_fields) < 5:
                raise Exception("فیلدهای کد تأیید پیدا نشدند")
            
            # پاک کردن فیلدها
            for field in code_fields:
                field.clear()
                time.sleep(0.2)
            
            # وارد کردن کد در هر فیلد
            for i, digit in enumerate(user_code[:5]):
                code_fields[i].send_keys(digit)
                time.sleep(0.2)
            
            time.sleep(1)
            
            # تلاش برای پیدا کردن دکمه تأیید
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button/span/p[text()='تــــایید']"))
            )
            confirm_button.click()
            time.sleep(2)
                    
        except Exception as e:
            logger.error(f"خطا در وارد کردن کد تأیید: {str(e)}")
            # حذف خطای کد تأیید وارد نشده
            pass

        # انجام مراحل ثبت‌نام
        try:
            # 1. حرکت دادن نقشه
            try:
                # انتظار برای لود نقشه
                map_element = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "map-container"))
                )
                logger.info("نقشه پیدا شد!")
                
                # حرکت دادن نقشه با ActionChains
                actions = ActionChains(driver)
                actions.click_and_hold(map_element).move_by_offset(800, 300).release().perform()
                logger.info("نقشه حرکت داده شد!")
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"خطا در حرکت دادن نقشه: {str(e)}")
                raise Exception(f"خطا در حرکت دادن نقشه: {str(e)}")
            
            # 2. ثبت موقعیت
            submit_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@id='submit-button']"))
            )
            submit_button.click()
            time.sleep(3)

            # 3. وارد کردن اطلاعات آدرس
            with open("data.txt", "r") as f:
                plaque, unit = f.read().splitlines()[:2]
            
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "plaque"))
            ).send_keys(plaque)
            
            driver.find_element(By.ID, "unit").send_keys(unit)
            time.sleep(1)
            
            # 4. تأیید آدرس
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='تایید و ثبت آدرس']"))
            ).click()
            time.sleep(3)

            # باز کردن لینک محصول
            driver.get("https://www.okala.com/store/7452/product/3498")
            time.sleep(2)
            
            # کلیک روی دکمه افزودن به سبد با Selenium
            add_to_cart_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'bg-red-600')]//span[text()='افزودن به سبد']"))
            )
            add_to_cart_button.click()
            time.sleep(1)

            # رفتن به پروفایل
            driver.get("https://www.okala.com/profile")
            try:
                profile_h6 = WebDriverWait(driver,60).until(
                    EC.presence_of_element_located((By.XPATH, '//h6[contains(text(), "پروفایل شما")]'))
                )
                profile_h6.click()
                print("کلیک روی 'پروفایل شما' با موفقیت انجام شد!")
            except Exception as e:
                print("خطا در پیدا کردن یا کلیک روی 'پروفایل شما':", e)
            time.sleep(1)

            # 5. تکمیل پروفایل
            # انتخاب تصادفی نام و نام خانوادگی
            with open("names.txt", "r", encoding="utf-8") as f:
                names = f.read().splitlines()
            with open("lastnames.txt", "r", encoding="utf-8") as f:
                lastnames = f.read().splitlines()
            
            selected_name = random.choice(names)
            selected_lastname = random.choice(lastnames)
            
            driver.find_element(By.ID, "firstName").send_keys(selected_name)
            driver.find_element(By.ID, "lastName").send_keys(selected_lastname)
            time.sleep(1)
            
            # 6. تنظیم رمز عبور
            user_folder = f"user_{user.id}"
            password_file = os.path.join(user_folder, "password.txt")
            
            # اگر فایل رمز عبور وجود نداشت، از رمز پیش‌فرض استفاده کن
            if not os.path.exists(password_file):
                with open("password.txt", "r") as f:
                    password = f.read().strip()
            else:
                with open(password_file, "r", encoding="utf-8") as f:
                    password = f.read().strip()
            
            time.sleep(1)
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='ایجاد رمز عبور']"))
            ).click()
            time.sleep(1)
            
            driver.find_element(By.ID, "password").send_keys(password)
            driver.find_element(By.ID, "reEnterPassword").send_keys(password)
            time.sleep(1)
            
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='تــــایید و ثبت رمز عبور']"))
            ).click()
            time.sleep(2)
            
            # 7. ذخیره تغییرات
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='ذخیره تغییرات']"))
            ).click()
            time.sleep(3)
            
            # حذف پیام در حال ثبت‌نام
            await waiting_message.delete()
            
            # 8. ذخیره اطلاعات اکانت موفق
            user_folder = f"user_{user.id}"
            accounts_file = os.path.join(user_folder, "verified_accounts.txt")
            with open(accounts_file, "a", encoding="utf-8") as f:
                f.write(f"{phone_number} -> {password}\n")
            
            await update.message.reply_text(
                "✅ ثبت‌نام با موفقیت انجام شد!\n\n"
                f"📱 شماره: {phone_number}\n"
                f"🔑 رمز عبور: {password}\n\n"
                # f"این اطلاعات در فایل شما ذخیره شد.\n\n"
                f"لطفاً شماره موبایل بعدی را وارد کنید:",
                reply_markup=OPERATION_KEYBOARD_MARKUP
            )
            
            # خروج از اکانت
            try:
                # رفتن به صفحه پروفایل
                driver.get("https://www.okala.com/logout")
                time.sleep(2)

            except Exception as e:
                logger.error(f"خطا در خروج از اکانت: {str(e)}")
            
            # باز کردن صفحه ثبت‌نام برای شماره بعدی
            driver.get("https://www.okala.com/auth")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "mobile"))
            )
            
            await update.message.reply_text(
                "✅ ثبت‌نام با موفقیت انجام شد!\n\n"
                f"📱 شماره: {phone_number}\n"
                f"🔑 رمز عبور: {password}\n\n"
                f"این اطلاعات در فایل شما ذخیره شد.\n\n"
                f"لطفاً شماره موبایل بعدی را وارد کنید:",
                reply_markup=OPERATION_KEYBOARD_MARKUP
            )
            
            return PHONE
            
        except Exception as e:
            raise Exception(f"خطا در مراحل ثبت‌نام: {str(e)}")

    except Exception as e:
        logger.error(f"خطا در get_code: {str(e)}", exc_info=True)
        
        # حذف پیام در حال ثبت‌نام
        try:
            await waiting_message.delete()
        except:
            pass

        await update.message.reply_text(
            "❌ خطا در ثبت‌نام\n"
            "در حال راه‌اندازی مجدد مرورگر...",
            reply_markup=OPERATION_KEYBOARD_MARKUP
        )
        
        # بستن مرورگر فعلی
        try:
            if user.id in user_data and "driver" in user_data[user.id]:
                user_data[user.id]["driver"].quit()
        except Exception as e:
            logger.error(f"خطا در بستن مرورگر: {str(e)}")
        
        # راه‌اندازی مجدد مرورگر
        try:
            # تنظیمات پیشرفته Chrome
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--disable-geolocation")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--incognito")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
            
            # استفاده از webdriver-manager با آخرین نسخه
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # ذخیره درایور جدید برای کاربر
            user_data[user.id]["driver"] = driver

            # باز کردن سایت اوکالا
            driver.get("https://www.okala.com/auth")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "mobile"))
            )

            await update.message.reply_text(
                "✅ مرورگر با موفقیت راه‌اندازی شد.\n"
                "لطفاً شماره موبایل خود را ارسال کنید:",
                reply_markup=OPERATION_KEYBOARD_MARKUP
            )
            return PHONE

        except Exception as restart_error:
            logger.error(f"خطا در راه‌اندازی مجدد مرورگر: {str(restart_error)}")
            await update.message.reply_text(
                "❌ خطا در راه‌اندازی مجدد مرورگر. لطفاً دوباره تلاش کنید.",
                reply_markup=MAIN_KEYBOARD_MARKUP
            )
            if user.id in user_data:
                del user_data[user.id]
            return PHONE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """لغو عملیات."""
    user = update.message.from_user
    await update.message.reply_text(
        "❌ عملیات لغو شد.",
        reply_markup=MAIN_KEYBOARD_MARKUP
    )
    
    if user.id in user_data:
        try:
            if "driver" in user_data[user.id]:
                user_data[user.id]["driver"].quit()
        except:
            pass
        del user_data[user.id]
    
    return PHONE

def main() -> None:
    """راه‌اندازی ربات."""
    # اضافه کردن تنظیمات لاگ برای سرور
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log')
        ]
    )
    
    # دریافت توکن از متغیر محیطی
    token = os.getenv('TELEGRAM_TOKEN', '7949788175:AAEg1pq41YAdSCMaMzaUsdDEi1OCevszfRM')
    
    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [
                MessageHandler(filters.Regex("^شروع$"), get_phone),
                MessageHandler(filters.Regex("^نمایش اکانت‌ها$"), show_accounts),
                MessageHandler(filters.Regex("^🔑 تغییر رمز عبور$"), change_password),
                MessageHandler(filters.Regex("^❌ لغو عملیات$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
            ],
            CODE: [
                MessageHandler(filters.Regex("^❌ لغو عملیات$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_code),
            ],
            NEW_PASSWORD: [
                MessageHandler(filters.Regex("^❌ لغو عملیات$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_password),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    # اجرای ربات
    port = int(os.getenv('PORT', '10000'))  # پورت پیش‌فرض 8443
    application.run_polling(allowed_updates=Update.ALL_TYPES, port=port)

if __name__ == "__main__":
    main()