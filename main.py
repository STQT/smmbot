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

from database import load_data, create_record, save_data, delete_object_by_id, create_record_groups, save_data_groups, \
    load_data_groups, delete_object_by_name_groups, get_object_by_name_groups, get_groups_name, \
    load_posts_using_group_id

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


def dynamic_kb(data):
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for obj in data:
        keyboard.add(KeyboardButton(obj))
    return keyboard


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


def generate_keyboard(data):
    rows = 2
    buttons_per_row = len(data) // rows + (len(data) % rows > 0)
    buttons = [KeyboardButton(button['name']) for button in data]
    button_rows = [buttons[i:i + buttons_per_row] for i in range(0, len(buttons), buttons_per_row)]
    keyboard = ReplyKeyboardMarkup(row_width=buttons_per_row, resize_keyboard=True)
    for row in button_rows:
        keyboard.add(*row)
    return keyboard


def action_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        KeyboardButton("Да"),
        KeyboardButton("Нет")
    )
    return keyboard


class Form(StatesGroup):
    get_data = State()
    get_timezone = State()
    get_group = State()
    get_post = State()


class FormChannel(StatesGroup):
    get_id = State()
    get_name = State()


class ChannelCRUD(StatesGroup):
    get_group_name = State()
    get_action = State()


class GetPosts(StatesGroup):
    get_group = State()


class GetChannelInfo(StatesGroup):
    get_channel = State()


scheduler = AsyncIOScheduler()


async def publish_delayed_posts():
    current_time = datetime.utcnow()
    delayed_posts = load_data()
    for post in delayed_posts:
        tz = datetime.strptime(post['scheduled'], "%d-%m-%Y %H:%M")
        if abs((tz - current_time).total_seconds()) < 100:
            msg = types.Message(**post['post'])
            await msg.send_copy(post['group_id'])
            delete_object_by_id(post['id'])


async def on_startup(dp):
    scheduler.add_job(publish_delayed_posts, 'interval', minutes=1)
    scheduler.start()
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", "Botni ishga tushurish"),
            types.BotCommand("schedule", "Добавить задачу"),
            types.BotCommand("myposts", "Мои посты"),
            types.BotCommand("mygroups", "Мои группы"),
            types.BotCommand("addgroup", "Добавить группу"),
            types.BotCommand("getgroupid", "Узнать ID группы (работает в группах)"),
            types.BotCommand("getchannelid", "Узнать ID канала")
        ]
    )


@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "Я бот для отложенных публикаций. Используй команду /schedule, чтобы добавить отложенную публикацию.")


@dp.message_handler(commands=['myposts'])
async def schedule(message: types.Message):
    post_having_groups = get_groups_name()
    await message.answer("Выберите группу", reply_markup=dynamic_kb(post_having_groups))
    await GetPosts.get_group.set()


@dp.message_handler(state=GetPosts.get_group)
async def get_groups(message: types.Message, state: FSMContext):
    group_id = get_object_by_name_groups(message.text)
    posts = load_posts_using_group_id(group_id)
    if not posts:
        await message.answer("Not found")
    for post in posts:
        msg = types.Message(**post['post'])
        timezone_str = post['utc']
        tz = convert_timezone_utc(timezone_str, post['scheduled'], "%d-%m-%Y %H:%M")
        await message.answer(f'Post ID: {post["id"]} \n'
                             f'{tz.strftime("%Y-%m-%d %H:%M:%S")} with TZ: {timezone_str}'
                             '👇👇👇👇👇')
        await msg.send_copy(message.from_user.id)
    await message.answer("Они точно отправятся. Отправленные посты удалятся со списка",
                         reply_markup=types.ReplyKeyboardRemove())
    await state.finish()


@dp.message_handler(commands=['mygroups', 'mychannels'])
async def schedule_groups(message: types.Message):
    groups_list = load_data_groups()
    if not groups_list:
        await message.answer("Not found")
        return
    await message.answer("Выберите группу из списка", reply_markup=generate_keyboard(groups_list))
    await ChannelCRUD.get_group_name.set()


@dp.message_handler(commands=['getgroupid'])
async def schedule_groups(message: types.Message):
    if message.chat.type == "group":
        await message.answer(f"ID группы: `{message.chat.id}`", parse_mode="MarkdownV2")
    else:
        await message.answer("Добавь меня в группу и введи эту команду чтобы узнать ID группы")


@dp.message_handler(commands=['getchannelid'])
async def schedule_groups(message: types.Message):
    await message.answer("Отправь мне пост с нужного канала чтобы узнать ID канала")
    await GetChannelInfo.get_channel.set()


@dp.message_handler(content_types=types.ContentTypes.ANY, state=GetChannelInfo.get_channel)
async def schedule_groups(message: types.Message, state: FSMContext):
    logging.info(message)
    if message.is_forward():
        await message.answer(f"ID Канала: `{message.forward_from_chat.id}`", parse_mode="MarkdownV2")
        await state.finish()
    else:
        await message.answer("Пожалуйста, отправь мне пересланное сообщение")


@dp.message_handler(commands=['addgroup', "addchannel"])
async def schedule(message: types.Message):
    await message.answer(
        "Отправьте айди группы или канала")
    await FormChannel.get_id.set()


@dp.message_handler(state=FormChannel.get_id)
async def process_get_id(msg: types.Message, state: FSMContext):
    await state.update_data(id=msg.text)
    await msg.answer("Название группы/канала")
    await FormChannel.get_name.set()


@dp.message_handler(state=ChannelCRUD.get_group_name)
async def process_group_get_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("Вы хотите удалить группу/канал?", reply_markup=action_keyboard())
    await ChannelCRUD.get_action.set()


@dp.message_handler(state=ChannelCRUD.get_action)
async def process_group_get_action(msg: types.Message, state: FSMContext):
    if msg.text == "Да":
        data = await state.get_data()
        delete_object_by_name_groups(data['name'])
        await msg.answer("Успешно удалено", reply_markup=types.ReplyKeyboardRemove())
    else:
        await msg.answer("Отменено", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()


@dp.message_handler(state=FormChannel.get_name)
async def process_get_name(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    saving_data = create_record_groups(msg.text, data['id'])
    save_data_groups(saving_data)
    await msg.answer("Успешно добавился")
    await state.finish()


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
    groups_list = load_data_groups()
    await msg.answer("Выбери группу", reply_markup=generate_keyboard(groups_list))
    await Form.get_group.set()


@dp.message_handler(state=Form.get_group)
async def process_schedule_get_group(msg: types.Message, state: FSMContext):
    await state.update_data(group_name=msg.text)
    await msg.answer("Отправь мне пост одним сообщением", reply_markup=types.ReplyKeyboardRemove())
    await Form.get_post.set()


@dp.message_handler(state=Form.get_post, content_types=types.ContentTypes.ANY)
async def get_post_form(m: types.Message, state: FSMContext):
    data = await state.get_data()
    group_id = get_object_by_name_groups(data['group_name'])
    saving_data = create_record(m.as_json(), data['date'], utc=data['utc'], group_id=group_id)
    save_data(saving_data)
    await m.answer("Отложенная публикация успешно добавлена!")
    await state.finish()


@dp.message_handler(state="*")
async def echo(msg: types.Message, state: FSMContext):
    await msg.answer(
        "Я бот для отложенных публикаций. Используй команду /schedule, чтобы добавить отложенную публикацию.")


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, on_startup=on_startup)
