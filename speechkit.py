import logging
import requests
from config import *
from creds import get_creds


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=LOGS,
    filemode="w"
)


def speech_to_text(audio_file):
    iam_token, folder_id = get_creds()
    params = "&".join([
        "topic=general",
        f"folderId={folder_id}",
        "lang=ru-RU"
    ])
    url = f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}"
    headers = {
        'Authorization': f'Bearer {iam_token}',
    }
    response = requests.post(url=url, headers=headers, data=audio_file)
    decoded_data = response.json()
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")
    else:
        return False, "При расшифровке аудио произошла ошибка, повторите еще раз."


def text_to_voice(user_text: str):
    iam_token, folder_id = get_creds()
    headers = {
        'Authorization': f'Bearer {iam_token}'
    }
    data = {
        "text": user_text,
        'lang': 'ru=RU',
        'voice': TEXT_VOICE,
        'folderId': folder_id
    }
    response = requests.post('https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize', headers=headers, data=data)
    if response.status_code == 200:
        return True, response.content
    else:
        logging.error(f"0 НЬЕТ!1! КАКАЯТО ФИНГНГЯ СЛУЧТЛАСЬ. КОД ОШИБКИ:{response.status_code}")
        return False, f"При запросе произошла непредвиденная ошибка. Статус ошибки: {response.status_code}"
