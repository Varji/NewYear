import logging
import random
import sqlite3
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = 'santa_bot.db'
admin_id = YOUR_ADMIN_ID_HERE

def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            details TEXT
        )
    ''')
    conn.commit()
    conn.close()

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Привет! Я бот для назначения Тайного Санты. Используйте команду /register, чтобы зарегистрироваться.")

def register(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_name = update.message.from_user.full_name

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM participants WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        update.message.reply_text("Вы уже зарегистрированы!")
        conn.close()
        return

    details = ' '.join(context.args) if context.args else 'Нет дополнительных данных.'
    cursor.execute("INSERT INTO participants (user_id, name, details) VALUES (?, ?, ?)", (user_id, user_name, details))
    conn.commit()
    conn.close()

    update.message.reply_text(f"Вы зарегистрированы как {user_name}. Ожидайте назначения Тайного Санты.")

def assign_santa(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != admin_id:
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM participants")
    participants = cursor.fetchall()
    conn.close()

    if len(participants) < 2:
        update.message.reply_text("Нужно как минимум 2 участника для назначения Тайного Санты!")
        return

    random.shuffle(participants)

    assignments = {}
    participants_copy = participants[:]

    for participant in participants:
        while True:
            santa = random.choice(participants_copy)
            if santa[1] != participant[1]:
                assignments[participant[1]] = santa[1]
                participants_copy.remove(santa)
                break

    for user_id, name, _ in participants:
        santa_name = assignments[name]
        context.bot.send_message(chat_id=user_id, text=f"Твой Тайный Санта: {santa_name}. Поделись подарком с ним!")

    update.message.reply_text("Тайные Санты назначены! Проверьте личные сообщения.")

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Доступные команды:\n/start - начать взаимодействие\n/register [имя] - зарегистрироваться\n/assign - назначить Тайного Санту (только для администратора)")

def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update {update} caused error {context.error}')

def main() -> None:
    create_db()
    updater = Updater("YOUR_TOKEN_HERE")
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("register", register))
    dispatcher.add_handler(CommandHandler("assign", assign_santa))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
