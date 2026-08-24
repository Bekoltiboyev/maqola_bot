from aiogram.fsm.state import State, StatesGroup


class RegisterStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()


class ArticleStates(StatesGroup):
    waiting_file = State()


class AdminUploadStates(StatesGroup):
    waiting_info_letter = State()
    waiting_sample = State()


class ChannelStates(StatesGroup):
    waiting_chat_id = State()
    waiting_url = State()


class BroadcastStates(StatesGroup):
    waiting_message = State()