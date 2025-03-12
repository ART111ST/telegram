import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from collections import defaultdict

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загружаем токен из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ Токен бота не найден! Проверьте файл .env")

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# ID администратора
ADMIN_ID = 5685631367

# Список пользователей, которым разрешено отправлять заявку
users_in_request_mode = set()

# Статистика заявок
requests_stats = defaultdict(int)
user_requests = {}

# Адрес кошелька TON
TON_WALLET_ADDRESS = "UQDIOasS2M_s8vvwt8XT7rduysajUwOwVgazra4rjXc8nIGp"

# Главное меню
builder = InlineKeyboardBuilder()
builder.button(text="📸 Instagram", url="https://www.instagram.com/a_eco_official")
builder.button(text="📦 Оставить заявку", callback_data="submit_request")
builder.button(text="🔍 Подробнее", callback_data="more_info")
builder.button(text="❤️ Поддержать", callback_data="support")
builder.adjust(1)
kb = builder.as_markup()

# Кнопка поддержки
support_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💰 Поддержать нас в TON", url=f"https://t.me/wallet?start={TON_WALLET_ADDRESS}")],
    [InlineKeyboardButton(text="📎 Отправить чек", callback_data="send_receipt")]
])

# Панель администратора
admin_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📊 Статистика", callback_data="view_stats")],
    [InlineKeyboardButton(text="📌 Управление заявками", callback_data="manage_requests")]
])

# Обработчик команды /start
@router.message(Command("start"))
async def start_command(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🔧 Панель администратора", reply_markup=admin_kb)
    else:
        await message.answer(
            "🌍 Приветствуем вас! Мы - компания A-ECO ♻, занимаемся переработкой пластика!\n\n"
            "📩 Оставьте заявку, если у вас накопился пластик!\n\n"
            "👇 Выберите нужный раздел:",
            reply_markup=kb
        )

# Обработчик кнопок
@router.callback_query(lambda c: True)
async def handle_callback(callback_query: types.CallbackQuery):
    try:
        user_id = callback_query.from_user.id

        if callback_query.data == "submit_request":
            users_in_request_mode.add(user_id)
            await callback_query.message.answer(
                "📋 Отправьте заявку в формате:\n\n"
                "🏢 Название: [Ваше заведение]\n"
                "📍 Адрес: [Ваш адрес]\n"
                "📞 Номер: [Ваш номер]\n"
                "🕒 Время работы: [Ваше время]\n"
                "📦 Количество пластика: [В мешках или фото]"
            )
        elif callback_query.data == "more_info":
            await bot.send_message(
                user_id,
                "🔎 Полезная информация:\n\n"
                "♻ *Какие виды пластика принимаются?*\n"
                "Мы принимаем пластиковые бутылки. Этикетки можно не снимать, но их удаление упростит переработку!\n\n"
                "🗑 *Как правильно сортировать мусор?*\n"
                "1️⃣ Промывайте бутылки перед сдачей.\n"
                "2️⃣ Оставляйте крышки на бутылках.\n"
                "3️⃣ Если есть возможность, отсортируйте бутылки по цвету.\n\n"
                "🏭 *Куда идут переработанные отходы?*\n"
                "Мы перерабатываем пластиковые бутылки в пруток для 3D-печати. Из него мы создаем новые изделия и продаем его для дальнейшего использования.\n"
                "Также мы печатаем изделия любого формата по заказу.\n\n"
                "❤️ *Наши благотворительные и волонтерские инициативы*\n"
                "Мы активно участвуем в акциях по сбору пластика, производим игрушки для детей и организуем экологические инициативы. Ваш вклад помогает сделать мир лучше! 🌍💚"
            )
        elif callback_query.data == "support":
            await callback_query.message.answer("🙏 Поддержите нас TON!", reply_markup=support_kb)
        elif callback_query.data == "view_stats" and user_id == ADMIN_ID:
            await callback_query.message.answer(
                f"📊 Статистика заявок:\nПринято: {requests_stats['accepted']}\nОтклонено: {requests_stats['rejected']}"
            ) 

        elif callback_query.data == "support":
            await callback_query.message.answer("🙏 Поддержите нас TON!", reply_markup=support_kb)
        elif callback_query.data == "view_stats" and user_id == ADMIN_ID:
            await callback_query.message.answer(
                f"📊 Статистика заявок:\nПринято: {requests_stats['accepted']}\nОтклонено: {requests_stats['rejected']}"
            )
        elif callback_query.data == "manage_requests" and user_id == ADMIN_ID:
            if not user_requests:
                await callback_query.message.answer("📭 Нет новых заявок.")
            else:
                for uid, req in user_requests.items():
                    await bot.send_message(
                        ADMIN_ID,
                        f"📥 Заявка от @{uid}:\n\n{req}",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="📩 Принять", callback_data=f"accept_{uid}")],
                            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{uid}")]
                        ])
                    )
        elif callback_query.data.startswith("accept_") and user_id == ADMIN_ID:
            target_user_id = int(callback_query.data.split("_")[1])
            if target_user_id in user_requests:
                del user_requests[target_user_id]
                requests_stats["accepted"] += 1
                await bot.send_message(target_user_id, "✅ Ваша заявка принята! Мы с вами свяжемся.")
        elif callback_query.data.startswith("reject_") and user_id == ADMIN_ID:
            target_user_id = int(callback_query.data.split("_")[1])
            if target_user_id in user_requests:
                del user_requests[target_user_id]
                requests_stats["rejected"] += 1
                await bot.send_message(target_user_id, "❌ Ваша заявка отклонена.")
        await callback_query.answer()
    except Exception as e:
        logging.error(f"Ошибка: {e}")

# Обработчик заявок от пользователей
@router.message(lambda msg: msg.from_user.id in users_in_request_mode)
async def handle_request(message: Message):
    user_id = message.from_user.id
    users_in_request_mode.discard(user_id)
    user_requests[user_id] = message.text
    username = message.from_user.username or f"ID: {user_id}"
    await bot.send_message(ADMIN_ID, f"📥 Новая заявка от @{username}:\n\n{message.text}")
    await message.answer("✅ Ваша заявка отправлена!")

# Обработчик фото чека
@router.message(lambda message: message.photo)
async def handle_receipt_photo(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"ID: {user_id}"
    photo_id = message.photo[-1].file_id
    await bot.send_photo(ADMIN_ID, photo=photo_id, caption=f"📩 Новый чек от @{username}.")
    await message.answer("✅ Спасибо! Ваш чек отправлен админу.")

# Запуск бота
async def main():
    dp.include_router(router)
    logging.info("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
