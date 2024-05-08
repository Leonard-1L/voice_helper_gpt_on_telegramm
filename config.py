HOME_DIR = '/home/student/Dev/voice_helper_gpt_on_telegramm'  # путь к папке с проектом
DB_FILE = f'{HOME_DIR}/messages.db'  # файл для базы данных
LOGS = f'{HOME_DIR}/logs.txt'

IAM_TOKEN_PATH = f'{HOME_DIR}/creds/iam_token.json'  # файл для хранения iam_token
FOLDER_ID_PATH = f'{HOME_DIR}/creds/folder_id.txt'  # файл для хранения folder_id
BOT_TOKEN_PATH = f'{HOME_DIR}/creds/bot_token.txt'  # файл для хранения bot_token

MAX_USERS = 3  # максимальное кол-во пользователей
MAX_GPT_TOKENS = 200  # максимальное кол-во токенов в ответе GPT
COUNT_LAST_MSG = 2  # кол-во последних сообщений из диалога доступных для памяти нейросети

# лимиты для пользователя
MAX_USER_STT_BLOCKS = 10  # колво аудиоблоков для расшифровки аудио
MAX_USER_TTS_SYMBOLS = 5_000  # кол-во символов для озвучки текста
MAX_USER_GPT_TOKENS = 400  # колво токенов для взаимодействия с gpt
MAX_REQUESTS_SYMBOLS = 300  # Максимально количество символов на один запрос
TEXT_VOICE = "madirus"  # Голос при озвучивании текста. Женский это marina, мужской - madirus

SYSTEM_PROMPT = [{'role': 'system',
                  'text': 'Смешно рифмуй в ответ'}]  # список с системным промтом
