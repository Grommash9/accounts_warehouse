import asyncio
import collections
import os
import logging
from functools import wraps
import aiogram
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import config
import data_base_sender
import db_api
import keyboards

bot = Bot(token=config.bot_token)
logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
loop = asyncio.get_event_loop()
dp = Dispatcher(bot, storage=storage, loop=loop)


def restricted(func):
    @wraps(func)
    def wrapped(message, *args, **kwargs):
        user_id = message.from_user.id
        if user_id not in config.users_list:
            raise TypeError(f'{message.from_user.id} user are not in the list - config.users_list')
        return func(message, *args, **kwargs)
    return wrapped


class Form(StatesGroup):
    new_category_name = State()
    user_file_name = State()
    accounts_count = State()
    target_category_name = State()


@dp.message_handler(commands=['start'])
@restricted
async def process_start_command(message: types.Message):
    await bot.send_message(chat_id=message.from_user.id, text='hi', reply_markup=keyboards.default_reply_keyboard())


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('add'))
async def data_entering(callback_query: types.CallbackQuery):
    adding_data = callback_query.data.split('_')

    file_name = adding_data[2]
    category_name = adding_data[1]

    unique_accounts_list, duplicate_accounts_list = [], []
    all_accounts_data = []
    for accounts in db_api.get_all_accounts():
        all_accounts_data.append(accounts[1])
    with open(f"{config.files_path}/{file_name}.txt", 'r') as data_file:
        for line in data_file:
            if line.endswith('\n'):
                clean_line = line[:-1]
            else:
                clean_line = line
            if clean_line in all_accounts_data:
                duplicate_accounts_list.append(line)
            else:
                db_api.add_accounts(account_data=clean_line, category_name=category_name)
                unique_accounts_list.append(line)
    try:
        os.remove(f"{config.files_path}/{file_name}.txt")
    except FileNotFoundError:
        pass
    await bot.answer_callback_query(callback_query_id=callback_query.id)
    if len(unique_accounts_list) > 0:
        with open(f"{config.files_path}/{file_name}_unique.txt", 'a') as file_to_save_unique:
            for accounts in unique_accounts_list:
                file_to_save_unique.write(f"{accounts}\n")
        await bot.send_document(document=open(f"{config.files_path}/{file_name}_unique.txt", 'rb'),
                                chat_id=callback_query.from_user.id)
        try:
            os.remove(f"{config.files_path}/{file_name}_unique.txt")
        except FileNotFoundError:
            pass

    if len(duplicate_accounts_list) > 0:
        with open(f"{config.files_path}/{file_name}_duplicate.txt", 'a') as file_to_save_duplicate:
            for accounts in duplicate_accounts_list:
                file_to_save_duplicate.write(f"{accounts}\n")
        await bot.send_document(document=open(f"{config.files_path}/{file_name}_duplicate.txt", 'rb'),
                                chat_id=callback_query.from_user.id)
        try:
            os.remove(f"{config.files_path}/{file_name}_duplicate.txt")
        except FileNotFoundError:
            pass

    await bot.send_message(chat_id=callback_query.from_user.id, text='You have:\n\n'
                                                                     f'{len(unique_accounts_list)} unique accounts uploaded to database\n\n'
                                                                     f'{len(duplicate_accounts_list)} duplicate accounts')


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('new'), state='*')
async def category_creation(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['users_file_name'] = callback_query.data.split('_')[1]
    await Form.new_category_name.set()
    await bot.send_message(chat_id=callback_query.from_user.id, text='Please enter new category name (english please)\n\n'
                                                                     'For cancel please use /cancel')
    await bot.answer_callback_query(callback_query_id=callback_query.id)


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):

    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)

    await state.finish()
    await bot.send_message(chat_id=message.from_user.id, text='You are canceled the operation')


