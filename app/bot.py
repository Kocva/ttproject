from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, ConversationHandler
import requests


API_BASE_URL = 'http://127.0.0.1:5000/api'  # Укажите корректный адрес API
TOKEN = '7506782496:AAFa49IjW1q3wrO1e5L4QGmDpgVILI3vvq0'  # Укажите токен бота
LOGIN_URL = f"{API_BASE_URL}/login"
session = requests.Session()
login_payload = {
    "username": "bot",
    "password": "bot"
}
response = session.post(LOGIN_URL, data=login_payload)

if response.status_code == 200:
    print("✅ Бот успешно авторизован!")

data = {"username": "bot", "password": "bot"}
headers = {"Content-Type": "application/json"}

response = requests.post(LOGIN_URL, json=data, headers=headers)
print(response.status_code, response.text)

AUTHORIZED_USERS = {}  # Храним авторизованных сотрудников
CLIENTS = {}  # Храним привязанных клиентов
TITLE, DESCRIPTION, SELECT_CLIENT, SELECT_PLACE = range(4)

def get_main_menu():
    return ReplyKeyboardMarkup([ 
        ['Создать заявку', 'Просмотреть заявки']
    ], resize_keyboard=True)


async def link_telegram_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Использование: /link_account <client_id>")
        return

    client_id = context.args[0]
    telegram_id = update.message.chat.id

    # Отправка данных на API для привязки аккаунта
    response = requests.post(f'{API_BASE_URL}/link_telegram_account', json={
        'telegram_id': telegram_id,
        'client_id': client_id
    })

    if response.status_code == 200:
        await update.message.reply_text("Ваш аккаунт успешно привязан.")
    else:
        await update.message.reply_text("Ошибка при привязке аккаунта.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    # Проверяем, является ли этот пользователь клиентом или сотрудником
    client = requests.get(f'{API_BASE_URL}/client_by_telegram/{telegram_id}')
    employee = requests.get(f'{API_BASE_URL}/employee_by_telegram/{telegram_id}')
    
    if client.status_code == 200:
        client_data = client.json()
        context.user_data['client_id'] = client_data.get('client_id')
        await update.message.reply_text(
            f"Привет Вы авторизованы как клиент.\n"
            "Для создания заявки выберите опцию ниже.",
            reply_markup=get_main_menu()
        )
    elif employee.status_code == 200:
        employee_data = employee.json()
        context.user_data['employee_id'] = employee_data.get('employee_id')
        await update.message.reply_text(
            f"Привет! Вы авторизованы как сотрудник.\n"
            "Для создания заявки выберите опцию ниже.",
            reply_markup=get_main_menu()
        )
    else:
        await update.message.reply_text(
            "Извините, вы не привязаны к системе. Пожалуйста, привяжите ваш аккаунт через сайт."
        )

# Функция для обработки изменения статуса через кнопки
async def set_ticket_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, ticket_id, new_status = query.data.split('_')
    response = requests.patch(f'{API_BASE_URL}/tickets/{ticket_id}', json={'status': new_status})

    if response.status_code == 200:
        await query.message.reply_text(f"Статус заявки {ticket_id} изменен на {new_status}.")
    else:
        await query.message.reply_text("Ошибка при изменении статуса. Попробуйте снова позже.")


# Функция для изменения статуса заявки
async def change_ticket_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ticket_id = int(query.data.split('_')[2])
    statuses = ['новая', 'в процессе', 'завершенная', 'на рассмотрении']

    keyboard = [[InlineKeyboardButton(status, callback_data=f"status_{ticket_id}_{status}")] for status in statuses]
    await query.message.reply_text(f"Выберите новый статус для заявки {ticket_id}:", reply_markup=InlineKeyboardMarkup(keyboard))


async def change_ticket_status_by_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Проверяем, соответствует ли формат команды
    if text.lower().startswith("заявка") and "статус" in text.lower():
        parts = text.split()

        if len(parts) == 4:
            try:
                ticket_id = int(parts[1])  # Извлекаем ID заявки
                new_status = parts[3].lower()  # Извлекаем новый статус

                # Проверяем, что статус правильный
                valid_statuses = ['новая', 'в процессе', 'завершена', 'на рассмотрении']
                if new_status not in valid_statuses:
                    await update.message.reply_text(f"Неверный статус! Доступные статусы: {', '.join(valid_statuses)}.")
                    return

                # Отправляем запрос для изменения статуса
                response = requests.patch(f'{API_BASE_URL}/tickets/{ticket_id}', json={'status': new_status})

                if response.status_code == 200:
                    await update.message.reply_text(f"Статус заявки {ticket_id} изменен на {new_status}.")
                else:
                    await update.message.reply_text("Ошибка при изменении статуса. Попробуйте снова позже.")
            except ValueError:
                await update.message.reply_text("Неверный формат команды. Используйте: 'заявка <id> статус <статус>'.")
        else:
            await update.message.reply_text("Неверный формат команды. Используйте: 'заявка <id> статус <статус>'.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=get_main_menu())
    return ConversationHandler.END

async def create_ticket_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверка на авторизацию
    if 'client_id' not in context.user_data and 'employee_id' not in context.user_data:
        await update.message.reply_text("Пожалуйста, выполните авторизацию с помощью /start.")
        return

    await update.message.reply_text("Введите название заявки:", reply_markup=ReplyKeyboardRemove())
    return TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Введите описание заявки:")
    return DESCRIPTION

def get_places(client_id=None):
    if client_id:
        response = requests.get(f'{API_BASE_URL}/places/{client_id}')  # Получаем точки продаж для конкретного клиента
    else:
        response = requests.get(f'{API_BASE_URL}/places')  # Получаем все точки продаж
    if response.status_code == 200:
        return response.json()  # Возвращаем список точек продаж
    return []

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text

    # Если это клиент, показываем ему выбор точки продаж
    if 'client_id' in context.user_data:
        places = get_places(context.user_data['client_id'])  # Получаем точки продаж этого клиента
        if places:
            keyboard = [[InlineKeyboardButton(place['address'], callback_data=f"place_{place['id']}")] for place in places]
            await update.message.reply_text("Выберите точку продаж:", reply_markup=InlineKeyboardMarkup(keyboard))
            return SELECT_PLACE
    else:
        # Если это сотрудник, показываем выбор клиента
        response = requests.get(f'{API_BASE_URL}/clients')
        if response.status_code == 200:
            clients = response.json()
            if clients:
                keyboard = [[InlineKeyboardButton(client['company_name'], callback_data=f"client_{client['id']}")] for client in clients]
                await update.message.reply_text("Выберите клиента:", reply_markup=InlineKeyboardMarkup(keyboard))
                return SELECT_CLIENT
            else:
                await update.message.reply_text("Клиенты отсутствуют.")
        else:
            await update.message.reply_text("Ошибка при получении списка клиентов.")
    return ConversationHandler.END

async def select_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    client_id = int(query.data.split('_')[1])
    context.user_data['client_id'] = client_id

    # После выбора клиента показываем выбор точки продаж
    places = get_places(client_id)
    if places:
        keyboard = [[InlineKeyboardButton(place['address'], callback_data=f"place_{place['id']}")] for place in places]
        await query.message.reply_text("Выберите точку продаж:", reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_PLACE
    else:
        await query.message.reply_text("Нет доступных точек продаж для этого клиента.")
        return ConversationHandler.END

async def select_place(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    place_id = int(query.data.split('_')[1])  # Получаем ID выбранной точки продаж
    context.user_data['place_id'] = place_id

    # Если это клиент, создаем заявку с привязкой к точке продаж
    if 'client_id' in context.user_data:
        client_id = context.user_data['client_id']
    else:
        client_id = None  # Сотрудник может выбрать любого клиента

    data = {
        'title': context.user_data['title'],
        'description': context.user_data['description'],
        'source': "Телеграм-бот",
        'employee_id': context.user_data['employee_id'] if 'employee_id' in context.user_data else 1,  # Если сотрудник
        'client_id': client_id,
        'place_id': place_id  # Добавляем ID точки продаж
    }

    response = requests.post(f'{API_BASE_URL}/tickets', json=data)
    if response.status_code == 201:
        ticket_id = response.json()['ticket_id']
        await query.message.reply_text(f"Заявка с ID {ticket_id} успешно создана.", reply_markup=get_main_menu())
    else:
        await query.message.reply_text("Ошибка при создании заявки.", reply_markup=get_main_menu())
    
    return ConversationHandler.END

async def view_tickets_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'client_id' in context.user_data:
        client_id = context.user_data['client_id']
        response = requests.get(f"{API_BASE_URL}/client/{client_id}/tickets")
        is_client = True
    elif 'employee_id' in context.user_data:
        response = requests.get(f"{API_BASE_URL}/tickets")
        is_client = False
    else:
        await update.message.reply_text("Пожалуйста, выполните авторизацию с помощью /start.")
        return

    if response.status_code == 200:
        tickets = response.json()
        if tickets:
            for ticket in tickets:
                message = f"ID: {ticket['id']}\nTitle: {ticket['title']}\nStatus: {ticket['status']}"
                
                keyboard = []
                if not is_client:  # Если пользователь не клиент, добавляем кнопку
                    keyboard.append([InlineKeyboardButton("Изменить статус", callback_data=f"change_status_{ticket['id']}")])
                
                reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                await update.message.reply_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text("Заявки отсутствуют.")
    else:
        await update.message.reply_text("Ошибка при получении заявок.")

# Для завершения диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=get_main_menu())
    return ConversationHandler.END


def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(set_ticket_status, pattern=r'^status_\d+_\w+'))
    application.add_handler(MessageHandler(filters.Regex(r'^заявка \d+ статус \w+$'), change_ticket_status_by_text))
    application.add_handler(CallbackQueryHandler(select_client, pattern=r'^client_'))
    application.add_handler(CallbackQueryHandler(select_place, pattern=r'^place_'))  # Обработчик выбора точки продаж
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Создать заявку$"), create_ticket_menu)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            SELECT_CLIENT: [CallbackQueryHandler(select_client, pattern=r'^client_')],
            SELECT_PLACE: [CallbackQueryHandler(select_place, pattern=r'^place_')]  # Новый шаг
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Regex("^Просмотреть заявки$"), view_tickets_menu))
    application.add_handler(CommandHandler("link_account", link_telegram_account))
    application.add_handler(CallbackQueryHandler(change_ticket_status, pattern=r'^change_status_\d+$'))
    application.run_polling()

if __name__ == '__main__':
    main()
