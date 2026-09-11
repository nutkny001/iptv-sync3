import os
import json
import requests
from datetime import datetime, timedelta, timezone

# ดึงค่าจาก GitHub Secrets
HOST = os.getenv("API_HOST", "http://grace4k.com").strip()
if not HOST.startswith("http"):
    HOST = f"http://{HOST}"
HOST = HOST.rstrip("/")

USERNAME = os.getenv("API_USERNAME", "").strip()
PASSWORD = os.getenv("API_PASSWORD", "").strip()
OUTPUT_LIVE_M3U = "jadooball.m3u"

# กำหนดชื่อกลุ่มและรหัสหมวดหมู่ใหม่
CATEGORY_MAPPING = {
    "1350": "VIP | UEFA CHAMPIONS LEAGUE",
    "1362": "VIP | UEFA EUROPA LEAGUE",
    "1344": "VIP | PREMIER LEAGUE",
    "1346": "VIP | LA LIGA",
    "1349": "VIP | LIGUE 1",
    "1347": "VIP | SERIE A",
    "1345": "VIP | BUNDESLIGA",
    "1361": "VIP | LIGA PORTUGAL BETCLIC",
    "1496": "VIP | 4K ULTRA HD"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_live_via_api():
    if not USERNAME or not PASSWORD:
        print("[-] ไม่พบ Username หรือ Password ใน Secrets")
        return

    print("[1] กำลังยืนยันตัวตนผ่าน Xtream Codes API...")
    auth_url = f"{HOST}/player_api.php?username={USERNAME}&password={PASSWORD}"

    try:
        res = requests.get(auth_url, headers=headers, timeout=30)
        user_info = res.json()

        if user_info.get("user_info", {}).get("auth") != 1:
            print("[-] ยืนยันตัวตนไม่สำเร็จ")
            return

        exp_timestamp = user_info.get("user_info", {}).get("exp_date")
        if exp_timestamp and str(exp_timestamp).isdigit():
            dt = datetime.fromtimestamp(int(exp_timestamp))
            exp_date_str = dt.strftime('%d-%m-%Y')
        else:
            exp_date_str = "Unlimited"

        # ตั้งเวลาปัจจุบันให้เป็นเวลาประเทศไทย (UTC+7)
        thai_time = datetime.now(timezone.utc) + timedelta(hours=7)
        now_str = thai_time.strftime('%d-%m-%Y %H:%M')

        print(f"[i] วันหมดอายุ: {exp_date_str}")
        print(f"[i] อัปเดตล่าสุดเมื่อ (เวลาไทย): {now_str}")

        print("[2] กำลังดึงช่องสด...")
        live_url = f"{HOST}/player_api.php?username={USERNAME}&password={PASSWORD}&action=get_live_streams"
        live_res = requests.get(live_url, headers=headers, timeout=60)
        live_data = live_res.json()

        if not isinstance(live_data, list):
            print("[-] ไม่พบข้อมูลช่อง")
            return

        epg_url = f"{HOST}/xmltv.php?username={USERNAME}&password={PASSWORD}"
        count = 0

        with open(OUTPUT_LIVE_M3U, "w", encoding="utf-8") as f:
            f.write(f'#EXTM3U url-tvg="{epg_url}"\n')
            f.write(f'#EXTINF:-1 group-title="ℹ️ SYSTEM INFO",🕒 🟢 อัปเดตล่าสุด: {now_str} 🟢\n')
            f.write('http://clients.link/updated\n')

            for item in live_data:
                cat_id = str(item.get("category_id", ""))
                if cat_id in CATEGORY_MAPPING:
                    name = item.get("name", "Unknown")
                    stream_id = item.get("stream_id")
                    group_title = CATEGORY_MAPPING[cat_id]
                    container_extension = item.get("container_extension", "ts")
                    stream_url = f"{HOST}/live/{USERNAME}/{PASSWORD}/{stream_id}.{container_extension}"

                    f.write(f'#EXTINF:-1 tvg-id="{stream_id}" group-title="{group_title}",{name}\n')
                    f.write(f"{stream_url}\n")
                    count += 1

        print(f"[✔] บันทึกสำเร็จ {count} ช่อง")

    except Exception as e:
        print(f"[-] เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    get_live_via_api()
