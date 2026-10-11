
import json
import random
import os
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = "8928396781:AAFsil03ebW-S2bXFFRpicWGSYuePisZR4Q"
DB_FILE = "nomer_x_data.json"

# ---------- СОХРАНЕНИЕ ДАННЫХ ----------

def load_data():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data():
    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

data = load_data()

def get_user(user_id):
    key = str(user_id)

    if key not in data:
        data[key] = {
            "balance": 0,
            "history": [],
            "next_id": 1,
        }
        save_data()

    return data[key]

# ---------- НОМЕРА И ЦЕНЫ ----------

def generate_number():
    region = random.choice(["01", "10", "20", "30", "40", "50", "60", "70", "75", "80", "85", "90"])
    letters = "ABCEHKMOPTX"
    first = random.choice(letters)
    last = random.choice(letters)
    last2 = random.choice(letters)

    digits = "".join(str(random.randint(0, 9)) for _ in range(3))

    # Иногда выпадают красивые комбинации
    roll = random.random()

    if roll < 0.05:
        digits = "777"
    elif roll < 0.10:
        digits = "888"
    elif roll < 0.15:
        digits = "999"
    elif roll < 0.20:
        digits = "001"
    elif roll < 0.25:
        digits = "007"
    elif roll < 0.30:
        digits = "555"

    return f"{region} {first} {digits} {last}{last2}"

def calculate_price(number):
    digits = number.split()[2]
    letters = number.split()[3]

    # Цены вымышленные, для игровой экономики
    if len(set(digits)) == 1:
        return 15_000_000, "LEGENDARY"
    elif digits in ("007", "001"):
        return 8_000_000, "RARE"
    elif digits in ("123", "321", "555", "777", "888", "999"):
        return 5_000_000, "RARE"
    elif digits[0] == digits[1] or digits[1] == digits[2]:
        return 2_000_000, "UNCOMMON"
    elif letters[0] == letters[1]:
        return 1_500_000, "UNCOMMON"
    else:
        return 500_000, "COMMON"

def money(amount):
    return f"{amount:,}".replace(",", " ") + " сум"

# ---------- КЛАВИАТУРЫ ----------

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 Крутить номер", callback_data="spin")],
        [
            InlineKeyboardButton("💰 Продать номер", callback_data="sell"),
            InlineKeyboardButton("📜 История", callback_data="history"),
        ],
        [InlineKeyboardButton("👛 Баланс", callback_data="balance")],
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="home")]
    ])

def home_text(user):
    return (
        "🟡 <b>NOMER X</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎰 <b>АВТОМОБИЛЬНЫЕ НОМЕРА</b>\n\n"
        f"🪙 Баланс: <b>{money(user['balance'])}</b>\n\n"
        "Крути номера, узнавай их стоимость "
        "и продавай за игровые сумы.\n\n"
        "👇 Выбери действие:"
    )

# ---------- КОМАНДА START ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    await update.message.reply_text(
        home_text(user),
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )

# ---------- ОБРАБОТКА КНОПОК ----------

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)
    action = query.data

    if action == "home":
        await query.edit_message_text(
            home_text(user),
            reply_markup=main_keyboard(),
            parse_mode="HTML",
        )
        return

    if action == "spin":
        number = generate_number()
        price, rarity = calculate_price(number)

        item = {
            "id": user["next_id"],
            "number": number,
            "price": price,
            "rarity": rarity,
            "sold": False,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        }

        user["next_id"] += 1
        user["history"].insert(0, item)
        save_data()

        rarity_names = {
            "COMMON": "⚪ Обычный",
            "UNCOMMON": "🟣 Красивый",
            "RARE": "🔵 Редкий",
            "LEGENDARY": "🟡 Легендарный",
        }

        text = (
            "🟡 <b>NOMER X</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🎉 <b>ТЕБЕ ВЫПАЛ НОМЕР!</b>\n\n"
            "┏━━━━━━━━━━━━━━━━┓\n"
            f"┃ 🇺🇿 <b>{number}</b>\n"
            "┗━━━━━━━━━━━━━━━━┛\n\n"
            f"💰 Цена: <b>{money(price)}</b>\n"
            f"💎 Редкость: {rarity_names[rarity]}\n\n"
            "Номер добавлен в историю.\n"
            "Можешь продать его или крутить ещё."
        )

        await query.edit_message_text(
            text,
            reply_markup=main_keyboard(),
            parse_mode="HTML",
        )
        return

    if action == "sell":
        # Продаём самый новый номер, который ещё не продан
        item = next(
            (entry for entry in user["history"] if not entry["sold"]),
            None,
        )

        if item is None:
            await query.edit_message_text(
                "🏷️ <b>НЕТ НОМЕРОВ ДЛЯ ПРОДАЖИ</b>\n\n"
                "Сначала нажми «Крутить номер».",
                reply_markup=back_keyboard(),
                parse_mode="HTML",
            )
            return

        item["sold"] = True
        user["balance"] += item["price"]
        save_data()

        await query.edit_message_text(
            "✅ <b>НОМЕР ПРОДАН!</b>\n\n"
            f"🚘 Номер: <b>{item['number']}</b>\n"
            f"💰 Получено: <b>{money(item['price'])}</b>\n"
            f"🪙 Новый баланс: <b>{money(user['balance'])}</b>",
            reply_markup=main_keyboard(),
            parse_mode="HTML",
        )
        return

    if action == "balance":
        await query.edit_message_text(
            "👛 <b>ТВОЙ БАЛАНС</b>\n\n"
            f"🪙 {money(user['balance'])}\n\n"
            "Деньги начисляются за продажу номеров.",
            reply_markup=back_keyboard(),
            parse_mode="HTML",
        )
        return

    if action == "history":
        items = user["history"][:15]

        if not items:
            text = (
                "📜 <b>ИСТОРИЯ НОМЕРОВ</b>\n\n"
                "Пока пусто. Крути первый номер!"
            )
        else:
            lines = ["📜 <b>ИСТОРИЯ НОМЕРОВ</b>\n"]

            for item in items:
                status = "✅ Продан" if item["sold"] else "🟡 Не продан"

                lines.append(
                    f"🚘 <b>{item['number']}</b>\n"
                    f"💰 {money(item['price'])}\n"
                    f"📅 {item['date']}\n"
                    f"{status}\n"
                )

            text = "\n".join(lines)

        await query.edit_message_text(
            text,
            reply_markup=back_keyboard(),
            parse_mode="HTML",
        )
        return

# ---------- ЗАПУСК БОТА ----------

def main():
    if TOKEN == "ВСТАВЬ_СЮДА_ТОКЕН_BOTFATHER":
        raise ValueError("Сначала вставь токен своего бота в переменную TOKEN.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("NOMER X запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()

    
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

TOKEN = "8928396781:AAFsil03ebW-S2bXFFRpicWGSYuePisZR4Q"
WEB_APP_URL = "https://ТВОЙ-АДРЕС/index.html"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🚀 Открыть NOMER X",
                web_app=WebAppInfo(url=WEB_APP_URL),
            )
        ]
    ])

    await update.message.reply_text(
        "🟡 NOMER X\n\n"
        "Крути автомобильные номера, "
        "смотри их цены и продавай за игровые сумы.\n\n"
        "Нажми кнопку ниже, чтобы открыть лаунчер:",
        reply_markup=keyboard,
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("NOMER X Bot запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()

