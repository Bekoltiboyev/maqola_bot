from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

import database as db
import config
from states import AdminUploadStates, ChannelStates, BroadcastStates, ReviewStates
from keyboards import admin_panel_keyboard, channels_manage_keyboard

router = Router()
# Ushbu router faqat ADMIN_IDS ro'yxatidagi foydalanuvchilar uchun ishlaydi
router.message.filter(F.from_user.id.in_(config.ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(config.ADMIN_IDS))


@router.message(Command("admin"))
async def admin_panel(message: Message):
    await message.answer("🔐 <b>Admin panel</b>", reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == "admin_new_journal")
async def new_journal(callback: CallbackQuery, bot: Bot):
    new_number = await db.create_new_journal()
    await callback.answer("Yangi jurnal ochildi!")
    await callback.message.answer(
        f"✅ №{new_number}-jurnal ochildi. Foydalanuvchilarga xabar yuborilmoqda..."
    )

    tg_ids = await db.get_all_user_tg_ids()
    sent, failed = 0, 0
    for tg_id in tg_ids:
        try:
            await bot.send_message(
                tg_id,
                f"🎉 <b>№{new_number}-jurnal</b> uchun maqolalar qabul qilish boshlandi!\n"
                'Marhamat, "📤 Maqola yuborish" tugmasi orqali maqolangizni yuboring.',
            )
            sent += 1
        except Exception:
            failed += 1

    await callback.message.answer(f"📨 Xabar yuborildi: {sent} ta ✅ | {failed} ta ❌")


@router.callback_query(F.data == "admin_upload_info")
async def ask_info_letter(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("✉️ Axborot xati faylini yuboring (.pdf yoki .docx).")
    await state.set_state(AdminUploadStates.waiting_info_letter)


@router.callback_query(F.data == "admin_upload_sample")
async def ask_sample(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("📑 Maqola namunasi faylini yuboring (.pdf yoki .docx).")
    await state.set_state(AdminUploadStates.waiting_sample)


@router.message(AdminUploadStates.waiting_info_letter, F.document)
async def save_info_letter(message: Message, state: FSMContext):
    await db.set_admin_file("info_letter", message.document.file_id, message.document.file_name)
    await message.answer("✅ Axborot xati yangilandi. Endi barcha userlarga shu fayl yuboriladi.")
    await state.clear()


@router.message(AdminUploadStates.waiting_sample, F.document)
async def save_sample(message: Message, state: FSMContext):
    await db.set_admin_file("sample", message.document.file_id, message.document.file_name)
    await message.answer("✅ Maqola namunasi yangilandi. Endi barcha userlarga shu fayl yuboriladi.")
    await state.clear()


@router.message(AdminUploadStates.waiting_info_letter)
@router.message(AdminUploadStates.waiting_sample)
async def wrong_admin_upload(message: Message):
    await message.answer("❗ Iltimos, fayl (document) ko'rinishida yuboring.")


@router.callback_query(F.data == "admin_stats")
async def stats(callback: CallbackQuery):
    await callback.answer()
    users = await db.count_users()
    journals = await db.count_journals()
    subs = await db.count_submissions()
    current = await db.get_current_journal()
    await callback.message.answer(
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: {users}\n"
        f"📚 Jurnallar: {journals} (joriy: №{current['number']})\n"
        f"📥 Jami maqolalar: {subs}"
    )


# ==================== MAJBURIY KANALLAR (istalgancha) ====================

def _channels_text(channels) -> str:
    if not channels:
        return "📢 Hozircha majburiy kanal/guruh qo'shilmagan."
    lines = ["📢 <b>Majburiy kanal/guruhlar:</b>\n"]
    for ch in channels:
        title = ch["title"] or ch["chat_id"]
        lines.append(f"🔹 {title} — <code>{ch['chat_id']}</code>")
    return "\n".join(lines)


@router.callback_query(F.data == "admin_channels")
async def admin_channels(callback: CallbackQuery):
    await callback.answer()
    channels = await db.get_all_channels()
    await callback.message.answer(_channels_text(channels), reply_markup=channels_manage_keyboard(channels))


@router.callback_query(F.data == "addch")
async def addch_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Kanal yoki guruhning username'ini (masalan: <b>@mychannel</b>) yoki raqamli ID'sini "
        "(masalan: <b>-1001234567890</b>) yuboring.\n\n"
        "⚠️ Diqqat: bot o'sha kanal/guruhda <b>ADMIN</b> qilib qo'yilgan bo'lishi shart, "
        "aks holda a'zolikni tekshira olmaydi!\n\n"
        "Bekor qilish uchun /cancel"
    )
    await state.set_state(ChannelStates.waiting_chat_id)


@router.message(Command("cancel"), ChannelStates.waiting_chat_id)
@router.message(Command("cancel"), ChannelStates.waiting_url)
async def addch_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())


@router.message(ChannelStates.waiting_chat_id)
async def addch_id(message: Message, state: FSMContext):
    chat_id = message.text.strip()
    await state.update_data(chat_id=chat_id)
    await message.answer("Endi shu kanal/guruhning taklif havolasini yuboring (masalan: https://t.me/mychannel):")
    await state.set_state(ChannelStates.waiting_url)


@router.message(ChannelStates.waiting_url)
async def addch_url(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    chat_id = data["chat_id"]
    url = message.text.strip()

    title = chat_id
    warn = ""
    try:
        chat = await bot.get_chat(chat_id)
        title = chat.title or chat_id
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id, me.id)
        if member.status not in ("administrator", "creator"):
            warn = "\n\n⚠️ Ogohlantirish: bot bu yerda ADMIN emas! Uni admin qilib qo'ymasangiz, obuna tekshiruvi ishlamaydi."
    except Exception:
        warn = "\n\n⚠️ Ogohlantirish: bu kanal/guruhni topa olmadim. ID/username to'g'riligini va bot admin ekanini tekshiring."

    await db.add_channel(chat_id, url, title)
    await state.clear()
    await message.answer(f"✅ Kanal qo'shildi: {title} ({chat_id}){warn}", reply_markup=admin_panel_keyboard())


@router.callback_query(F.data.startswith("refch_"))
async def refresh_channel(callback: CallbackQuery, bot: Bot):
    channel_id = int(callback.data.split("_", 1)[1])
    ch = await db.get_channel(channel_id)
    if not ch:
        await callback.answer("❗ Kanal topilmadi.", show_alert=True)
        return

    try:
        chat = await bot.get_chat(ch["chat_id"])
        new_title = chat.title or ch["chat_id"]
        await db.update_channel_title(channel_id, new_title)
        await callback.answer(f"✅ Yangilandi: {new_title}")
    except Exception:
        await callback.answer(
            "❗ Kanal nomini ololmadim. Bot shu yerda ADMIN ekanini tekshiring.",
            show_alert=True,
        )
        return

    channels = await db.get_all_channels()
    try:
        await callback.message.edit_text(_channels_text(channels), reply_markup=channels_manage_keyboard(channels))
    except Exception:
        pass


@router.callback_query(F.data.startswith("delch_"))
async def delch(callback: CallbackQuery):
    channel_id = int(callback.data.split("_", 1)[1])
    await db.remove_channel(channel_id)
    await callback.answer("✅ O'chirildi")

    channels = await db.get_all_channels()
    try:
        await callback.message.edit_text(_channels_text(channels), reply_markup=channels_manage_keyboard(channels))
    except Exception:
        pass


# ==================== BARCHAGA BITTA XABAR YUBORISH ====================

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "✍️ Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring.\n"
        "Matn, rasm, video yoki fayl bo'lishi mumkin — u xuddi shu ko'rinishda hammaga yuboriladi.\n\n"
        "Bekor qilish uchun /cancel"
    )
    await state.set_state(BroadcastStates.waiting_message)


