import os
import uuid

from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import database as db
import config
from states import ArticleStates
from keyboards import main_menu_keyboard, review_keyboard

router = Router()


async def _require_registered(message: Message) -> bool:
    user = await db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer("❗ Avval ro'yxatdan o'ting: /start buyrug'ini bosing.")
        return False
    return True


def _verify_file_signature(path: str, ext: str) -> bool:
    """Fayl kengaytmasi haqiqiy tarkibga mos kelishini tekshiradi (xavfsizlik)."""
    try:
        with open(path, "rb") as f:
            header = f.read(8)
        if ext == ".pdf":
            return header.startswith(b"%PDF")
        if ext == ".docx":
            return header.startswith(b"PK")  # docx = zip konteyner
        if ext == ".doc":
            return header.startswith(b"\xd0\xcf\x11\xe0")  # legacy OLE format
        return True
    except Exception:
        return True


@router.message(F.text == "📤 Maqola yuborish")
async def send_article_start(message: Message, state: FSMContext):
    if not await _require_registered(message):
        return

    user = await db.get_user_by_tg(message.from_user.id)
    journal = await db.get_current_journal()

    if await db.has_submitted(user["id"], journal["id"]):
        await message.answer(
            f"⚠️ Siz №{journal['number']}-jurnal uchun allaqachon maqola yuborgansiz.\n"
            "Keyingi jurnal ochilishi haqida bot orqali xabar berilganda qayta yuborishingiz mumkin bo'ladi."
        )
        return

    await message.answer(
        "📎 Maqolangizni <b>.docx</b> yoki <b>.pdf</b> formatida yuboring.\n"
        f"Fayl hajmi {config.MAX_FILE_SIZE_MB}MB dan oshmasin."
    )
    await state.set_state(ArticleStates.waiting_file)


@router.message(ArticleStates.waiting_file, F.document)
async def receive_article_file(message: Message, state: FSMContext, bot: Bot):
    doc = message.document
    ext = os.path.splitext(doc.file_name or "")[1].lower()

    if ext not in config.ALLOWED_EXTENSIONS:
        await message.answer(
            "❌ Fayl formati noto'g'ri!\n"
            "Faqat <b>.doc</b>, <b>.docx</b> yoki <b>.pdf</b> formatidagi fayllarni qabul qilamiz. "
            "Iltimos, qaytadan yuboring."
        )
        return

    if doc.file_size and doc.file_size > config.MAX_FILE_SIZE_MB * 1024 * 1024:
        await message.answer(f"❌ Fayl hajmi juda katta! Maksimal hajm: {config.MAX_FILE_SIZE_MB}MB.")
        return

    user = await db.get_user_by_tg(message.from_user.id)
    journal = await db.get_current_journal()

    # Qayta tekshirish (race-condition / ikki marta bosishning oldini olish)
    if await db.has_submitted(user["id"], journal["id"]):
        await message.answer("⚠️ Siz bu jurnal uchun allaqachon maqola yuborgansiz.")
        await state.clear()
        return

    journal_dir = os.path.join(config.ARTICLES_DIR, str(journal["number"]))
    os.makedirs(journal_dir, exist_ok=True)
    safe_name = f"{user['id']}_{uuid.uuid4().hex[:8]}{ext}"
    dest_path = os.path.join(journal_dir, safe_name)

    await bot.download(doc, destination=dest_path)

    if not _verify_file_signature(dest_path, ext):
        try:
            os.remove(dest_path)
        except OSError:
            pass
        await message.answer(
            "❌ Fayl buzilgan yoki formati mos emas. Iltimos, haqiqiy .docx yoki .pdf fayl yuboring."
        )
        return

    submission_id = await db.add_submission(user["id"], journal["id"], doc.file_name, dest_path, ext)

    await message.answer(
        "✅ Maqolangiz muvaffaqiyatli qabul qilindi! Rahmat.",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_document(
                admin_id,
                doc.file_id,
                caption=(
                    "📥 <b>Yangi maqola</b>\n"
                    f"👤 {user['full_name']}\n"
                    f"📱 {user['phone']}\n"
                    f"🆔 tg_id: {user['tg_id']}\n"
                    f"📚 Jurnal: №{journal['number']}"
                ),
                reply_markup=review_keyboard(submission_id),
            )
        except Exception:
            pass


@router.message(ArticleStates.waiting_file)
async def receive_article_wrong_type(message: Message):
    await message.answer(
        "❌ Noto'g'ri format! Matn, rasm yoki boshqa turdagi fayl emas — "
        "faqat <b>.docx</b> yoki <b>.pdf</b> hujjat yuboring."
    )


@router.message(F.text == "📄 Men yuborgan maqolalar")
async def my_articles(message: Message):
    if not await _require_registered(message):
        return

    user = await db.get_user_by_tg(message.from_user.id)
    subs = await db.get_user_submissions(user["id"])

    if not subs:
        await message.answer("📭 Siz hali maqola yubormagansiz.")
        return

    lines = ["📄 <b>Sizning maqolalaringiz:</b>\n"]
    status_map = {
        "pending": "⏳ Ko'rib chiqilmoqda",
        "approved": "✅ Qabul qilindi",
        "rejected": "❌ Rad etildi",
    }
    for s in subs:
        date = (s["submitted_at"] or "").split(".")[0]
        status_text = status_map.get(s["status"] or "pending", "⏳ Ko'rib chiqilmoqda")
        lines.append(f"• №{s['journal_number']}-jurnal — {s['file_name']} ({date})\n  Holati: {status_text}")

    await message.answer("\n".join(lines))


@router.message(F.text == "📊 Jurnallar soni")
async def journals_count(message: Message):
    if not await _require_registered(message):
        return

    total = await db.count_journals()
    current = await db.get_current_journal()
    await message.answer(
        f"📊 Hozirgacha chiqarilgan jurnallar soni: <b>{total}</b>\n"
        f"📚 Joriy jurnal: №{current['number']}"
    )


@router.message(F.text == "✉️ Axborot xati")
async def info_letter(message: Message):
    if not await _require_registered(message):
        return

    row = await db.get_admin_file("info_letter")
    if not row:
        await message.answer("⏳ Hozircha axborot xati yuklanmagan. Tez orada qo'shiladi.")
        return
    await message.answer_document(row["file_id"], caption="✉️ Axborot xati")


@router.message(F.text == "📑 Maqola namunasi")
async def sample_article(message: Message):
    if not await _require_registered(message):
        return

    row = await db.get_admin_file("sample")
    if not row:
        await message.answer("⏳ Hozircha maqola namunasi yuklanmagan. Tez orada qo'shiladi.")
        return
    await message.answer_document(row["file_id"], caption="📑 Maqola namunasi")


# ---------- Kutilmagan turdagi xabarlar (raqam, matn, rasm) uchun ogohlantirish ----------

@router.message(F.photo)
async def unexpected_photo(message: Message):
    if not await _require_registered(message):
        return
    await message.answer(
        "❗ Bot rasm qabul qilmaydi. Iltimos, quyidagi menyudan kerakli bo'limni tanlang.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.document)
async def unexpected_document(message: Message):
    if not await _require_registered(message):
        return
    await message.answer(
        '❗ Hozir fayl kutilmayapti. Maqola yuborish uchun avval "📤 Maqola yuborish" tugmasini bosing.',
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text)
async def unexpected_text(message: Message):
    if not await _require_registered(message):
        return
    await message.answer(
        "❗ Kechirasiz, tushunmadim. Iltimos, quyidagi menyudan tanlang:",
        reply_markup=main_menu_keyboard(),
    )