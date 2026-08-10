import os
import re

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import database as db
import config
from states import RegisterStates
from keyboards import phone_keyboard, main_menu_keyboard

router = Router()

NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ'\- ]{3,60}$")
PHONE_RE = re.compile(r"^\+?\d{9,15}$")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    # Intro video (agar media/intro.mp4 mavjud bo'lsa)
    try:
        if os.path.exists(config.INTRO_VIDEO_PATH):
            await message.answer_video(
                FSInputFile(config.INTRO_VIDEO_PATH),
                caption="👋 Xush kelibsiz! Bot imkoniyatlari haqida qisqacha video.",
            )
    except Exception:
        pass

    user = await db.get_user_by_tg(message.from_user.id)
    if user:
        await message.answer(
            f"Xush kelibsiz, <b>{user['full_name']}</b>! 👇 Quyidagi bo'limlardan birini tanlang:",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(
        "📝 <b>Ro'yxatdan o'tish</b>\n\n"
        "Iltimos, to'liq ism va familiyangizni kiriting.\n"
        "Masalan: <b>Aliyev Vali</b>"
    )
    await state.set_state(RegisterStates.waiting_name)


@router.message(RegisterStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not NAME_RE.match(text):
        await message.answer(
            "❗ Ism-familiya noto'g'ri kiritildi. Faqat harflardan foydalaning "
            "(kamida 3 ta belgi). Masalan: <b>Aliyev Vali</b>"
        )
        return

    await state.update_data(full_name=text)
    await message.answer(
        "📱 Endi telefon raqamingizni yuboring.\n"
        "Pastdagi tugmadan foydalaning yoki qo'lda kiriting (masalan: +998901234567).",
        reply_markup=phone_keyboard(),
    )
    await state.set_state(RegisterStates.waiting_phone)


@router.message(RegisterStates.waiting_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    await _finish_registration(message, state, message.contact.phone_number)


@router.message(RegisterStates.waiting_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip().replace(" ", "")
    if not PHONE_RE.match(phone):
        await message.answer(
            "❗ Telefon raqam noto'g'ri formatda.\nMasalan: <b>+998901234567</b> ko'rinishida kiriting."
        )
        return
    await _finish_registration(message, state, phone)


@router.message(RegisterStates.waiting_phone)
async def process_phone_invalid(message: Message):
    await message.answer("❗ Iltimos, telefon raqamingizni matn yoki tugma orqali yuboring (rasm/fayl emas).")


async def _finish_registration(message: Message, state: FSMContext, phone: str):
    data = await state.get_data()
    full_name = data.get("full_name", "").strip()

    existing = await db.get_user_by_tg(message.from_user.id)
    if not existing:
        await db.register_user(message.from_user.id, full_name, phone)

    await state.clear()
    await message.answer(
        "✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n"
        "👇 Quyidagi bo'limlardan birini tanlang:",
        reply_markup=main_menu_keyboard(),
    )
