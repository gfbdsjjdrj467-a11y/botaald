import asyncio
from telethon import TelegramClient, events, Button
import os
import tempfile
import requests
import json
import subprocess
import time

BOT_TOKEN = "8962532742:AAG1377yowFSqklfaPP_AzEXvIvV-Fm_jqw"
GROQ_API_KEY = "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"
API_URL = "https://api.groq.com/openai/v1/chat/completions"

bot = TelegramClient('deployer_bot', api_id=6, api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e")

# Хранилище состояний пользователей
user_states = {}

# Папка для загруженных ботов
BOTS_DIR = "deployed_bots"
os.makedirs(BOTS_DIR, exist_ok=True)

def generate_bot_code(description: str) -> str:
    """ИИ генерирует код бота по описанию"""
    prompt = f"""
Ты — эксперт по Telegram ботам на Python (библиотека Telethon).
Напиши ПОЛНЫЙ рабочий код бота по описанию пользователя.

Правила:
1. Используй: from telethon import TelegramClient, events
2. api_id = 6, api_hash = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
3. Токен должен быть: BOT_TOKEN = "ВСТАВЬ_СВОЙ_ТОКЕН"
4. Добавь команду /start с описанием функций
5. Выдай ТОЛЬКО Python код, без объяснений
6. Код должен быть полностью рабочим

Описание бота: {description}
"""
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 3000
    }
    
    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        code = resp.json()['choices'][0]['message']['content']
        return code.replace("```python", "").replace("```", "").strip()
    except Exception as e:
        return f"# Ошибка генерации: {e}"

def deploy_bot(code: str, token: str) -> str:
    """Запускает бота с новым токеном"""
    # Заменяем токен в коде
    code = code.replace("ВСТАВЬ_СВОЙ_ТОКЕН", token)
    code = code.replace('"ТОКЕН_СЮДА"', token)
    code = code.replace("'ТОКЕН_СЮДА'", token)
    
    # Создаём имя файла
    bot_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    filename = f"{BOTS_DIR}/bot_{bot_id}.py"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(code)
    
    # Запускаем бота в фоне
    subprocess.Popen(['python', filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return f"bot_{bot_id}.py"

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    buttons = [
        [Button.inline("📤 Загрузить код (деплой бота)", "upload")],
        [Button.inline("🤖 ИИ напишет бота", "ai_generate")],
        [Button.inline("📋 Мои боты", "list")],
    ]
    await event.reply(
        "🤖 **Бот-Деплоер**\n\n"
        "📤 **Загрузить код** — скинь .py файл, я запущу его с твоим токеном\n"
        "🤖 **ИИ напишет** — опиши бота, ИИ создаст код и запустит\n\n"
        "Выбери действие:",
        buttons=buttons
    )

@bot.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    data = event.data.decode()
    
    if data == "upload":
        user_states[user_id] = {'action': 'wait_code'}
        await event.edit("📤 **Отправь .py файл с кодом бота**\n\nЗатем я спрошу токен для деплоя.")
    
    elif data == "ai_generate":
        user_states[user_id] = {'action': 'wait_description'}
        await event.edit("🤖 **Опиши бота**\n\nНапиши что должен делать бот.\nПример: «бот для поиска по базам данных, принимает номер телефона и выдаёт информацию»")
    
    elif data == "list":
        bots = [f for f in os.listdir(BOTS_DIR) if f.endswith('.py')]
        if bots:
            text = "📋 **Запущенные боты:**\n\n" + "\n".join([f"• `{b}`" for b in bots])
        else:
            text = "Нет запущенных ботов."
        await event.edit(text)

@bot.on(events.NewMessage(incoming=True))
async def handle(event):
    if event.out:
        return
    
    user_id = event.sender_id
    text = event.text.strip() if event.text else ""
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    
    # Обработка загрузки файла
    if state['action'] == 'wait_code':
        if event.file and event.file.name and event.file.name.endswith('.py'):
            # Скачиваем файл
            temp_path = os.path.join(tempfile.gettempdir(), event.file.name)
            await event.download_media(temp_path)
            
            with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            user_states[user_id]['code'] = code
            user_states[user_id]['action'] = 'wait_token'
            
            await event.reply(
                "✅ Код получен!\n\n"
                "Теперь отправь **токен бота** от @BotFather\n"
                "Формат: `123456:ABCdef...`"
            )
            os.remove(temp_path)
        else:
            await event.reply("❌ Отправь именно .py файл с кодом бота!")
    
    # Обработка токена
    elif state['action'] == 'wait_token':
        token = text.strip()
        if ':' in token and len(token) > 30:
            code = state['code']
            
            msg = await event.reply("⏳ Запускаю бота...")
            
            try:
                filename = deploy_bot(code, token)
                del user_states[user_id]
                await msg.edit(f"✅ **Бот запущен!**\n\nФайл: `{filename}`\nТокен: `{token[:10]}...`\n\nБот уже работает!")
            except Exception as e:
                await msg.edit(f"❌ Ошибка запуска: {e}")
        else:
            await event.reply("❌ Неверный формат токена. Должно быть: `123456:ABCdef...`")
    
    # Обработка описания для ИИ
    elif state['action'] == 'wait_description':
        description = text
        msg = await event.reply("🤖 ИИ генерирует код...")
        
        code = generate_bot_code(description)
        
        # Сохраняем сгенерированный код
        gen_path = os.path.join(tempfile.gettempdir(), f"generated_bot_{random.randint(1000,9999)}.py")
        with open(gen_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        await msg.edit("✅ Код сгенерирован! Отправляю файл...")
        await bot.send_file(user_id, gen_path, caption="🤖 Готовый бот!\n\n📝 Замени `ВСТАВЬ_СВОЙ_ТОКЕН` на токен от @BotFather\nИли отправь мне .py файл обратно с токеном — я запущу!")
        
        os.remove(gen_path)
        del user_states[user_id]

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    print("🤖 Бот-Деплоер запущен!")
    print("📤 Загрузи .py файл — запущу бота")
    print("🤖 Или опиши бота — ИИ создаст код")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    import random, string
    asyncio.run(main())
