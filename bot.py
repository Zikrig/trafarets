import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import BOT_TOKEN, ADMIN_ID, PDF_FOLDER, DATA_FOLDER

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Состояния FSM
class AdminStates(StatesGroup):
    editing_welcome = State()
    editing_contact = State()
    editing_templates = State()
    adding_pdf = State()
    deleting_pdf = State()

def read_text_file(filename):
    try:
        with open(os.path.join(DATA_FOLDER, filename), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Файл {filename} не найден"

def write_text_file(filename, content):
    with open(os.path.join(DATA_FOLDER, filename), 'w', encoding='utf-8') as f:
        f.write(content)

def get_pdf_files():
    return [f for f in os.listdir(PDF_FOLDER) if f.endswith('.pdf')]

def create_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Связь с админом", callback_data="contact")],
        [InlineKeyboardButton(text="📄 Шаблоны", callback_data="templates")]
    ])

def create_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить приветствие", callback_data="edit_welcome")],
        [InlineKeyboardButton(text="✏️ Изменить контакты", callback_data="edit_contact")],
        [InlineKeyboardButton(text="✏️ Изменить описание шаблонов", callback_data="edit_templates")],
        [InlineKeyboardButton(text="📤 Добавить PDF", callback_data="add_pdf")],
        [InlineKeyboardButton(text="🗑️ Удалить PDF", callback_data="delete_pdf")],
        [InlineKeyboardButton(text="❌ Закрыть админ-панель", callback_data="close_admin")]
    ])

def create_pdf_delete_keyboard():
    files = get_pdf_files()
    keyboard = []
    for file in files:
        keyboard.append([InlineKeyboardButton(text=f"🗑️ {file}", callback_data=f"delete_{file}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = read_text_file("welcome.txt")
    await message.answer(welcome_text, reply_markup=create_main_keyboard())

@dp.message(Command("admin"))
async def admin_handler(message: types.Message):
    if str(message.from_user.id) not in ADMIN_ID:
        await message.answer("У вас нет прав администратора")
        return
    
    await message.answer("Админ-панель:", reply_markup=create_admin_keyboard())

@dp.callback_query(F.data == "contact")
async def contact_handler(callback: types.CallbackQuery):
    contact_text = read_text_file("contact.txt")
    await callback.message.answer(contact_text)
    await callback.answer()

@dp.callback_query(F.data == "templates")
async def templates_handler(callback: types.CallbackQuery):
    templates_text = read_text_file("templates.txt")
    files = get_pdf_files()
    
    if not files:
        await callback.message.answer("Шаблоны временно недоступны")
        return
    
    await callback.message.answer(templates_text)
    
    for file in files:
        file_path = os.path.join(PDF_FOLDER, file)
        await callback.message.answer_document(
            FSInputFile(file_path),
            caption=f"📄 {file}"
        )
    await callback.answer()

# Обработчики админ-панели
@dp.callback_query(F.data == "edit_welcome")
async def edit_welcome_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите новый текст приветствия:")
    await state.set_state(AdminStates.editing_welcome)
    await callback.answer()

@dp.callback_query(F.data == "edit_contact")
async def edit_contact_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите новый текст контактов:")
    await state.set_state(AdminStates.editing_contact)
    await callback.answer()

@dp.callback_query(F.data == "edit_templates")
async def edit_templates_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите новое описание шаблонов:")
    await state.set_state(AdminStates.editing_templates)
    await callback.answer()

@dp.callback_query(F.data == "add_pdf")
async def add_pdf_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте PDF-файл для добавления:")
    await state.set_state(AdminStates.adding_pdf)
    await callback.answer()

@dp.callback_query(F.data == "delete_pdf")
async def delete_pdf_handler(callback: types.CallbackQuery):
    files = get_pdf_files()
    if not files:
        await callback.message.answer("Нет файлов для удаления")
        return
    
    await callback.message.answer("Выберите файл для удаления:", reply_markup=create_pdf_delete_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("delete_"))
async def delete_specific_pdf_handler(callback: types.CallbackQuery):
    filename = callback.data.replace("delete_", "")
    file_path = os.path.join(PDF_FOLDER, filename)
    
    try:
        os.remove(file_path)
        await callback.message.answer(f"Файл {filename} успешно удален")
        await callback.message.edit_reply_markup(reply_markup=create_pdf_delete_keyboard())
    except Exception as e:
        await callback.message.answer(f"Ошибка при удалении файла: {e}")
    
    await callback.answer()

@dp.callback_query(F.data == "back_to_admin")
async def back_to_admin_handler(callback: types.CallbackQuery):
    await callback.message.edit_text("Админ-панель:", reply_markup=create_admin_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "close_admin")
async def close_admin_handler(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer()

# Обработчики состояний FSM
@dp.message(AdminStates.editing_welcome)
async def process_edit_welcome(message: types.Message, state: FSMContext):
    write_text_file("welcome.txt", message.text)
    await message.answer("Приветственный текст обновлен!")
    await state.clear()

@dp.message(AdminStates.editing_contact)
async def process_edit_contact(message: types.Message, state: FSMContext):
    write_text_file("contact.txt", message.text)
    await message.answer("Текст контактов обновлен!")
    await state.clear()

@dp.message(AdminStates.editing_templates)
async def process_edit_templates(message: types.Message, state: FSMContext):
    write_text_file("templates.txt", message.text)
    await message.answer("Описание шаблонов обновлено!")
    await state.clear()

@dp.message(AdminStates.adding_pdf, F.document)
async def process_add_pdf(message: types.Message, state: FSMContext):
    if not message.document.mime_type == "application/pdf":
        await message.answer("Пожалуйста, отправьте PDF-файл")
        return
    
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    filename = message.document.file_name
    
    # Сохраняем файл
    destination = os.path.join(PDF_FOLDER, filename)
    await bot.download_file(file_path, destination)
    
    await message.answer(f"Файл {filename} успешно добавлен!")
    await state.clear()

if __name__ == "__main__":
    # Создаем необходимые папки, если их нет
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(PDF_FOLDER, exist_ok=True)
    
    # Создаем файлы по умолчанию, если их нет
    default_files = {
        "welcome.txt": "Добро пожаловать! 🎉\n\nЭто бот для работы с шаблонами документов.\n\nВыберите нужную опцию:",
        "contact.txt": "Связь с администратором: @username_admin\n\nПо всем вопросам обращайтесь напрямую!",
        "templates.txt": "Доступные шаблоны документов:"
    }
    
    for filename, content in default_files.items():
        if not os.path.exists(os.path.join(DATA_FOLDER, filename)):
            write_text_file(filename, content)
    
    dp.run_polling(bot)