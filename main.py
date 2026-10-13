import sqlite3
import random
import asyncio
import os
import sys
import logging
from telegram.error import Forbidden
from pathlib import Path



from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from telegram.ext import (

    Application,

    CommandHandler,

    CallbackQueryHandler,

    MessageHandler,

    ContextTypes,

    filters,

)



# ==================================================

# NOMER X BOT

# ==================================================



# Xavfsizlik: BotFather tokenini bu yerga yozing yoki BOT_TOKEN

# nomli environment variable o'rnating. Tokenni hech kimga yubormang.

BOT_TOKEN ="8928396781:AAFsil03ebW-S2bXFFRpicWGSYuePisZR4Q"



BASE_DIR = Path(__file__).resolve().parent

DB_NAME = BASE_DIR / "nomer_x.db"



START_MONEY = 50000

SPIN_PRICE = 1000



RARITIES = [

    ("Oddiy", 70),

    ("Mif", 20),

    ("Legenda", 8),

    ("Ultra", 2),

]



PLATE_SELL_PRICES = {

    "Oddiy": 500,

    "Mif": 2000,

    "Legenda": 5000,

    "Ultra": 15000,

}



PROMO_CODES = {

    "NOMERX": 50000,

    "START": 20000,

    "ABDURASULKOT": 1000000,

    "VIPKA": 50000000,

}



CARS = {

    "Cobalt": 15000,

    "Malibu": 30000,

    "BMW M4": 45000,

    "Mercedes-AMG": 1200000,

    "Lamborghini": 1000000,

    "bugati": 5000000,

    "Maclaren": 10000000,

}



LETTERS = ["AAA", "ABA", "AAB", "ABC", "XXX", "UZB"]





# ==================================================

# DATABASE

# ==================================================



def connect():

    return sqlite3.connect(DB_NAME)





def setup_database():

    with connect() as db:

        db.execute("""

            CREATE TABLE IF NOT EXISTS users (

                user_id INTEGER PRIMARY KEY,

                money INTEGER NOT NULL

            )

        """)

        db.execute("""

            CREATE TABLE IF NOT EXISTS plates (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                number TEXT NOT NULL,

                rarity TEXT NOT NULL,

                car TEXT DEFAULT NULL

            )

        """)

        db.execute("""

            CREATE TABLE IF NOT EXISTS cars (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                name TEXT NOT NULL

            )

        """)

        db.execute("""

            CREATE TABLE IF NOT EXISTS promo_uses (

                user_id INTEGER NOT NULL,

                code TEXT NOT NULL,

                PRIMARY KEY (user_id, code)

            )

        """)





def register_user(user_id):

    with connect() as db:

        db.execute(

            "INSERT OR IGNORE INTO users (user_id, money) VALUES (?, ?)",

            (user_id, START_MONEY),

        )





def get_money(user_id):

    with connect() as db:

        row = db.execute(

            "SELECT money FROM users WHERE user_id = ?",

            (user_id,),

        ).fetchone()

    return row[0] if row else 0





# ==================================================

# KEYBOARDS

# ==================================================



def main_keyboard():

    return InlineKeyboardMarkup([

        [

            InlineKeyboardButton("🎰 Nomer olish", callback_data="spin"),

            InlineKeyboardButton("🚘 Mashinalar", callback_data="shop"),

        ],

        [

            InlineKeyboardButton("🏠 Garajim", callback_data="garage"),

            InlineKeyboardButton("💰 Balans", callback_data="balance"),

        ],

        [

            InlineKeyboardButton("🎟️ Promokod", callback_data="promo"),

            InlineKeyboardButton("💸 Nomer sotish", callback_data="sell"),

        ],

    ])





def back_keyboard():

    return InlineKeyboardMarkup([

        [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="home")]

    ])





async def show_menu(query, text="🚘 NOMER X — Bosh menyu"):

    await query.edit_message_text(text, reply_markup=main_keyboard())





# ==================================================

# START

