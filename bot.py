import sqlite3
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# ================================================
#  ТВОИ ДАННЫЕ
# ================================================
TOKEN = "8905575206:AAHb16Dxm4AyY5UEKXx2KIE1bfOe4yoUK2g"
ADMIN_ID = 1714472061
CARD_NUMBER = "2202208013041323"
ADMIN_USERNAME = "@asQ20000"
PRICE = 125
# ================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# --- БАЗА ДАННЫХ (расширенная) ---
def init_db():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        registered_at TEXT,
        subscription_end TEXT,
        level INTEGER DEFAULT 0,
        exp INTEGER DEFAULT 0,
        water_norm INTEGER DEFAULT 2500,
        moti_hour INTEGER DEFAULT 7
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        category TEXT,
        done INTEGER DEFAULT 0,
        added_at TEXT,
        done_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        calories INTEGER,
        protein REAL,
        fat REAL,
        carbs REAL,
        added_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS water (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        added_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        wtype TEXT,
        duration INTEGER,
        date TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS quotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        author TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sleep (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        hours REAL,
        date TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS weekly_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        done INTEGER DEFAULT 0,
        week_start TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS nofap (
        user_id INTEGER PRIMARY KEY,
        start_date TEXT,
        last_checkin TEXT,
        streak INTEGER DEFAULT 0,
        longest_streak INTEGER DEFAULT 0,
        total_days INTEGER DEFAULT 0,
        last_reset TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# --- МОТИВИРУЮЩИЕ ФРАЗЫ ---
def seed_quotes():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM quotes")
    if c.fetchone()[0] == 0:
        quotes = [
            ("Ты не обязан быть великим, но ты обязан начать.", "Зиг Зиглар"),
            ("Дисциплина — это мост между целями и достижениями.", "Джим Рон"),
            ("Каждое утро у тебя есть два выбора: продолжать спать и мечтать, или встать и воплощать мечты в реальность.", "Неизвестный"),
            ("Маленькие ежедневные усилия суммируются в огромные результаты.", "Робин Шарма"),
            ("Твоя единственная конкуренция — это ты вчерашний.", "Неизвестный"),
            ("Ты можешь всё, если готов заплатить цену.", "Арнольд Шварценеггер"),
            ("Сложно не значит невозможно.", "Неизвестный"),
            ("Сделай сегодня больше, чем вчера.", "Неизвестный"),
            ("Ты — сумма твоих привычек.", "Уильям Джеймс"),
            ("Победа любит подготовленных.", "Неизвестный")
        ]
        c.executemany("INSERT INTO quotes (text, author) VALUES (?, ?)", quotes)
        conn.commit()
    conn.close()

seed_quotes()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def register_user(user_id, username):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, registered_at) VALUES (?, ?, ?)",
              (user_id, username, datetime.now().isoformat()))
    # Инициализация nofap
    c.execute("INSERT OR IGNORE INTO nofap (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT level, exp, water_norm, moti_hour FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def add_exp(user_id, amount):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT level, exp FROM users WHERE user_id=?", (user_id,))
    level, exp = c.fetchone()
    exp += amount
    if exp >= 100:
        level += 1
        exp = 0
    c.execute("UPDATE users SET level=?, exp=? WHERE user_id=?", (level, exp, user_id))
    conn.commit()
    conn.close()

def is_subscribed(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT subscription_end FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        return datetime.fromisoformat(row[0]) > datetime.now()
    return False

def set_subscription(user_id, days=30):
    end = datetime.now() + timedelta(days=days)
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("UPDATE users SET subscription_end=? WHERE user_id=?", (end.isoformat(), user_id))
    conn.commit()
    conn.close()

def get_moti_hour(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT moti_hour FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 7

def set_moti_hour(user_id, hour):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("UPDATE users SET moti_hour=? WHERE user_id=?", (hour, user_id))
    conn.commit()
    conn.close()

# --- ЗАДАЧИ ---
def add_task(user_id, text, category="Общее"):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, text, category, added_at) VALUES (?, ?, ?, ?)",
              (user_id, text, category, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    add_exp(user_id, 5)

def get_tasks(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT id, text, category, done FROM tasks WHERE user_id=? AND done=0 ORDER BY id", (user_id,))
    active = c.fetchall()
    c.execute("SELECT id, text, category, done, done_at FROM tasks WHERE user_id=? AND done=1 ORDER BY done_at DESC LIMIT 10", (user_id,))
    done = c.fetchall()
    conn.close()
    return active, done

def mark_done(user_id, task_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET done=1, done_at=? WHERE id=? AND user_id=?", (datetime.now().isoformat(), task_id, user_id))
    conn.commit()
    conn.close()
    add_exp(user_id, 10)

def delete_task(user_id, task_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, user_id))
    conn.commit()
    conn.close()

# --- ЕДА ---
def add_meal(user_id, name, calories, protein, fat, carbs):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO meals (user_id, name, calories, protein, fat, carbs, added_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (user_id, name, calories, protein, fat, carbs, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    add_exp(user_id, 3)

def get_today_meals(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT name, calories, protein, fat, carbs FROM meals WHERE user_id=? AND date(added_at)=date(?)",
              (user_id, datetime.now().isoformat()))
    return c.fetchall()

# --- ВОДА ---
def add_water(user_id, amount):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO water (user_id, amount, added_at) VALUES (?, ?, ?)",
              (user_id, amount, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    add_exp(user_id, 2)

def get_today_water(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM water WHERE user_id=? AND date(added_at)=date(?)", (user_id, datetime.now().isoformat()))
    total = c.fetchone()[0] or 0
    conn.close()
    return total

def get_water_norm(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT water_norm FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 2500

def set_water_norm(user_id, norm):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("UPDATE users SET water_norm=? WHERE user_id=?", (norm, user_id))
    conn.commit()
    conn.close()

# --- ТРЕНИРОВКИ ---
def add_workout(user_id, wtype, duration):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO workouts (user_id, wtype, duration, date) VALUES (?, ?, ?, ?)",
              (user_id, wtype, duration, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    add_exp(user_id, 15)

def get_today_workout_count(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM workouts WHERE user_id=? AND date(date)=date(?)", (user_id, datetime.now().isoformat()))
    return c.fetchone()[0] or 0

# --- СОН ---
def add_sleep(user_id, hours):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO sleep (user_id, hours, date) VALUES (?, ?, ?)",
              (user_id, hours, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    add_exp(user_id, 5)

def get_week_sleep(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    c.execute("SELECT hours, date FROM sleep WHERE user_id=? AND date>?", (user_id, week_ago))
    rows = c.fetchall()
    conn.close()
    return rows

# --- ЦЕЛИ НЕДЕЛИ ---
def get_week_start():
    now = datetime.now()
    start = now - timedelta(days=now.weekday())
    return start.date().isoformat()

def add_weekly_goal(user_id, text):
    week = get_week_start()
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO weekly_goals (user_id, text, week_start) VALUES (?, ?, ?)",
              (user_id, text, week))
    conn.commit()
    conn.close()
    add_exp(user_id, 5)

def get_weekly_goals(user_id):
    week = get_week_start()
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT id, text, done FROM weekly_goals WHERE user_id=? AND week_start=? ORDER BY id", (user_id, week))
    goals = c.fetchall()
    conn.close()
    return goals

def mark_weekly_goal_done(user_id, goal_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("UPDATE weekly_goals SET done=1 WHERE id=? AND user_id=?", (goal_id, user_id))
    conn.commit()
    conn.close()
    add_exp(user_id, 10)

def delete_weekly_goal(user_id, goal_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("DELETE FROM weekly_goals WHERE id=? AND user_id=?", (goal_id, user_id))
    conn.commit()
    conn.close()

def cleanup_old_weekly_goals():
    week = get_week_start()
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("DELETE FROM weekly_goals WHERE week_start < ?", (week,))
    conn.commit()
    conn.close()

# --- СТАТИСТИКА ---
def get_week_stats(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    c.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND done=1 AND done_at>?", (user_id, week_ago))
    tasks_done = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM workouts WHERE user_id=? AND date>?", (user_id, week_ago))
    workouts = c.fetchone()[0]
    c.execute("SELECT SUM(amount) FROM water WHERE user_id=? AND date(added_at)>?", (user_id, week_ago))
    water = c.fetchone()[0] or 0
    c.execute("SELECT SUM(calories) FROM meals WHERE user_id=? AND date(added_at)>?", (user_id, week_ago))
    cal = c.fetchone()[0] or 0
    c.execute("SELECT AVG(hours) FROM sleep WHERE user_id=? AND date>?", (user_id, week_ago))
    avg_sleep = c.fetchone()[0] or 0
    conn.close()
    return tasks_done, workouts, water, cal, avg_sleep

def get_random_quote():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT text, author FROM quotes ORDER BY RANDOM() LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return "У тебя всё получится!", "Неизвестный"

def get_all_users():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT user_id, subscription_end FROM users")
    return c.fetchall()

# ================== НОВАЯ СИСТЕМА NOFAP ==================
def get_nofap_data(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT start_date, last_checkin, streak, longest_streak, total_days, last_reset FROM nofap WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def init_nofap(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT OR IGNORE INTO nofap (user_id, start_date, last_checkin, streak, longest_streak, total_days, last_reset) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (user_id, now, now, 0, 0, 0, now))
    conn.commit()
    conn.close()

def checkin_nofap(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    now = datetime.now().isoformat()
    today = datetime.now().date()
    c.execute("SELECT last_checkin, streak, longest_streak, total_days FROM nofap WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        init_nofap(user_id)
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute("SELECT last_checkin, streak, longest_streak, total_days FROM nofap WHERE user_id=?", (user_id,))
        row = c.fetchone()
    last_checkin = datetime.fromisoformat(row[0]).date()
    streak = row[1]
    longest = row[2]
    total = row[3]
    # Если сегодня уже отмечали – ничего не делаем
    if last_checkin == today:
        conn.close()
        return False, streak, longest, total
    # Если пропущен день – сбрасываем стрик
    if last_checkin < today - timedelta(days=1):
        streak = 0
    streak += 1
    total += 1
    if streak > longest:
        longest = streak
    c.execute("UPDATE nofap SET last_checkin=?, streak=?, longest_streak=?, total_days=? WHERE user_id=?",
              (now, streak, longest, total, user_id))
    conn.commit()
    conn.close()
    # Добавляем опыт за отметку дня
    add_exp(user_id, 10)
    return True, streak, longest, total

def reset_nofap(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("SELECT longest_streak FROM nofap WHERE user_id=?", (user_id,))
    row = c.fetchone()
    longest = row[0] if row else 0
    c.execute("UPDATE nofap SET streak=0, last_reset=?, total_days=0 WHERE user_id=?", (now, user_id))
    conn.commit()
    conn.close()
    return longest

def get_nofap_motivation():
    messages = [
        "Ты сильнее своих желаний. Каждый день без срыва — это победа!",
        "Дисциплина — это умение делать то, что нужно, даже когда не хочется.",
        "Ты строишь себя заново. Каждое утро — новый шанс.",
        "Стрик — это не просто число, это твоя новая личность.",
        "Вспомни, зачем ты начал. Ты уже лучше, чем вчера."
    ]
    return random.choice(messages)

# --- КЛАВИАТУРА ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Мой план"), KeyboardButton(text="➕ Добавить задачу")],
        [KeyboardButton(text="🍽️ Добавить еду"), KeyboardButton(text="💧 Вода")],
        [KeyboardButton(text="🏋️ Тренировка"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="🌟 Мотивация"), KeyboardButton(text="💳 Подписка")],
        [KeyboardButton(text="😴 Сон"), KeyboardButton(text="📅 Цели недели")],
        [KeyboardButton(text="🚫 Воздержание"), KeyboardButton(text="⚙️ Настройки")]
    ],
    resize_keyboard=True
)

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username or "без username")
    await message.answer(
        "🔥 Добро пожаловать в 520 System!\n"
        "Твой помощник для дисциплины и здоровья.\n\n"
        "⚠️ Бот работает в демо-режиме. Для доступа ко всем функциям оформи подписку 125 ₽/мес.\n"
        "Нажми '💳 Подписка' для оплаты.\n\n"
        "🌟 Каждое утро в 7:00 я буду присылать мотивирующую фразу!",
        reply_markup=main_kb
    )

@dp.message(lambda m: m.text == "💳 Подписка")
async def subscribe(message: types.Message):
    user_id = message.from_user.id
    if is_subscribed(user_id):
        await message.answer("✅ У тебя уже есть активная подписка! Пользуйся.")
        return
    await message.answer(
        f"💳 ОФОРМЛЕНИЕ ПОДПИСКИ ({PRICE} ₽/мес):\n\n"
        "1️⃣ Переведи сумму на карту: **" + CARD_NUMBER + "**\n"
        "2️⃣ В назначении платежа укажи свой Telegram ID: " + str(user_id) + "\n"
        "3️⃣ После оплаты напиши администратору → " + ADMIN_USERNAME + "\n"
        "✅ Подписка активируется вручную в течение 1 часа.\n\n"
        "📌 Если у тебя нет ID, напиши @userinfobot — он покажет."
    )

@dp.message(lambda m: m.text == "🌟 Мотивация")
async def send_motivation(message: types.Message):
    text, author = get_random_quote()
    await message.answer(f"🌟 {text}\n— {author}")

@dp.message(Command("confirm"))
async def confirm_payment(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав.")
        return
    try:
        user_id = int(message.text.split()[1])
        set_subscription(user_id)
        await message.answer(f"✅ Подписка для пользователя {user_id} активирована на 30 дней.")
    except:
        await message.answer("⚠️ Используй: /confirm 123456789")

@dp.message(Command("addquote"))
async def add_quote(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав.")
        return
    try:
        parts = message.text.split('/addquote', 1)[1].strip().split('|')
        if len(parts) == 2:
            text, author = parts[0].strip(), parts[1].strip()
            conn = sqlite3.connect('user_data.db')
            c = conn.cursor()
            c.execute("INSERT INTO quotes (text, author) VALUES (?, ?)", (text, author))
            conn.commit()
            conn.close()
            await message.answer("✅ Фраза добавлена!")
        else:
            await message.answer("⚠️ Используй: /addquote Текст | Автор")
    except:
        await message.answer("⚠️ Ошибка. Пример: /addquote Успех любит смелых | Ницше")

@dp.message(Command("settime"))
async def set_time(message: types.Message):
    if not is_subscribed(message.from_user.id):
        await message.answer("⛔ Только для подписчиков.")
        return
    try:
        hour = int(message.text.split()[1])
        if 0 <= hour <= 23:
            set_moti_hour(message.from_user.id, hour)
            await message.answer(f"✅ Время рассылки изменено на {hour}:00")
        else:
            await message.answer("⚠️ Введите час от 0 до 23")
    except:
        await message.answer("⚠️ Используй: /settime 8")

async def check_subscription(message: types.Message):
    if not is_subscribed(message.from_user.id):
        await message.answer(
            "⛔ Эта функция доступна только подписчикам.\n"
            "Оформи подписку за 125 ₽ через кнопку '💳 Подписка'.",
            reply_markup=main_kb
        )
        return False
    return True

@dp.message(lambda m: m.text == "📋 Мой план")
async def show_plan(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    active, done = get_tasks(user_id)
    text = "📋 ТВОЙ ПЛАН:\n\n"
    if active:
        for task in active:
            text += f"⬜ {task[1]} (id:{task[0]})\n"
    else:
        text += "Нет активных задач.\n"
    inline_kb = InlineKeyboardMarkup()
    for task in active:
        inline_kb.add(
            InlineKeyboardButton(f"✅ {task[1][:15]}", callback_data=f"done_{task[0]}"),
            InlineKeyboardButton("❌", callback_data=f"del_{task[0]}")
        )
    if done:
        text += "\n📌 Недавно выполненные:\n"
        for t in done[:5]:
            text += f"✅ {t[1]}\n"
    await message.answer(text, reply_markup=inline_kb if inline_kb.inline_keyboard else None)

@dp.callback_query(lambda c: c.data.startswith("done_"))
async def callback_done(call: types.CallbackQuery):
    if not is_subscribed(call.from_user.id):
        await call.answer("Нужна подписка", show_alert=True)
        return
    task_id = int(call.data.split("_")[1])
    mark_done(call.from_user.id, task_id)
    await call.answer("✅ Выполнено!", show_alert=False)
    await call.message.edit_reply_markup(reply_markup=None)

@dp.callback_query(lambda c: c.data.startswith("del_"))
async def callback_del(call: types.CallbackQuery):
    if not is_subscribed(call.from_user.id):
        await call.answer("Нужна подписка", show_alert=True)
        return
    task_id = int(call.data.split("_")[1])
    delete_task(call.from_user.id, task_id)
    await call.answer("🗑️ Удалено", show_alert=False)
    await call.message.edit_reply_markup(reply_markup=None)

@dp.message(lambda m: m.text == "➕ Добавить задачу")
async def add_task_prompt(message: types.Message):
    if not await check_subscription(message): return
    await message.answer("✏️ Напиши текст задачи (можно с категорией через ' / ').")

@dp.message(lambda m: m.text and m.text not in ["📋 Мой план", "➕ Добавить задачу", "🍽️ Добавить еду", "💧 Вода", "🏋️ Тренировка", "📊 Статистика", "🌟 Мотивация", "💳 Подписка", "😴 Сон", "📅 Цели недели", "🚫 Воздержание", "⚙️ Настройки"])
async def handle_text(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    text = message.text.strip()
    if " / " in text:
        category, task = text.split(" / ", 1)
    else:
        category, task = "Общее", text
    add_task(user_id, task, category)
    await message.answer(f"✅ Задача '{task}' добавлена в категорию '{category}'!")

@dp.message(lambda m: m.text == "🍽️ Добавить еду")
async def add_meal_prompt(message: types.Message):
    if not await check_subscription(message): return
    await message.answer("🍽️ Введи: Название, калории, белки, жиры, углеводы\nПример: Гречка, 400, 20, 10, 45")

@dp.message(lambda m: m.text and m.text not in ["📋 Мой план", "➕ Добавить задачу", "🍽️ Добавить еду", "💧 Вода", "🏋️ Тренировка", "📊 Статистика", "🌟 Мотивация", "💳 Подписка", "😴 Сон", "📅 Цели недели", "🚫 Воздержание", "⚙️ Настройки"])
async def handle_meal_or_workout(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    try:
        parts = message.text.split(',')
        if len(parts) >= 2:
            name = parts[0].strip()
            calories = int(parts[1].strip())
            protein = float(parts[2]) if len(parts) > 2 else 0
            fat = float(parts[3]) if len(parts) > 3 else 0
            carbs = float(parts[4]) if len(parts) > 4 else 0
            add_meal(user_id, name, calories, protein, fat, carbs)
            await message.answer(f"✅ Записано: {name} ({calories} ккал, б:{protein} ж:{fat} у:{carbs})")
            return
    except:
        pass
    duration = 30
    add_workout(user_id, message.text, duration)
    await message.answer(f"🏋️ Тренировка '{message.text}' засчитана (30 мин)!")

@dp.message(lambda m: m.text == "💧 Вода")
async def water_menu(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    today = get_today_water(user_id)
    norm = get_water_norm(user_id)
    await message.answer(
        f"💧 Вода сегодня: {today} мл из {norm} мл ({int(today/norm*100)}%)\n"
        "Напиши количество выпитой воды в мл (например: 250)"
    )

@dp.message(lambda m: m.text and m.text.isdigit() and int(m.text) > 0)
async def handle_water(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    amount = int(message.text)
    add_water(user_id, amount)
    today = get_today_water(user_id)
    norm = get_water_norm(user_id)
    await message.answer(f"✅ Добавлено {amount} мл. Всего сегодня: {today} мл из {norm} мл")

@dp.message(lambda m: m.text == "🏋️ Тренировка")
async def workout_prompt(message: types.Message):
    if not await check_subscription(message): return
    await message.answer("🏋️ Напиши тип тренировки (например: Турники, Силовая).")

@dp.message(lambda m: m.text == "😴 Сон")
async def sleep_menu(message: types.Message):
    if not await check_subscription(message): return
    await message.answer("😴 Сколько часов ты спал прошлой ночью?\nНапиши число (например: 7.5)")

@dp.message(lambda m: m.text and m.text.replace('.','',1).isdigit() and float(m.text) > 0)
async def handle_sleep(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    hours = float(message.text)
    if hours > 12:
        await message.answer("⚠️ Слишком много часов, проверь ввод.")
        return
    add_sleep(user_id, hours)
    await message.answer(f"✅ Сон записан: {hours} ч. +5 опыта!")

@dp.message(lambda m: m.text == "📅 Цели недели")
async def weekly_goals_menu(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    goals = get_weekly_goals(user_id)
    if not goals:
        await message.answer("📅 У тебя пока нет целей на эту неделю.\nНапиши первую цель (например: 'Прочитать книгу')")
        return
    text = "📅 ЦЕЛИ НА ЭТУ НЕДЕЛЮ:\n\n"
    inline_kb = InlineKeyboardMarkup()
    for goal in goals:
        status = "✅" if goal[2] else "⬜"
        text += f"{status} {goal[1]}\n"
        if not goal[2]:
            inline_kb.add(InlineKeyboardButton(f"✅ {goal[1][:15]}", callback_data=f"goal_done_{goal[0]}"))
            inline_kb.add(InlineKeyboardButton("❌", callback_data=f"goal_del_{goal[0]}"))
    await message.answer(text, reply_markup=inline_kb if inline_kb.inline_keyboard else None)

@dp.callback_query(lambda c: c.data.startswith("goal_done_"))
async def goal_done(call: types.CallbackQuery):
    if not is_subscribed(call.from_user.id):
        await call.answer("Нужна подписка", show_alert=True)
        return
    goal_id = int(call.data.split("_")[2])
    mark_weekly_goal_done(call.from_user.id, goal_id)
    await call.answer("✅ Цель выполнена!", show_alert=False)
    await call.message.edit_reply_markup(reply_markup=None)

@dp.callback_query(lambda c: c.data.startswith("goal_del_"))
async def goal_del(call: types.CallbackQuery):
    if not is_subscribed(call.from_user.id):
        await call.answer("Нужна подписка", show_alert=True)
        return
    goal_id = int(call.data.split("_")[2])
    delete_weekly_goal(call.from_user.id, goal_id)
    await call.answer("🗑️ Удалено", show_alert=False)
    await call.message.edit_reply_markup(reply_markup=None)

@dp.message(lambda m: m.text == "📊 Статистика")
async def show_stats(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    active, done = get_tasks(user_id)
    meals = get_today_meals(user_id)
    water = get_today_water(user_id)
    norm = get_water_norm(user_id)
    w_count = get_today_workout_count(user_id)
    level, exp = get_user_data(user_id)[:2]
    week_tasks, week_workouts, week_water, week_cal, avg_sleep = get_week_stats(user_id)
    stats = (
        f"📊 СТАТИСТИКА ЗА СЕГОДНЯ:\n\n"
        f"👤 Уровень: {level} (опыт: {exp}/100)\n"
        f"📝 Активных задач: {len(active)}, выполнено сегодня: {len(done)}\n"
        f"🍽️ Калории: {sum(m[1] for m in meals)} ккал\n"
        f"💧 Вода: {water} мл из {norm} мл ({int(water/norm*100)}%)\n"
        f"🏋️ Тренировок: {w_count}\n\n"
        f"📈 ЗА НЕДЕЛЮ:\n"
        f"✅ Задач выполнено: {week_tasks}\n"
        f"🏋️ Тренировок: {week_workouts}\n"
        f"💧 Воды: {week_water} мл\n"
        f"🍽️ Калорий: {week_cal} ккал\n"
        f"😴 Средний сон: {avg_sleep:.1f} ч"
    )
    if meals:
        stats += "\n\n🍲 Детально за сегодня:\n" + "\n".join(f"• {m[0]} – {m[1]} ккал (б:{m[2]} ж:{m[3]} у:{m[4]})" for m in meals)
    await message.answer(stats)

# ================== ХЕНДЛЕРЫ NOFAP ==================
@dp.message(lambda m: m.text == "🚫 Воздержание")
async def nofap_menu(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    data = get_nofap_data(user_id)
    if not data:
        init_nofap(user_id)
        data = get_nofap_data(user_id)
    start_date, last_checkin, streak, longest, total, last_reset = data
    today = datetime.now().date()
    last_checkin_date = datetime.fromisoformat(last_checkin).date()
    if last_checkin_date < today:
        # Не проверяем, пропущен ли день, чтобы пользователь сам мог отметить
        pass
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Моя статистика воздержания")],
            [KeyboardButton(text="✅ Отметить день")],
            [KeyboardButton(text="❌ Сброс (срыв)")],
            [KeyboardButton(text="💪 Мотивация")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer("🚫 МЕНЮ ВОЗДЕРЖАНИЯ\n\nВыбери действие:", reply_markup=kb)

@dp.message(lambda m: m.text == "📊 Моя статистика воздержания")
async def nofap_stats(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    data = get_nofap_data(user_id)
    if not data:
        init_nofap(user_id)
        data = get_nofap_data(user_id)
    start_date, last_checkin, streak, longest, total, last_reset = data
    today = datetime.now().date()
    last_checkin_date = datetime.fromisoformat(last_checkin).date()
    days_since_last = (today - last_checkin_date).days
    if streak == 0 and total == 0:
        await message.answer("📊 Ты ещё не начал отсчёт. Нажми '✅ Отметить день', чтобы начать.")
        return
    text = f"📊 СТАТИСТИКА ВОЗДЕРЖАНИЯ:\n\n"
    text += f"🔥 Текущий стрик: {streak} дней\n"
    text += f"🏆 Лучший стрик: {longest} дней\n"
    text += f"📅 Всего дней: {total}\n"
    text += f"📆 Последняя отметка: {last_checkin_date.strftime('%d.%m.%Y')} (прошло {days_since_last} дн.)\n"
    if streak > 0:
        text += f"\n💪 Ты держишься уже {streak} дней! Так держать!"
    else:
        text += f"\n🔄 Ты сбросил стрик. Не сдавайся, начинай заново!"
    await message.answer(text)

@dp.message(lambda m: m.text == "✅ Отметить день")
async def nofap_checkin(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    success, streak, longest, total = checkin_nofap(user_id)
    if success:
        moto = get_nofap_motivation()
        await message.answer(f"✅ Отлично! Ты отметил день! Твой стрик: {streak} дн.\n\n{moto}")
        if streak % 7 == 0 and streak > 0:
            await message.answer(f"🎉 Поздравляю! Ты достиг {streak} дней! Это огромный прогресс!")
    else:
        await message.answer("⚠️ Ты уже отмечал сегодняшний день. Приходи завтра!")

@dp.message(lambda m: m.text == "❌ Сброс (срыв)")
async def nofap_reset(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    # Запрос подтверждения
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Да, сбросить", callback_data="confirm_reset"))
    kb.add(InlineKeyboardButton("Нет, отмена", callback_data="cancel_reset"))
    await message.answer("❌ Ты уверен, что хочешь сбросить стрик? Это действие необратимо.", reply_markup=kb)

@dp.callback_query(lambda c: c.data == "confirm_reset")
async def confirm_reset(call: types.CallbackQuery):
    if not is_subscribed(call.from_user.id):
        await call.answer("Нужна подписка", show_alert=True)
        return
    user_id = call.from_user.id
    longest = reset_nofap(user_id)
    await call.answer("Сброс выполнен", show_alert=False)
    await call.message.edit_text(f"❌ Стрик сброшен. Твой лучший результат: {longest} дней. Начинай новый путь!")

@dp.callback_query(lambda c: c.data == "cancel_reset")
async def cancel_reset(call: types.CallbackQuery):
    await call.answer("Отмена", show_alert=False)
    await call.message.edit_text("✅ Сброс отменён. Продолжай держаться!")

@dp.message(lambda m: m.text == "💪 Мотивация")
async def nofap_motivation(message: types.Message):
    if not await check_subscription(message): return
    moto = get_nofap_motivation()
    await message.answer(f"💪 {moto}")

@dp.message(lambda m: m.text == "🔙 Назад")
async def back_to_main(message: types.Message):
    await message.answer("🔙 Возврат в главное меню.", reply_markup=main_kb)

# --- НАСТРОЙКИ ---
@dp.message(lambda m: m.text == "⚙️ Настройки")
async def settings_menu(message: types.Message):
    if not await check_subscription(message): return
    user_id = message.from_user.id
    norm = get_water_norm(user_id)
    hour = get_moti_hour(user_id)
    await message.answer(
        f"⚙️ НАСТРОЙКИ:\n"
        f"💧 Норма воды: {norm} мл (изменить: вода 3000)\n"
        f"⏰ Час мотивации: {hour}:00 (изменить: /settime 8)"
    )

@dp.message(lambda m: m.text and m.text.startswith("вода"))
async def change_water_norm(message: types.Message):
    if not await check_subscription(message): return
    try:
        norm = int(message.text.split()[1])
        if norm >= 1000:
            set_water_norm(message.from_user.id, norm)
            await message.answer(f"✅ Норма воды: {norm} мл")
        else:
            await message.answer("⚠️ Норма должна быть не менее 1000 мл.")
    except:
        await message.answer("⚠️ Пример: вода 3000")

# --- РАССЫЛКИ ---
async def daily_motivation():
    for user_id, sub_end in get_all_users():
        if sub_end and datetime.fromisoformat(sub_end) > datetime.now():
            text, author = get_random_quote()
            try:
                await bot.send_message(user_id, f"🌅 ДОБРОЕ УТРО!\n\n🌟 {text}\n— {author}\n\nУдачи в новом дне! 💪")
            except:
                pass

scheduler.add_job(daily_motivation, CronTrigger(hour=7, minute=0))

async def water_reminder():
    for user_id, sub_end in get_all_users():
        if sub_end and datetime.fromisoformat(sub_end) > datetime.now():
            try:
                await bot.send_message(user_id, "💧 Напоминание: выпей стакан воды! Это поможет держать кожу чистой и тонус.")
            except:
                pass

scheduler.add_job(water_reminder, IntervalTrigger(hours=2))

async def cleanup_old_tasks():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    c.execute("DELETE FROM tasks WHERE done=1 AND done_at < ?", (week_ago,))
    conn.commit()
    conn.close()

scheduler.add_job(cleanup_old_tasks, CronTrigger(hour=3, minute=0))

async def cleanup_weekly_goals():
    cleanup_old_weekly_goals()

scheduler.add_job(cleanup_weekly_goals, CronTrigger(day_of_week='sun', hour=23, minute=59))

scheduler.start()

# --- ЗАПУСК ---
if __name__ == "__main__":
    print("🚀 Бот 520 System с системой воздержания запущен!")
    dp.run_polling(bot)
