import os

import telebot
from telebot.types import Message
from validators import *
from ya_gpt import ask_gpt
from sql_database import create_database, add_message, select_n_last_messages, count_all_tokens
from speechkit import *
from creds import get_bot_token
from config import LOGS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=LOGS,
    filemode="w"
)

create_database()
bot = telebot.TeleBot(token=get_bot_token())

help_sms = '''Догадки есть же у меня,
что нет проблем у вас сейчас,
а просто надоела вам болтовня
или кнопка случайно заманила вас.
Тогда тут нету обьяснений,
лишь только место для презрений.

Но если вы нажали неспроста,
то создатель мой сам узнает, что за суета
мешает вам мои стихи любить, читать,
да и самого разработчика посрамлять.'''


@bot.message_handler(commands=['start'])
def start(message: Message):
    bot.send_message(message.from_user.id,
                     f"{message.from_user.username}, приветсвую тебя!\n"
                     f"Я не Шекспир конечно, но рифмоплет,\n"
                     f"Обидеть я фразой могу шутя,\n"
                     f"Хоть посуществу я просто бот.\n"
                     f"\n"
                     f"Ты напиши или в диктофон скажи,\n"
                     f"Что хочешь для своей души.\n"
                     f"Коль ты запутаешся где-то,\n"
                     f"То команда /help там будет к месту.")


@bot.message_handler(content_types=['voice'])
def handle_voice(message: telebot.types.Message):
    try:
        user_id = message.from_user.id

        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return

        stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
        if error_message:
            bot.send_message(user_id, error_message)
            return

        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        status_stt, stt_text = speech_to_text(file)
        if not status_stt:
            bot.send_message(user_id, stt_text)
            return

        add_message(user_id=user_id, full_message=[stt_text, 'user', 0, 0, stt_blocks])

        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            bot.send_message(user_id, error_message)
            return

        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return

        total_gpt_tokens += tokens_in_answer

        tts_symbols, error_message = is_tts_symbol_limit(user_id, answer_gpt)

        add_message(user_id=user_id, full_message=[answer_gpt, 'assistant', total_gpt_tokens, tts_symbols, 0])

        if error_message:
            bot.send_message(user_id, error_message)
            return

        status_tts, voice_response = text_to_voice(answer_gpt)
        if status_tts:
            bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)
        else:
            bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)

    except Exception as e:
        logging.error(f"Ошибка при обработке голосового сообщения. {e}")
        bot.send_message(message.from_user.id, "Не получилось ответить. Попробуй записать другое сообщение")


@bot.message_handler(commands=['help'])
def send_help(message: Message):
    bot.send_message(message.from_user.id, help_sms)
    logging.info(f"{message.from_user.id} запросил помощь.")


@bot.message_handler(commands=['debug'])
def send_logs(message: Message):
    logging.info(f'{message.from_user.username} с ID {message.from_user.id} запросил логи')
    with open(LOGS, 'r') as logs:
        bot.send_document(message.from_user.id, logs)


@bot.message_handler(commands=['rm_db'])
def remove_database(message):
    tokens = count_all_tokens()
    os.remove(DB_FILE)
    bot.send_message(message.from_user.id, f"База удалена, потрачено токенов: {tokens}.")


@bot.message_handler(commands=['cr_db'])
def creat_database(message):
    create_database()
    logging.info('Дата база создана.')

@bot.message_handler(commands=['tts'])
def tts_handler(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Отправь следующим сообщением текст, чтобы я его озвучил!')
    bot.register_next_step_handler(message, tts)


def tts(message):
    user_id = message.chat.id
    text = message.text
    try:
        if message and message.content_type != 'text':
            bot.send_message(user_id, 'Отправь текстовое сообщение')
            return

        status, error_message = is_tts_symbol_limit(user_id, text)
        if error_message:
            bot.send_message(user_id, error_message)
            return

        logging.info(f"Запрос от {user_id} проверки режима TTS")
        status, content = text_to_voice(text)

        full_message = [text, 'user', 0, len(text), 0]

        if status:
            add_message(user_id, full_message)
            bot.send_voice(user_id, content)
        else:
            bot.send_message(user_id, content)
    except Exception as e:
        logging.error(e)
        bot.send_message(user_id,
                         "Не получилось перевест текст в аудио. Разрабочик уже в пути.")


@bot.message_handler(commands=['stt'])
def stt_handler(message):
    bot.send_message(message.chat.id, "Отправь голосовое сообщение: ")

    bot.register_next_step_handler(message, stt)


def stt(message):
    try:
        user_id = message.from_user.id

        if not message.voice:
            bot.send_message(user_id, 'Отправь голосовое сообщение')
            return

        blocks, out = is_stt_block_limit(user_id, message.voice.duration)
        if out:
            bot.send_message(user_id, out)
            return

        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)

        status, text = speech_to_text(file)

        full_message = [text, 'user', 0, 0, blocks]
        if status:
            add_message(user_id, full_message)
            bot.send_message(user_id, text, reply_to_message_id=message.id)
        else:
            bot.send_message(user_id, text)

    except Exception as e:
        logging.error(e)
        bot.send_message(message.from_user.id, "Не получилось перевести аудио. Попробуй еще раз.")
        return False, ""


@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        user_id = message.from_user.id

        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return

        full_user_message = [message.text, 'user', 0, 0, 0]
        add_message(user_id=user_id, full_message=full_user_message)

        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)

        if error_message:
            bot.send_message(user_id, error_message)
            return

        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return

        total_gpt_tokens += tokens_in_answer
        full_gpt_message = [answer_gpt, 'assistant', total_gpt_tokens, 0, 0]
        add_message(user_id=user_id, full_message=full_gpt_message)

        bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)
    except Exception as e:
        logging.error(e)
        bot.send_message(message.from_user.id, "Не получилось ответить. Попробуй написать другое сообщение")


@bot.message_handler(func=lambda: True)
def others_message(message):
    bot.send_message(message.from_user.id, "Отправь мне голосовое или текстовое сообщение, и я тебе отвечу")


if __name__ == "__main__":
    logging.info("Бот запущен")
    bot.polling(none_stop=True)