@router.message(Command("cancel"), BroadcastStates.waiting_message)
async def broadcast_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())


@router.message(BroadcastStates.waiting_message)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    tg_ids = await db.get_all_user_tg_ids()
    status = await message.answer(f"⏳ Xabar {len(tg_ids)} ta foydalanuvchiga yuborilmoqda...")

    sent, failed = 0, 0
    for tg_id in tg_ids:
        try:
            await bot.copy_message(chat_id=tg_id, from_chat_id=message.chat.id, message_id=message.message_id)
            sent += 1
        except Exception:
            failed += 1

    await status.edit_text(f"📨 Xabar yuborildi: {sent} ta ✅ | {failed} ta ❌")
    await message.answer("Admin panel:", reply_markup=admin_panel_keyboard())


# ==================== MAQOLALARNI KO'RIB CHIQISH (Qabul / Rad etish) ====================

@router.callback_query(F.data.startswith("approve_"))
async def approve_submission(callback: CallbackQuery, bot: Bot):
    submission_id = int(callback.data.split("_", 1)[1])
    sub = await db.get_submission_full(submission_id)

    if not sub:
        await callback.answer("❗ Maqola topilmadi.", show_alert=True)
        return

    if sub["status"] != "pending":
        await callback.answer("⚠️ Bu maqola allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.set_submission_status(submission_id, "approved")
    await callback.answer("✅ Qabul qilindi")

    try:
        await callback.message.edit_caption(
            caption=(callback.message.caption or "") + "\n\n✅ <b>QABUL QILINDI</b>",
            reply_markup=None,
        )
    except Exception:
        pass

    try:
        await bot.send_message(
            sub["user_tg_id"],
            f"🎉 <b>Tabriklaymiz!</b>\n\n"
            f"№{sub['journal_number']}-jurnal uchun yuborgan <b>{sub['file_name']}</b> nomli maqolangiz "
            f"qabul qilindi!",
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("reject_"))
async def reject_start(callback: CallbackQuery, state: FSMContext):
    submission_id = int(callback.data.split("_", 1)[1])
    sub = await db.get_submission_full(submission_id)

    if not sub:
        await callback.answer("❗ Maqola topilmadi.", show_alert=True)
        return

    if sub["status"] != "pending":
        await callback.answer("⚠️ Bu maqola allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await callback.answer()
    await state.update_data(submission_id=submission_id, admin_msg_id=callback.message.message_id, admin_chat_id=callback.message.chat.id)
    await callback.message.answer(
        "✍️ Rad etish sababini yozing — bu xabar aynan shu ko'rinishda foydalanuvchiga yuboriladi.\n\n"
        "Bekor qilish uchun /cancel"
    )
    await state.set_state(ReviewStates.waiting_reject_reason)


@router.message(Command("cancel"), ReviewStates.waiting_reject_reason)
async def reject_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())


@router.message(ReviewStates.waiting_reject_reason, F.text)
async def reject_finish(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    submission_id = data["submission_id"]
    reason = message.text.strip()

    sub = await db.get_submission_full(submission_id)
    await state.clear()

    if not sub or sub["status"] != "pending":
        await message.answer("⚠️ Bu maqola allaqachon ko'rib chiqilgan yoki topilmadi.", reply_markup=admin_panel_keyboard())
        return

    await db.set_submission_status(submission_id, "rejected", reason)

    try:
        await bot.edit_message_caption(
            chat_id=data["admin_chat_id"],
            message_id=data["admin_msg_id"],
            caption=(
                f"📥 <b>Maqola</b>\n"
                f"👤 {sub['user_full_name']}\n"
                f"📚 Jurnal: №{sub['journal_number']}\n\n"
                f"❌ <b>RAD ETILDI</b>\nSabab: {reason}"
            ),
            reply_markup=None,
        )
    except Exception:
        pass

    try:
        await bot.send_message(
            sub["user_tg_id"],
            f"❌ Afsuski, №{sub['journal_number']}-jurnal uchun yuborgan <b>{sub['file_name']}</b> nomli "
            f"maqolangiz rad etildi.\n\n"
            f"<b>Sabab:</b> {reason}",
        )
    except Exception:
        pass

    await message.answer("✅ Rad etish sababi foydalanuvchiga yuborildi.", reply_markup=admin_panel_keyboard())