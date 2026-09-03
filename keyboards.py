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
            [InlineKeyboardButton(text="📋 Ko'rib chiqilmagan maqolalar", callback_data="admin_pending")],
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
    """Admin uchun: mavjud kanallar ro'yxati (yangilash/o'chirish tugmalari bilan) + qo'shish tugmasi."""
    buttons = []
    for ch in channels:
        title = ch["title"] or ch["chat_id"]
        buttons.append([
            InlineKeyboardButton(text=f"🔄 {title}", callback_data=f"refch_{ch['id']}"),
            InlineKeyboardButton(text="❌", callback_data=f"delch_{ch['id']}"),
        ])
    buttons.append([InlineKeyboardButton(text="➕ Yangi kanal qo'shish", callback_data="addch")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def review_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    """Har bir yangi maqolaostida chiqadigan Qabul qilindi / Rad etish tugmalari."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Qabul qilindi", callback_data=f"approve_{submission_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{submission_id}"),
            ]
        ]
    )


def reject_reason_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    """Rad etish sababini tanlash uchun tayyor variantlar menyusi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔸 Yengil tuzatish talab etiladi", callback_data=f"rreason_{submission_id}_r1")],
            [InlineKeyboardButton(text="🔸 Mustaqil ilmiy hissa yetarli emas", callback_data=f"rreason_{submission_id}_r2")],
            [InlineKeyboardButton(text="🔸 Tanlov shartiga mos emas", callback_data=f"rreason_{submission_id}_r3")],
            [InlineKeyboardButton(text="✍️ Boshqa sabab yozish", callback_data=f"rreason_{submission_id}_custom")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"backrev_{submission_id}")],
        ]
    )


def approve_choice_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    """Qabul qilish uchun qaysi xabar yuborilishini tanlash menyusi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Standart tabrik xabari", callback_data=f"apreason_{submission_id}_std")],
            [InlineKeyboardButton(text="📜 Rasmiy xabar (nashr uchun qabul)", callback_data=f"apreason_{submission_id}_official")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"backrev_{submission_id}")],
        ]
    )