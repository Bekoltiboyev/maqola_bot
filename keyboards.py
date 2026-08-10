from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📤 Maqola yuborish")],
            [KeyboardButton(text="📄 Men yuborgan maqolalar")],
            [KeyboardButton(text="📊 Jurnallar soni")],
            [KeyboardButton(text="✉️ Axborot xati"), KeyboardButton(text="📑 Maqola namunasi")],
        ],
        resize_keyboard=True,
    )


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Yangi jurnal ochish", callback_data="admin_new_journal")],
            [InlineKeyboardButton(text="✉️ Axborot xatini yuklash", callback_data="admin_upload_info")],
            [InlineKeyboardButton(text="📑 Maqola namunasini yuklash", callback_data="admin_upload_sample")],
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        ]
    )
