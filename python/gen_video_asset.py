# gen_video_asset.py

import os
import json
import shutil
import asyncio
import requests
from duckduckgo_search import DDGS
import edge_tts
from mutagen.mp3 import MP3
import time
import subprocess

BASE_PATH = "/workspaces/blog2video/video-template-1"
SCRIPT_PATH = "/workspaces/blog2video/python/script.json"
IMAGE_PATH = os.path.join(BASE_PATH, "public/images")
VOICE_PATH = os.path.join(BASE_PATH, "public/voices")
PROPS_PATH = os.path.join(BASE_PATH, "props.json")

def clean_previous_assets():
    if os.path.exists(IMAGE_PATH): shutil.rmtree(IMAGE_PATH); print(f"🧹 Xoá {IMAGE_PATH}")
    if os.path.exists(VOICE_PATH): shutil.rmtree(VOICE_PATH); print(f"🧹 Xoá {VOICE_PATH}")
    if os.path.exists(PROPS_PATH): os.remove(PROPS_PATH); print(f"🧹 Xoá {PROPS_PATH}")
    os.makedirs(IMAGE_PATH, exist_ok=True)
    os.makedirs(VOICE_PATH, exist_ok=True)
    print("📂 Đã tạo lại thư mục.")

def try_keywords_for_image(keyword_string: str, index: int) -> str | None:
    """
    Gọi script Node.js để tìm ảnh minh hoạ từ Bing theo từ khóa.
    """
    keywords = [k.strip() for k in keyword_string.replace("|", ",").split(",") if k.strip()]
    for keyword in keywords:
        print(f"    🔍 Thử tìm ảnh với từ khóa: {keyword}")
        try:
            result = subprocess.run(
                ["node", "../node/scrape_bing_images_v2.js", keyword, str(index)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30
            )
            image_path = result.stdout.strip()
            if image_path:
                print(f"    ✅ Đã lưu ảnh từ Bing: {image_path}")
                return image_path
        except Exception as e:
            print(f"    ⚠️ Lỗi Node.js: {e}")
        print(f"    ❌ Không tìm được ảnh cho: {keyword}")
    return None

async def _speak_with_edge_tts(text: str, output_path: str):
    voice = "vi-VN-HoaiMyNeural"
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)

def create_voice(text: str, index: int) -> tuple[str | None, str | None]:
    filename = f"part{index+1}.mp3"
    path = os.path.join(VOICE_PATH, filename)
    try:
        loop = asyncio.get_event_loop_policy().new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_speak_with_edge_tts(text, path))
        loop.close()
        audio = MP3(path)
        duration = round(audio.info.length, 2)
        print(f"    🎤 Đã tạo voice: {filename} ({duration}s)")
        return f"/voices/{filename}", str(duration)
    except Exception as e:
        print(f"    ❌ Lỗi tạo voice: {e}")
        return None, None

if __name__ == '__main__':
    print("♻️ Chuẩn bị thư mục...")
    clean_previous_assets()

    if not os.path.exists(SCRIPT_PATH):
        print(f"❌ Không tìm thấy {SCRIPT_PATH}. Hãy chạy gen_script.py trước.")
        exit()

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenes = data.get("scenes", [])
    if not scenes:
        print("❌ script.json không có scenes.")
        exit()

    props = {"slides": []}

    for i, scene in enumerate(scenes):
        print(f"\n🎬 Xử lý cảnh {i+1}")
        title = scene.get("title", f"Cảnh {i+1}")
        overlay = scene.get("overlay_text", "")
        script = scene.get("script_sentence", "")
        keyword = scene.get("image_keywords", "")
        if not script or not keyword:
            print("    ⚠️ Cảnh thiếu dữ liệu cần thiết.")
            continue

        voice_path, duration = create_voice(script, i)
        image_path = try_keywords_for_image(keyword, i)

        if voice_path and image_path:
            props["slides"].append({
                "text": f"{title.strip()}|{overlay.strip()}",
                "image": image_path,
                "voice": voice_path,
                "duration": duration
            })
        else:
            print("    ❌ Bỏ qua cảnh này do thiếu voice hoặc ảnh.")

    if props["slides"]:
        with open(PROPS_PATH, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Đã tạo props.json với {len(props['slides'])} slide.")
    else:
        print("❌ Không có slide nào được tạo.")
