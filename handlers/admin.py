from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

import database as db
import config
from states import AdminUploadStates
from keyboards import admin_panel_keyboard

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