# ==================================================



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    with connect() as db:

        db.execute(

            "INSERT OR IGNORE INTO users (user_id, money) VALUES (?, ?)",

            (user.id, START_MONEY),

        )

    context.user_data["waiting_promo"] = False



    await update.effective_message.reply_text(

        f"🚘 Xush kelibsiz, {user.first_name}!\n\n"

        "🔥 NOMER X o'yiniga xush kelibsiz!\n\n"

        f"💰 Boshlang'ich pul: {START_MONEY:,} coin\n"

        f"🎰 Bitta aylantirish: {SPIN_PRICE:,} coin\n\n"

        "Nima qilamiz?",

        reply_markup=main_keyboard(),

    )





# ==================================================

# PLATE GENERATOR

# ==================================================



def generate_plate():

    rarity = random.choices(

        [item[0] for item in RARITIES],

        weights=[item[1] for item in RARITIES],

        k=1,

    )[0]

    region = random.choice(["01", "10", "20", "25", "30", "40"])

    letters = random.choice(LETTERS)

    digits = random.randint(100, 999)



    if rarity == "Mif":

        digits = random.choice([111, 222, 333, 555, 777, 888, 999])

    elif rarity == "Legenda":

        digits = random.choice([111, 222, 333, 777, 888, 999])

        letters = random.choice(["AAA", "XXX", "UZB"])

    elif rarity == "Ultra":

        digits = 777

        letters = random.choice(["AAA", "XXX", "UZB"])



    return f"{region} {digits} {letters}", rarity





# ==================================================

# SPIN: charge and save number

# ==================================================



async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id



    with connect() as db:

        db.execute(

            "INSERT OR IGNORE INTO users (user_id, money) VALUES (?, ?)",

            (user_id, START_MONEY),

        )

        row = db.execute(

            "SELECT money FROM users WHERE user_id = ?", (user_id,)

        ).fetchone()



        if not row or row[0] < SPIN_PRICE:

            money = row[0] if row else 0

            await query.edit_message_text(

                "❌ Pul yetarli emas!\n"

                f"Kerak: {SPIN_PRICE:,} coin\n"

                f"Sizda: {money:,} coin",

                reply_markup=back_keyboard(),

            )

            return



        number, rarity = generate_plate()

        db.execute(

            "UPDATE users SET money = money - ? WHERE user_id = ?",

            (SPIN_PRICE, user_id),

        )

        db.execute(

            "INSERT INTO plates (user_id, number, rarity) VALUES (?, ?, ?)",

            (user_id, number, rarity),

        )

        new_money = row[0] - SPIN_PRICE



    emojis = {"Oddiy": "⚪", "Mif": "🔵", "Legenda": "🟣", "Ultra": "🟡"}

    await query.edit_message_text(

        "🎉 YANGI NOMER!\n\n"

        f"🎫 Nomeringiz: {number}\n"

        f"{emojis.get(rarity, '⚪')} Daraja: {rarity}\n\n"

        f"💰 Qolgan pul: {new_money:,} coin\n"

        "✅ Nomer garajingizga saqlandi.",

        reply_markup=main_keyboard(),

    )





# ==================================================

# BALANCE

# ==================================================



async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    with connect() as db:

        db.execute(

            "INSERT OR IGNORE INTO users (user_id, money) VALUES (?, ?)",

            (user_id, START_MONEY),

        )

        money = db.execute(

            "SELECT money FROM users WHERE user_id = ?", (user_id,)

        ).fetchone()[0]



    await query.edit_message_text(

        f"💰 Sizning balansingiz: {money:,} coin",

        reply_markup=back_keyboard(),

    )





# ==================================================

# CAR SHOP / BUY CAR

# ==================================================



async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    keyboard = [

        [InlineKeyboardButton(

            f"🚘 {name} — {price:,} coin", callback_data=f"buy:{name}"

        )]

        for name, price in CARS.items()

    ]

    keyboard.append([InlineKeyboardButton("⬅️ Bosh menyu", callback_data="home")])

    await query.edit_message_text(

        "🚘 MASHINALAR DO'KONI\n\nO'zingizga mashina tanlang:",

        reply_markup=InlineKeyboardMarkup(keyboard),

    )





