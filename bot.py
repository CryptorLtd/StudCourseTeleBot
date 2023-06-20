import logging
import asyncio
import aiomysql
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.storage import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage


logging.basicConfig(level=logging.INFO)
bot_token = 'YOUR_BOT_TOKEN'  # Замените на свой токен 
bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


class CourseRegistrationState(StatesGroup):
    START = State()
    ENTER_NAME = State()
    ENTER_EMAIL = State()
    ENTER_PHONE = State()


# Конфигурация курсов и соответствующих баз данных
courses = {
    'course1': {    # 1й курс
        'db_host': 'YOUR_DB_HOST_COURSE1',
        'db_user': 'YOUR_DB_USER_COURSE1',
        'db_password': 'YOUR_DB_PASSWORD_COURSE1',
        'db_name': 'YOUR_DB_NAME_COURSE1'
    },
    'course2': {    # 2й курс (последующие вставляйте сами)
        'db_host': 'YOUR_DB_HOST_COURSE2',
        'db_user': 'YOUR_DB_USER_COURSE2',
        'db_password': 'YOUR_DB_PASSWORD_COURSE2',
        'db_name': 'YOUR_DB_NAME_COURSE2'
    }
}


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('/register'))
    await message.reply('Добро пожаловать! Чтобы начать регистрацию, нажмите на кнопку регистрации или введите /register', reply_markup=keyboard)


@dp.message_handler(commands=['register'])
async def register_command(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for course in courses:
        keyboard.add(types.KeyboardButton(course))
    await message.reply('Выберите курс:', reply_markup=keyboard)
    await CourseRegistrationState.START.set()


@dp.message_handler(lambda message: message.text in courses.keys(), state=CourseRegistrationState.START)
async def process_course_selection(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['course'] = message.text
    await CourseRegistrationState.ENTER_NAME.set()
    await message.reply('Введите ваше имя:')


@dp.message_handler(state=CourseRegistrationState.ENTER_NAME)
async def process_name_state(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await CourseRegistrationState.ENTER_EMAIL.set()
    await message.reply('Введите ваш email:')


@dp.message_handler(state=CourseRegistrationState.ENTER_EMAIL)
async def process_email_state(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['email'] = message.text
    await CourseRegistrationState.ENTER_PHONE.set()
    await message.reply('Введите ваш номер телефона:')


@dp.message_handler(state=CourseRegistrationState.ENTER_PHONE)
async def process_phone_state(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.text

    course = courses[data['course']]
    await save_student_data(course, data['name'], data['email'], data['phone'])

    await state.finish()
    await message.reply('Спасибо! Вы успешно записаны на курс. C вами позже свяжется руководитель курса.')


async def save_student_data(course, name, email, phone):
    conn = await aiomysql.connect(
        host=course['db_host'],
        port=3306,
        user=course['db_user'],
        password=course['db_password'],
        db=course['db_name'],
        loop=asyncio.get_event_loop()
    )
    async with conn.cursor() as cursor:
        sql = "INSERT INTO students (name, email, phone) VALUES (%s, %s, %s)"
        await cursor.execute(sql, (name, email, phone))
        await conn.commit()
    conn.close()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
