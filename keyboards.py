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
            [InlineKeyboardButton(text="📢 Majburiy kanallar", callback_data="admin_channels")],
            [InlineKeyboardButton(text="📨 Xabar yuborish (Barchaga)", callback_data="admin_broadcast")],
        ]
    )


def subscribe_keyboard(unjoined_channels) -> InlineKeyboardMarkup:
    """Foydalanuvchi hali qo'shilmagan kanal/guruhlar uchun tugmalar."""
    buttons = []
    for ch in unjoined_channels:
        title = ch["title"] or ch["chat_id"]
        buttons.append([InlineKeyboardButton(text=f"➕ {title}", url=ch["url"])])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def channels_manage_keyboard(channels) -> InlineKeyboardMarkup:
    """Admin uchun: mavjud kanallar ro'yxati (o'chirish tugmasi bilan) + qo'shish tugmasi."""
    buttons = []
    for ch in channels:
        title = ch["title"] or ch["chat_id"]
        buttons.append([InlineKeyboardButton(text=f"❌ {title}", callback_data=f"delch_{ch['id']}")])
    buttons.append([InlineKeyboardButton(text="➕ Yangi kanal qo'shish", callback_data="addch")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)