async def buy_car(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    name = query.data.split(":", 1)[1]

    price = CARS.get(name)

    if price is None:

        await query.edit_message_text("❌ Mashina topilmadi.", reply_markup=main_keyboard())

        return



    with connect() as db:

        db.execute(

            "INSERT OR IGNORE INTO users (user_id, money) VALUES (?, ?)",

            (user_id, START_MONEY),

        )

        money = db.execute(

            "SELECT money FROM users WHERE user_id = ?", (user_id,)

        ).fetchone()[0]

        if money < price:

            await query.edit_message_text(

                "❌ Pul yetarli emas!\n\n"

                f"🚘 Mashina: {name}\n💵 Narxi: {price:,} coin\n"

                f"💰 Sizda: {money:,} coin",

                reply_markup=back_keyboard(),

            )

            return

        db.execute(

            "UPDATE users SET money = money - ? WHERE user_id = ?",

            (price, user_id),

        )

        db.execute("INSERT INTO cars (user_id, name) VALUES (?, ?)", (user_id, name))

        money -= price



    await query.edit_message_text(

        f"🎉 Tabriklaymiz!\n\n🚘 Siz {name} sotib oldingiz!\n"

        f"💰 Qolgan pul: {money:,} coin",

        reply_markup=main_keyboard(),

    )





# ==================================================

# GARAGE

# ==================================================



async def garage(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id



    with connect() as db:

        cars = db.execute(

            "SELECT id, name FROM cars WHERE user_id = ? ORDER BY id DESC",

            (user_id,),

        ).fetchall()

        plates = db.execute(

            "SELECT id, number, rarity, car FROM plates "

            "WHERE user_id = ? ORDER BY id DESC",

            (user_id,),

        ).fetchall()



    message = "🏠 SIZNING GARAJINGIZ\n\n🚘 MASHINALAR:\n"

    message += "".join(f"• {name}\n" for _, name in cars) if cars else "Hozircha mashinangiz yo'q.\n"

    message += "\n🎫 NOMERLAR:\n"

    if plates:

        for _, number, rarity, car in plates:

            installed = f" — {car} ga o'rnatilgan" if car else ""

            message += f"• {number} ({rarity}){installed}\n"

    else:

        message += "Hozircha nomeringiz yo'q.\n"



    keyboard = [

        [InlineKeyboardButton(f"🎫 {name} ga nomer o'rnatish", callback_data=f"install:{car_id}")]

        for car_id, name in cars

    ]

    keyboard.append([InlineKeyboardButton("⬅️ Bosh menyu", callback_data="home")])

    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))





# ==================================================

# INSTALL PLATE ON CAR

# ==================================================



