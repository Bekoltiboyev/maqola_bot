import logging
from typing import Any, Awaitable, Callable, Dict, Union

from aiogram import Router, F, Bot, types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.fsm.context import FSMContext

import database as db
import config
from keyboards import subscribe_keyboard, main_menu_keyboard
from states import RegisterStates

router = Router()
logger = logging.getLogger(__name__)


async def get_unjoined_channels(bot: Bot, user_id: int):
    """Foydalanuvchi hali qo'shilmagan majburiy kanal/guruhlar ro'yxatini qaytaradi."""
    channels = await db.get_all_channels()
    unjoined = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["chat_id"], user_id)
            if member.status in ("left", "kicked"):
                unjoined.append(ch)
        except Exception as e:
            logger.warning(f"'{ch['chat_id']}' obunasini tekshirishda xatolik: {e}")
            # Tekshirib bo'lmasa (bot o'sha yerda admin emas va h.k) - xavfsizlik uchun obuna emas deb hisoblaymiz
            unjoined.append(ch)
    return unjoined


class SubscriptionMiddleware(BaseMiddleware):
    """Har bir xabar/tugma bosilishidan oldin barcha majburiy kanallarga a'zolikni tekshiradi."""

    async def __call__(
        self,
        handler: Callable[[Union[types.Message, types.CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[types.Message, types.CallbackQuery],
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id

        # Admin uchun tekshiruv shart emas
        if user_id in config.ADMIN_IDS:
            return await handler(event, data)

        # "✅ Tekshirish" tugmasi bosilganda handlerning o'ziga o'tkazamiz
        if isinstance(event, types.CallbackQuery) and event.data == "check_sub":
            return await handler(event, data)

        bot: Bot = data["bot"]
        unjoined = await get_unjoined_channels(bot, user_id)

        if unjoined:
            markup = subscribe_keyboard(unjoined)
            if isinstance(event, types.CallbackQuery):
                await event.answer("❌ Siz hali barcha kanal/guruhlarga a'zo bo'lmagansiz!", show_alert=True)
                try:
                    await event.message.answer(
                        "Botdan foydalanish uchun avval quyidagi kanal/guruh(lar)ga a'zo bo'ling:",
                        reply_markup=markup,
                    )
                except Exception:
                    pass
            else:
                await event.answer(
                    "⚠️ Botdan foydalanish uchun avval quyidagi kanal/guruh(lar)ga a'zo bo'lishingiz shart:",
                    reply_markup=markup,
                )
            return  # handlerga o'tkazmaymiz

        return await handler(event, data)


@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    unjoined = await get_unjoined_channels(bot, callback.from_user.id)

    if unjoined:
        await callback.answer(f"❌ Yana {len(unjoined)} ta kanal/guruhga a'zo bo'lishingiz kerak!", show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    user = await db.get_user_by_tg(callback.from_user.id)
    if user:
        await callback.message.answer(
            f"✅ Obuna tasdiqlandi! Xush kelibsiz, <b>{user['full_name']}</b>!",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await callback.message.answer(
            "✅ Obuna tasdiqlandi!\n\n"
            "📝 Ro'yxatdan o'tish uchun to'liq ism va familiyangizni kiriting.\n"
            "Masalan: <b>Aliyev Vali</b>"
        )
        await state.set_state(RegisterStates.waiting_name)

    await callback.answer()