import logging
import os

from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from database import load_data, create_record, save_data, delete_object_by_id

load_dotenv()  # take environment variables from .env.

TOKEN = os.getenv("TOKEN")
GROUP_ID = 6201336345

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
)
logger.info("Starting bot")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


def convert_timezone_utc(timezone_str, date_time_str, date_time_format="%Y-%m-%d %H:%M:%S"):
    offset_hours = int(timezone_str[3:])
    dt = datetime.strptime(date_time_str, date_time_format)
    offset = timedelta(hours=offset_hours)
    dt_with_offset = dt + offset
    return dt_with_offset


def generate_timezones_keyboard():
    row_width = 2
    timezones = [f'UTC{offset}' if offset < 0 else f'UTC+{offset}' for offset in range(-12, 13)]

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=row_width)
    buttons = [KeyboardButton(text=timezone) for timezone in timezones]

    keyboard.add(*buttons)
    return keyboard


class Form(StatesGroup):
    get_data = State()
    get_timezone = State()
    get_post = State()


scheduler = AsyncIOScheduler()


async def publish_delayed_posts():
    current_time = datetime.utcnow()
    delayed_posts = load_data()
    for post in delayed_posts:
        tz = datetime.strptime(post['scheduled'], "%d-%m-%Y %H:%M")
        if abs((tz - current_time).total_seconds()) < 100:
            msg = types.Message(**post['post'])
            await msg.send_copy(GROUP_ID)
            delete_object_by_id(post['id'])


async def on_startup(dp):
    scheduler.add_job(publish_delayed_posts, 'interval', minutes=1)
    scheduler.start()


@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "Я бот для отложенных публикаций. Используй команду /schedule, чтобы добавить отложенную публикацию.")


@dp.message_handler(commands=['myposts'])
async def schedule(message: types.Message):
    posts = load_data()
    if not posts:
        await message.answer("Not found")
    for post in posts:
        msg = types.Message(**post['post'])
        timezone_str = post['utc']
        tz = convert_timezone_utc(timezone_str, post['scheduled'], "%d-%m-%Y %H:%M")
        await msg.answer(f'Post ID: {post["id"]} \n'
                         f'{tz.strftime("%Y-%m-%d %H:%M:%S")} with TZ: {timezone_str}'
                         '👇👇👇👇👇')
        await msg.send_copy(message.from_user.id)


@dp.message_handler(commands=['schedule'])
async def schedule(message: types.Message):
    await message.answer(
        "Отправь мне текст для отложенной публикации и время в формате DD-MM-YYY HH:MM (по UTC). \n"
        "Например: 13-11-2023 18:30")
    await Form.get_data.set()


@dp.message_handler(state=Form.get_data)
async def process_schedule(msg: types.Message, state: FSMContext):
    try:
        # Attempt to convert the string to a datetime object
        datetime.strptime(msg.text, "%d-%m-%Y %H:%M")
        await state.update_data(date=msg.text)
        await msg.answer("Выбери таймзону", reply_markup=generate_timezones_keyboard())
        await Form.get_timezone.set()
    except ValueError:
        # Handle the case where the conversion fails
        await msg.answer("Ошибка: Incorrect date format. Please provide the date in the format 'DD-MM-YYYY HH:MM'")


@dp.message_handler(lambda message: message.text.startswith('UTC'), state=Form.get_timezone)
async def process_timezone(msg: types.Message, state: FSMContext):
    await state.update_data(utc=msg.text)
    await msg.answer("Отправь мне пост одним сообщением", reply_markup=types.ReplyKeyboardRemove())
    await Form.get_post.set()


@dp.message_handler(state=Form.get_post)
async def get_postqweq(m: types.Message, state: FSMContext):
    data = await state.get_data()
    saving_data = create_record(m.as_json(), data['date'], utc=data['utc'])
    save_data(saving_data)
    await m.answer("Отложенная публикация успешно добавлена!")
    await state.finish()


@dp.message_handler(state="*")
async def qweqwrq(msg: types.Message, state: FSMContext):
    await msg.answer(
        "Я бот для отложенных публикаций. Используй команду /schedule, чтобы добавить отложенную публикацию.")


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, on_startup=on_startup)