async def install_plate(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    car_id = int(query.data.split(":", 1)[1])



    with connect() as db:

        car = db.execute(

            "SELECT name FROM cars WHERE id=? AND user_id=?", (car_id, user_id)

        ).fetchone()

        plates = db.execute(

            "SELECT id, number, rarity FROM plates WHERE user_id=? AND car IS NULL",

            (user_id,),

        ).fetchall()



    if not car:

        await query.edit_message_text("❌ Mashina topilmadi.", reply_markup=back_keyboard())

        return

    if not plates:

        await query.edit_message_text(

            "❌ O'rnatish uchun bo'sh nomeringiz yo'q. Avval nomer oling!",

            reply_markup=back_keyboard(),

        )

        return



    keyboard = [

        [InlineKeyboardButton(f"{number} ({rarity})", callback_data=f"plate:{car_id}:{plate_id}")]

        for plate_id, number, rarity in plates

    ]

    keyboard.append([InlineKeyboardButton("⬅️ Bosh menyu", callback_data="home")])

    await query.edit_message_text(

        f"🚘 Mashina: {car[0]}\n\nQaysi nomerni o'rnatamiz?",

        reply_markup=InlineKeyboardMarkup(keyboard),

    )





async def apply_plate(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    _, car_id, plate_id = query.data.split(":")

    car_id, plate_id = int(car_id), int(plate_id)



    with connect() as db:

        car = db.execute(

            "SELECT name FROM cars WHERE id=? AND user_id=?", (car_id, user_id)

        ).fetchone()

        plate = db.execute(

            "SELECT number FROM plates WHERE id=? AND user_id=? AND car IS NULL",

            (plate_id, user_id),

        ).fetchone()

        if car and plate:

            db.execute(

                "UPDATE plates SET car=? WHERE id=? AND user_id=? AND car IS NULL",

                (car[0], plate_id, user_id),

            )



    if car and plate:

        message = f"✅ NOMER O'RNATILDI!\n\n🚘 Mashina: {car[0]}\n🎫 Nomer: {plate[0]}"

    else:

        message = "❌ Mashina yoki bo'sh nomer topilmadi."



    await query.edit_message_text(message, reply_markup=main_keyboard())





# ==================================================

# PROMOCODES

# ==================================================



async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    context.user_data["waiting_promo"] = True

    await query.message.reply_text(

        "🎟️ Promokodni yuboring:\nMasalan: NOMERX\n\nBekor qilish uchun /cancel yozing."

    )





async def promo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("waiting_promo"):

        return



    code = update.message.text.strip().upper()

    user_id = update.effective_user.id

    context.user_data["waiting_promo"] = False



    with connect() as db:

        db.execute(

            "INSERT OR IGNORE INTO users (user_id, money) VALUES (?, ?)",

            (user_id, START_MONEY),

        )



        if code not in PROMO_CODES:

            await update.message.reply_text(

                "❌ Promokod noto'g'ri!", reply_markup=main_keyboard()

            )

            return



        used = db.execute(

            "SELECT 1 FROM promo_uses WHERE user_id=? AND code=?",

            (user_id, code),

        ).fetchone()

        if used:

            await update.message.reply_text(

                "⚠️ Bu promokoddan oldin foydalangansiz!",

                reply_markup=main_keyboard(),

            )

            return



        reward = PROMO_CODES[code]

        db.execute(

            "INSERT INTO promo_uses (user_id, code) VALUES (?, ?)", (user_id, code)

        )

        db.execute(

            "UPDATE users SET money=money+? WHERE user_id=?", (reward, user_id)

        )



    await update.message.reply_text(

        f"✅ Promokod qabul qilindi!\n🎁 Mukofot: {reward:,} coin\n"

        f"💰 Balans: {get_money(user_id):,} coin",

        reply_markup=main_keyboard(),

    )





async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["waiting_promo"] = False

    await update.effective_message.reply_text(

        "Bekor qilindi.", reply_markup=main_keyboard()

    )





# ==================================================

# SELL PLATE

# ==================================================



async def sell_plates(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id



    with connect() as db:

        plates = db.execute(

            "SELECT id, number, rarity FROM plates "

            "WHERE user_id=? AND car IS NULL ORDER BY id DESC",

            (user_id,),

        ).fetchall()



    if not plates:

        await query.edit_message_text(

            "❌ Sotish uchun bo'sh nomeringiz yo'q!",

            reply_markup=back_keyboard(),

        )

        return



    keyboard = []

    for plate_id, number, rarity in plates:

        price = PLATE_SELL_PRICES.get(rarity, 0)

        keyboard.append([

            InlineKeyboardButton(

                f"💸 {number} — {price:,} coin",

                callback_data=f"sellplate:{plate_id}",

            )

        ])

    keyboard.append([InlineKeyboardButton("⬅️ Bosh menyu", callback_data="home")])

    await query.edit_message_text(

        "💸 NOMER SOTISH\n\nSotmoqchi bo'lgan nomeringizni tanlang:",

        reply_markup=InlineKeyboardMarkup(keyboard),

    )





async def sell_one_plate(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    plate_id = int(query.data.split(":", 1)[1])



    with connect() as db:

        plate = db.execute(

            "SELECT number, rarity FROM plates "

            "WHERE id=? AND user_id=? AND car IS NULL",

            (plate_id, user_id),

        ).fetchone()



        if not plate:

            await query.edit_message_text(

                "❌ Nomer topilmadi yoki sotilgan/o'rnatilgan.",

                reply_markup=main_keyboard(),

            )

            return



        number, rarity = plate

        price = PLATE_SELL_PRICES.get(rarity, 0)

        if price <= 0:

            await query.edit_message_text("❌ Bu nomerni sotib bo'lmaydi.", reply_markup=main_keyboard())

            return



        deleted = db.execute(

            "DELETE FROM plates WHERE id=? AND user_id=? AND car IS NULL",

            (plate_id, user_id),

        )

        if deleted.rowcount != 1:

            await query.edit_message_text("❌ Nomer sotilmadi.", reply_markup=main_keyboard())

            return



        db.execute(

            "UPDATE users SET money=money+? WHERE user_id=?", (price, user_id)

        )



    await query.edit_message_text(

        f"✅ NOMER SOTILDI!\n\n🎫 Nomer: {number}\n"

        f"💵 Narx: {price:,} coin\n"

        f"💰 Yangi balans: {get_money(user_id):,} coin",

        reply_markup=main_keyboard(),

    )





# ==================================================

# BUTTON ROUTER

# ==================================================



async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    data = query.data or ""



    if data == "home":

        await query.answer()

        await show_menu(query)

    elif data == "spin":

        await spin(update, context)

    elif data == "shop":

        await shop(update, context)

    elif data == "garage":

        await garage(update, context)

    elif data == "balance":

        await balance(update, context)

    elif data == "promo":

        await promo(update, context)

    elif data == "sell":

        await sell_plates(update, context)

    elif data.startswith("buy:"):

        await buy_car(update, context)

    elif data.startswith("install:"):

        await install_plate(update, context)

    elif data.startswith("plate:"):

        await apply_plate(update, context)

    elif data.startswith("sellplate:"):

        await sell_one_plate(update, context)

    else:

        await query.answer("Noma'lum tugma", show_alert=True)





# ==================================================

# ERROR LOGGING
# ==================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def error_handler(update, context):
    error = context.error

    if isinstance(error, Forbidden):
        logger.warning(
            "Telegram запретил отправку сообщения: "
            "пользователь мог заблокировать бота."
        )
        return

    logger.error(
        "Ошибка при обработке обновления:",
        exc_info=error,
    )


# ==================================================

# MAIN

async def restart_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    # Впиши сюда свой числовой Telegram ID
    ADMIN_ID = 7172054998

    if update.effective_user.id != ADMIN_ID:
        await update.effective_message.reply_text(
            "⛔ Нет доступа."
        )
        return

    await update.effective_message.reply_text(
        "🔄 Nomer X Bot qayta ishga tushmoqda..."
    )

    await asyncio.sleep(2)

    os.execv(sys.executable, [sys.executable] + sys.argv)


# ==================================================



def main():

    if not BOT_TOKEN or BOT_TOKEN == "BU_YERGA_YANGI_BOTFATHER_TOKEN":

        raise RuntimeError(

            "Bot tokeni kiritilmagan. main.py ichidagi BOT_TOKEN qiymatini to'ldiring."

        )



    setup_database()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(40)
        .write_timeout(30)
        .pool_timeout(30)
        .get_updates_connect_timeout(30)
        .get_updates_read_timeout(45)
        .get_updates_write_timeout(30)
        .get_updates_pool_timeout(30)
        .build()
    )



    app.add_handler(CommandHandler("start", start))

    app.add_handler(CommandHandler("cancel", cancel))

    app.add_handler(CallbackQueryHandler(buttons))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, promo_text))
    app.add_error_handler(error_handler)



    print("Nomer X bot ishga tushdi!")

    # Polling retries after temporary network errors.
    app.run_polling(
        poll_interval=1.0,
        timeout=30,
        bootstrap_retries=-1,
        drop_pending_updates=False,
    )





if __name__ == "__main__":

    main()
