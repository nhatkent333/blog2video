import os
import json
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import shutil
import asyncio
import edge_tts
from mutagen.mp3 import MP3

# --- Cấu hình ---
OPENROUTER_API_KEY = "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"
BLOG_URL = "https://lifestyle.znews.vn/nghien-pickleball-choi-sao-de-khong-vao-vien-post1563629.html"

BASE_PATH = "/workspaces/blog2video/video-template-1"
IMAGE_PATH = os.path.join(BASE_PATH, "public/images")
VOICE_PATH = os.path.join(BASE_PATH, "public/voices")
PROPS_PATH = os.path.join(BASE_PATH, "props.json")

# --- XÓA DỮ LIỆU CŨ ---
def clean_previous_assets():
    if os.path.exists(IMAGE_PATH):
        shutil.rmtree(IMAGE_PATH)
        print("🧹 Đã xoá thư mục public/images/")
    if os.path.exists(VOICE_PATH):
        shutil.rmtree(VOICE_PATH)
        print("🧹 Đã xoá thư mục public/voices/")
    if os.path.exists(PROPS_PATH):
        os.remove(PROPS_PATH)
        print("🧹 Đã xoá props.json")

clean_previous_assets()

os.makedirs(IMAGE_PATH, exist_ok=True)
os.makedirs(VOICE_PATH, exist_ok=True)

# --- Hàm phụ trợ ---
def get_blog_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        main = soup.article or soup.main or soup.body
        paragraphs = main.find_all('p')
        return ' '.join(p.get_text() for p in paragraphs)
    except:
        return None

def generate_video_script_with_gemma(api_key, content):
    prompt = f"""
    Từ nội dung bài viết sau, hãy chia thành 5 cảnh cho một video ngắn.

    Mỗi cảnh gồm:
    - title: tiêu đề ngắn (3–5 từ)
    - script_sentence: câu thoại giọng đọc
    - overlay_text: dòng chữ nổi bật ngắn
    - image_keyword: từ khóa tiếng Anh để tìm ảnh minh hoạ

    Trả lời BẮT BUỘC bằng JSON object như sau:
    {{
      "scenes": [
        {{
          "title": "...",
          "script_sentence": "...",
          "overlay_text": "...",
          "image_keyword": "..."
        }}
      ]
    }}

    Nội dung bài viết:
    {content[:3000]}
    """
    payload = {
        "model": "google/gemma-3-27b-it:free",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    result_text = response.json()['choices'][0]['message']['content']
    if '```json' in result_text:
        result_text = result_text.split('```json\n')[1].split('```')[0]
    return json.loads(result_text)

def download_image(keyword, index):
    with DDGS() as ddgs:
        for img in ddgs.images(keyword):
            try:
                url = img.get("image")
                res = requests.get(url, timeout=10)
                filename = f"img{index+1}.jpg"
                path = os.path.join(IMAGE_PATH, filename)
                with open(path, 'wb') as f:
                    f.write(res.content)
                return f"/images/{filename}"
            except:
                continue
    return None

# --- Giọng đọc HoaiMy qua edge-tts ---
def create_voice(text, index):
    filename = f"part{index+1}.mp3"
    path = os.path.join(VOICE_PATH, filename)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_speak_with_edge_tts(text, path))

        audio = MP3(path)
        duration = round(audio.info.length, 2)
        return f"/voices/{filename}", str(duration)
    except Exception as e:
        print(f"❌ Lỗi tạo voice: {e}")
        return None, None

async def _speak_with_edge_tts(text, output_path):
    voice = "vi-VN-HoaiMyNeural"
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)

# --- Chạy chính ---
if "sk-" not in OPENROUTER_API_KEY:
    print("❌ Thiếu API key.")
    exit()

blog = get_blog_content(BLOG_URL)
if not blog:
    print("❌ Không lấy được nội dung blog.")
    exit()

data = generate_video_script_with_gemma(OPENROUTER_API_KEY, blog)
if not data or "scenes" not in data:
    print("❌ Lỗi khi tạo kịch bản.")
    exit()

props = {"slides": []}
for i, scene in enumerate(data["scenes"]):
    print(f"🎬 Cảnh {i+1}")
    title = scene.get("title", "Tiêu đề")
    overlay = scene.get("overlay_text", "Mô tả")
    script = scene.get("script_sentence", "")
    keyword = scene.get("image_keyword", "")

    text_combined = f"{title.strip()}|{overlay.strip()}"

    voice_path, duration = create_voice(script, i)
    image_path = download_image(keyword, i)

    if voice_path and image_path:
        props["slides"].append({
            "text": text_combined,
            "image": image_path,
            "voice": voice_path,
            "duration": duration
        })

if props["slides"]:
    with open(PROPS_PATH, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)
    print("✅ Đã tạo props.json tại:", PROPS_PATH)
else:
    print("❌ Không tạo được slide nào.")