@dp.message_handler(state=Form.new_category_name)
async def category_name_getter(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['new_category_name'] = message.text
    await state.finish()
    await bot.send_message(chat_id=message.from_user.id, text='Please press yes for add, or just ignore to cancel',
                           reply_markup=keyboards.done_adding_category(category_name=data['new_category_name'],
                                                                       file_data=data['users_file_name']))


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('page'))
async def upload_page_changer(callback_query: types.CallbackQuery):
    callback_data = callback_query.data.split('_')
    await bot.send_message(chat_id=callback_query.from_user.id, text=f'File will have id {callback_data[1]}\n\nPlease choose the category:', reply_markup=keyboards.file_upload_categories_keyboard(file_data=callback_data[1], start_step=int(callback_data[2]), end_step=int(callback_data[3])))
    await bot.answer_callback_query(callback_query_id=callback_query.id)


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def file_handle(message: types.Document):
    files_names = [0]
    for files in os.listdir(config.files_path):
        try:
            files_names.append(int(files.split('.txt')[0]))
        except ValueError:
            pass
    new_file_name = str(max(files_names) + 1)

    file = await bot.get_file(file_id=message.document.file_id)
    await bot.download_file(file_path=file.file_path, destination=f"{config.files_path}/{new_file_name}.txt")
    await message.answer(text=f'File will have id {new_file_name}\n\nPlease choose the category:',
                         reply_markup=keyboards.file_upload_categories_keyboard(new_file_name))


@dp.message_handler(aiogram.dispatcher.filters.Text(equals='Count'))
@restricted
async def count_button_callback(message: types.Message):
    categories_dict = dict()
    for accounts in db_api.get_all_accounts():
        if accounts[2] == 0:
            if accounts[3] in categories_dict.keys():
                categories_dict[accounts[3]] += 1
            else:
                categories_dict[accounts[3]] = 1
    sorted_category_tuple = collections.Counter(categories_dict).most_common()
    final_text = ''
    for categories in sorted_category_tuple:
        final_text += f"{categories[0]} - {categories[1]}\n"
    await bot.send_message(chat_id=message.from_user.id, text='Here is the quantity data:\n\n'
                                                              f'{final_text}')


@dp.message_handler(aiogram.dispatcher.filters.Text(equals='Download'))
@restricted
async def download_callback(message: types.Message):
    await bot.send_message(chat_id=message.from_user.id, text='Please choose the category for download:', reply_markup=keyboards.download_keyboard_generator())


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('dpage'))
async def download_menu_page_selector(callback_query: types.CallbackQuery):
    callback_data = callback_query.data.split('_')
    await bot.send_message(chat_id=callback_query.from_user.id, text=f'Please choose the category for download:', reply_markup=keyboards.download_keyboard_generator(start_step=int(callback_data[1]), end_step=int(callback_data[2])))
    await bot.answer_callback_query(callback_query_id=callback_query.id)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('get'), state='*')
async def category_creation(callback_query: types.CallbackQuery, state: FSMContext):
    target_category_name = callback_query.data.split('_')[1]
    async with state.proxy() as data:
        data['target_category_name'] = target_category_name
    await bot.send_message(chat_id=callback_query.from_user.id, text=f'Please enter how much {target_category_name} you want download\n\n'
                                                                     f'for cancel use /cancel command')
    await Form.accounts_count.set()
    await bot.answer_callback_query(callback_query_id=callback_query.id)


@dp.message_handler(state=Form.accounts_count)
async def category_name_getter(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['accounts_count'] = message.text
    await state.finish()
    accounts_download_list = []
    for accounts in db_api.get_all_accounts():
        if accounts[2] == 0 and accounts[3] == data['target_category_name']:
            if len(accounts_download_list) < int(data['accounts_count']):
                accounts_download_list.append(accounts[1])
                db_api.update_accounts(id=accounts[0], is_downloaded=1)
            else:
                break
    final_accounts_text_list = ''
    for account in accounts_download_list:
        final_accounts_text_list += f"{account}\n"
    await bot.send_message(chat_id=message.from_user.id, text=f"Here is your {data['target_category_name']} accounts:\n\n"
                                                                     f'{final_accounts_text_list}')


if __name__ == '__main__':
    dp.loop.create_task(data_base_sender.data_base_sender())
    executor.start_polling(dp)
