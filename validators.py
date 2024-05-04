import logging
from config import *
# подтягиваем функции для работы с БД
from sql_database import count_users, count_all_limits
# подтягиваем функцию для подсчета токенов в списке сообщений
from ya_gpt import count_gpt_tokens

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=LOGS,
    filemode="w"
)


def check_number_of_users(user_id):
    count = count_users(user_id)
    if count is None:
        return None, "Ошибка при работе с БД"
    if count > MAX_USERS:
        return None, "Превышено максимальное количество пользователей"
    return True, ""


def is_gpt_token_limit(messages, total_spent_tokens):
    all_tokens = count_gpt_tokens(messages) + total_spent_tokens
    if all_tokens > MAX_USER_GPT_TOKENS:
        return None, f"Превышен общий лимит GPT-токенов {MAX_USER_GPT_TOKENS}"
    return all_tokens, False


def is_stt_block_limit(user_id, duration):
    blocks_now = (duration // 15) + 1
    blocks = count_all_limits(user_id, 'stt_blocks') + blocks_now
    if blocks > MAX_USER_STT_BLOCKS or blocks_now > 2:
        return blocks, "Было затрачено слишком много аудио сообщений."
    return blocks, None


def is_tts_symbol_limit(user_id, text):
    symbols_now = len(text)
    symbols = count_all_limits(user_id, 'tts_symbols') + symbols_now
    if symbols > MAX_USER_TTS_SYMBOLS:
        return symbols, "Было затрачено слишком много символов."
    return symbols, None
