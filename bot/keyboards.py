import collections

from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

import db_api


def file_upload_categories_keyboard(file_data, start_step=0, end_step=7):
    categories_dict = dict()
    for accounts in db_api.get_all_accounts():
        if accounts[2] == 0:
            if accounts[3] in categories_dict.keys():
                categories_dict[accounts[3]] += 1
            else:
                categories_dict[accounts[3]] = 1
    categories_set_keyboard_markup = InlineKeyboardMarkup()
    if len(categories_dict.keys()) > 7:
        sorted_category_tuple = collections.Counter(categories_dict).most_common()
        print(sorted_category_tuple)
        for categories in sorted_category_tuple[start_step:end_step]:
            new_category_button = InlineKeyboardButton(text=f"{categories[0]} - {categories[1]}",
                                                       callback_data=f'add_{categories[0]}_{file_data}')
            categories_set_keyboard_markup.add(new_category_button)
        add_new_category_button = InlineKeyboardButton(text='add new', callback_data=f"new_{file_data}")
        categories_set_keyboard_markup.add(add_new_category_button)
        if start_step - 7 >= 0:
            back_button = InlineKeyboardButton(text='back', callback_data=f"page_{file_data}_{start_step-7}_{end_step-7}")
            categories_set_keyboard_markup.add(back_button)
            next_button = InlineKeyboardButton(text='next',
                                               callback_data=f"page_{file_data}_{start_step + 7}_{end_step + 7}")
            categories_set_keyboard_markup.insert(next_button)
        else:
            next_button = InlineKeyboardButton(text='next',
                                               callback_data=f"page_{file_data}_{start_step + 7}_{end_step + 7}")
            categories_set_keyboard_markup.add(next_button)
        return categories_set_keyboard_markup

    else:
        for category, count in categories_dict.items():
            new_category_button = InlineKeyboardButton(text=f"{category} - {count}", callback_data=f'add_{category}_{file_data}')
            categories_set_keyboard_markup.add(new_category_button)
        add_new_category_button = InlineKeyboardButton(text='add new', callback_data=f"new_{file_data}")
        categories_set_keyboard_markup.add(add_new_category_button)
        return categories_set_keyboard_markup


def download_keyboard_generator(start_step=0, end_step=7):
    categories_dict = dict()
    for accounts in db_api.get_all_accounts():
        if accounts[2] == 0:
            if accounts[3] in categories_dict.keys():
                categories_dict[accounts[3]] += 1
            else:
                categories_dict[accounts[3]] = 1
    categories_set_keyboard_markup = InlineKeyboardMarkup()
    if len(categories_dict.keys()) > 7:
        sorted_category_tuple = collections.Counter(categories_dict).most_common()
        print(sorted_category_tuple)
        for categories in sorted_category_tuple[start_step:end_step]:
            new_category_button = InlineKeyboardButton(text=f"{categories[0]} - {categories[1]}",
                                                       callback_data=f'get_{categories[0]}')
            categories_set_keyboard_markup.add(new_category_button)
        if start_step - 7 >= 0:
            back_button = InlineKeyboardButton(text='back',
                                               callback_data=f"dpage_{start_step - 7}_{end_step - 7}")
            categories_set_keyboard_markup.add(back_button)
            next_button = InlineKeyboardButton(text='next',
                                               callback_data=f"dpage_{start_step + 7}_{end_step + 7}")
            categories_set_keyboard_markup.insert(next_button)
        else:
            next_button = InlineKeyboardButton(text='next',
                                               callback_data=f"dpage_{start_step + 7}_{end_step + 7}")
            categories_set_keyboard_markup.add(next_button)
        return categories_set_keyboard_markup
    else:
        for category, count in categories_dict.items():
            new_category_button = InlineKeyboardButton(text=f"{category} - {count}", callback_data=f'get_{category}')
            categories_set_keyboard_markup.add(new_category_button)
        return categories_set_keyboard_markup


def done_adding_category(category_name, file_data):
    done_adding_keyboard_markup = InlineKeyboardMarkup()
    yes = InlineKeyboardButton(text='yes, i want', callback_data=f'add_{category_name}_{file_data}')
    done_adding_keyboard_markup.add(yes)
    return done_adding_keyboard_markup


def default_reply_keyboard():
    default_reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    count_button = KeyboardButton(text='Count')
    download_button = KeyboardButton(text='Download')
    default_reply_keyboard.add(count_button)
    default_reply_keyboard.insert(download_button)
    return default_reply_keyboard