import os
import json
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import shutil
import asyncio
import edge_tts
from mutagen.mp3 import MP3

# Import thư viện Google Generative AI
import google.generativeai as genai

# --- Cấu hình ---
GOOGLE_API_KEY = "AIzaSyCraYtKs_zidiPBpiH00WxqY25Z5fxoKrQ" # THAY THẾ BẰNG API KEY CỦA BẠN

BLOG_URL = "https://lifestyle.znews.vn/dau-hieu-nhan-biet-tre-thong-minh-tu-nho-post1303366.html"

# Sử dụng os.path.dirname(__file__) để đảm bảo BASE_PATH tương đối với file script
BASE_PATH = "/workspaces/blog2video/video-template-1"
IMAGE_PATH = os.path.join(BASE_PATH, "public/images")
VOICE_PATH = os.path.join(BASE_PATH, "public/voices")
PROPS_PATH = os.path.join(BASE_PATH, "props.json")

# --- XÓA DỮ LIỆU CŨ ---
def clean_previous_assets():
    """Xóa các thư mục và tệp tin tạo ra từ lần chạy trước."""
    if os.path.exists(IMAGE_PATH):
        shutil.rmtree(IMAGE_PATH)
        print(f"🧹 Đã xoá thư mục {IMAGE_PATH}")
    if os.path.exists(VOICE_PATH):
        shutil.rmtree(VOICE_PATH)
        print(f"🧹 Đã xoá thư mục {VOICE_PATH}")
    if os.path.exists(PROPS_PATH):
        os.remove(PROPS_PATH)
        print(f"🧹 Đã xoá {PROPS_PATH}")

clean_previous_assets()

# Tạo lại các thư mục cần thiết
os.makedirs(IMAGE_PATH, exist_ok=True)
os.makedirs(VOICE_PATH, exist_ok=True)
print(" thư mục đã được tạo lại.")

# --- Hàm phụ trợ ---
def get_blog_content(url: str) -> str | None:
    """
    Lấy nội dung văn bản từ một URL blog.
    Args:
        url (str): URL của bài blog.
    Returns:
        str | None: Nội dung bài blog dưới dạng chuỗi hoặc None nếu không lấy được.
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()  # Nâng Exception cho các mã trạng thái lỗi (4xx hoặc 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Cố gắng tìm phần nội dung chính của bài viết
        # Thường là trong thẻ <article>, <main>, hoặc các thẻ có class cụ thể như 'content-detail'
        main_content = soup.find('article') or soup.find('main') or soup.find(class_='content-detail')

        if not main_content:
            # Fallback: nếu không tìm thấy thẻ chính, thử tìm tất cả các đoạn văn trong body
            main_content = soup.body

        if main_content:
            paragraphs = main_content.find_all('p')
            # Lọc bỏ các đoạn văn rỗng hoặc quá ngắn
            cleaned_paragraphs = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
            return ' '.join(cleaned_paragraphs)
        else:
            print(f"❌ Không tìm thấy nội dung bài viết chính trên {url}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi khi yêu cầu URL {url}: {e}")
        return None
    except Exception as e:
        print(f"❌ Lỗi khi phân tích cú pháp HTML từ {url}: {e}")
        return None

def generate_video_script_with_gemma(api_key: str, content: str) -> dict | None:
    """
    Tạo kịch bản video từ nội dung bài blog bằng Google Gemini API (Gemma).

    Args:
        api_key (str): Khóa API của Google Gemini.
        content (str): Nội dung bài blog cần chuyển đổi thành kịch bản.

    Returns:
        dict | None: Một đối tượng JSON chứa danh sách các cảnh (scenes) cho video
                     hoặc None nếu có lỗi xảy ra.
    """
    # Cấu hình API key cho thư viện google.generativeai
    genai.configure(api_key=api_key)

    # Khởi tạo mô hình Gemini Pro.
    # Đây là mô hình tương đương phổ biến nhất và dễ truy cập nhất
    # cho các tác vụ tạo văn bản thông qua API công khai của Google.
    model = genai.GenerativeModel('gemma-3-27b-it') 

    prompt = f"""
    Bạn là một chuyên gia tạo nội dung video từ bài blog.

    Từ nội dung bài viết sau, nhiệm vụ của bạn là phân tích nội dung blog bên dưới và chuyển đổi thành một danh sách các cảnh (scenes) theo cấu trúc JSON.

    Yêu cầu:

    1. Phân chia nội dung thành các scene hợp lý, đảm bảo bao phủ toàn bộ ý chính trong blog.
    2. Mỗi scene gồm:
        - "title": tiêu đề ngắn gọn, gợi nhớ nội dung của cảnh đó (tối đa 10 từ).
        - "script_sentence": câu thoại có thể đọc to (nói tự nhiên, súc tích, dễ hiểu, tối đa 30 từ).
        - "overlay_text": dòng chữ nổi bật xuất hiện trên màn hình để nhấn mạnh ý chính hoặc thông tin quan trọng (tối đa 15 từ).
        - "image_keyword": từ khóa bằng tiếng Anh, dễ tìm ảnh minh hoạ phù hợp cho cảnh (ví dụ: "busy street in Tokyo", "healthy Vietnamese food", "futuristic city skyline", v.v., tối đa 5 từ).

    3. Tối ưu nội dung để video dễ hiểu, thu hút người xem, và có tính viral.

    Trả lời BẮT BUỘC bằng JSON object như sau:
    {{
      "scenes": [
        {{
          "title": "...",
          "script_sentence": "...",
          "overlay_text": "...",
          "image_keyword": "..."
        }},
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

    try:
        # Gửi yêu cầu tới API của Google Gemini
        # Thiết lập nhiệt độ (temperature) để kiểm soát độ sáng tạo của mô hình.
        # Giá trị 0.4 sẽ cho kết quả khá ổn định và phù hợp với yêu cầu cấu trúc JSON.
        response = model.generate_content(
            prompt, 
            generation_config={"temperature": 0.4}
        )
        
        # Lấy nội dung văn bản từ phản hồi của mô hình
        result_text = response.text

        # Mô hình đôi khi bọc JSON trong các dấu backtick (```json ... ```),
        # đoạn code này sẽ loại bỏ chúng để có chuỗi JSON hợp lệ.
        if '```json' in result_text:
            result_text = result_text.split('```json\n')[1].split('```')[0]
        
        # Chuyển đổi chuỗi JSON thành đối tượng Python dictionary
        return json.loads(result_text)

    except Exception as e:
        print(f"❌ Lỗi khi gọi Google Gemini API hoặc xử lý phản hồi: {e}")
        return None

def download_image(keyword: str, index: int) -> str | None:
    """
    Tìm kiếm và tải xuống hình ảnh liên quan đến từ khóa.
    Args:
        keyword (str): Từ khóa để tìm kiếm hình ảnh.
        index (int): Chỉ số của hình ảnh để đặt tên file.
    Returns:
        str | None: Đường dẫn tương đối của hình ảnh đã tải xuống hoặc None nếu không tìm được.
    """
    print(f"    🔍 Đang tìm ảnh cho từ khóa: '{keyword}'...")
    with DDGS() as ddgs:
        # Thử tìm kiếm 5 hình ảnh đầu tiên
        for i, img in enumerate(ddgs.images(keyword, safesearch='off', size='large')):
            if i >= 5: # Giới hạn số lần thử để tránh lãng phí thời gian
                break
            try:
                url = img.get("image")
                if not url: continue

                # Tải ảnh với timeout
                res = requests.get(url, timeout=10, stream=True)
                res.raise_for_status() # Kiểm tra lỗi HTTP

                # Kiểm tra Content-Type để đảm bảo là ảnh
                if 'image' not in res.headers.get('Content-Type', ''):
                    continue

                filename = f"img{index+1}.jpg"
                path = os.path.join(IMAGE_PATH, filename)
                with open(path, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"    ✅ Tải ảnh thành công: {filename}")
                return f"/images/{filename}"
            except requests.exceptions.RequestException as e:
                print(f"    ⚠️ Lỗi khi tải ảnh từ {url}: {e}")
                continue
            except Exception as e:
                print(f"    ⚠️ Lỗi không xác định khi xử lý ảnh: {e}")
                continue
    print(f"    ❌ Không tìm được ảnh phù hợp cho từ khóa: '{keyword}'")
    return None

def create_voice(text: str, index: int) -> tuple[str | None, str | None]:
    """
    Tạo file âm thanh từ văn bản sử dụng Edge TTS và trả về đường dẫn, thời lượng.
    Args:
        text (str): Văn bản cần chuyển thành giọng nói.
        index (int): Chỉ số của cảnh để đặt tên file âm thanh.
    Returns:
        tuple[str | None, str | None]: Đường dẫn tương đối của file âm thanh và thời lượng (string)
                                        hoặc (None, None) nếu có lỗi.
    """
    filename = f"part{index+1}.mp3"
    path = os.path.join(VOICE_PATH, filename)
    try:
        # Edge TTS cần asyncio, đảm bảo loop chạy đúng cách
        loop = asyncio.get_event_loop_policy().new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(_speak_with_edge_tts(text, path))
        loop.close() # Đóng loop sau khi hoàn thành

        audio = MP3(path)
        duration = round(audio.info.length, 2)
        print(f"    🎤 Tạo voice thành công: {filename} ({duration}s)")
        return f"/voices/{filename}", str(duration)
    except Exception as e:
        print(f"    ❌ Lỗi khi tạo voice cho cảnh {index+1}: {e}")
        return None, None

async def _speak_with_edge_tts(text: str, output_path: str):
    """Hàm bất đồng bộ để gọi Edge TTS."""
    voice = "vi-VN-HoaiMyNeural" # Giọng đọc tiếng Việt: HoaiMy
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)

# --- Chạy chính ---
if __name__ == '__main__':
    if GOOGLE_API_KEY == "YOUR_GOOGLE_GEMINI_API_KEY" or not GOOGLE_API_KEY:
        print("❌ Lỗi: Vui lòng thay thế 'YOUR_GOOGLE_GEMINI_API_KEY' bằng API Key của Google Gemini.")
        print("Bạn có thể lấy API Key từ [https://ai.google.dev/](https://ai.google.dev/) hoặc Google Cloud Console.")
        exit()

    print(f"Đang lấy nội dung từ blog: {BLOG_URL}...")
    blog_content = get_blog_content(BLOG_URL)
    if not blog_content:
        print("❌ Không lấy được nội dung blog. Vui lòng kiểm tra lại URL hoặc kết nối mạng.")
        exit()
    print("✅ Đã lấy nội dung blog.")

    print("\nĐang tạo kịch bản video bằng Google Gemini API...")
    video_script_data = generate_video_script_with_gemma(GOOGLE_API_KEY, blog_content)
    if not video_script_data or "scenes" not in video_script_data or not video_script_data["scenes"]:
        print("❌ Lỗi khi tạo kịch bản video hoặc kịch bản trống.")
        exit()
    print("✅ Đã tạo kịch bản video.")

    props = {"slides": []}
    for i, scene in enumerate(video_script_data["scenes"]):
        print(f"\n🎬 Xử lý Cảnh {i+1}:")
        title = scene.get("title", f"Cảnh {i+1}")
        overlay = scene.get("overlay_text", "Không có overlay")
        script = scene.get("script_sentence", "")
        keyword = scene.get("image_keyword", "")

        # Kiểm tra dữ liệu từ mô hình có hợp lệ không
        if not script or not keyword:
            print(f"    ⚠️ Cảnh {i+1} thiếu 'script_sentence' hoặc 'image_keyword'. Bỏ qua cảnh này.")
            continue

        text_combined = f"{title.strip()}|{overlay.strip()}"

        # Tạo giọng đọc
        voice_path, duration = create_voice(script, i)
        
        # Tải ảnh
        image_path = download_image(keyword, i)

        if voice_path and image_path:
            props["slides"].append({
                "text": text_combined,
                "image": image_path,
                "voice": voice_path,
                "duration": duration
            })
        else:
            print(f"    ❌ Bỏ qua Cảnh {i+1} do không tạo được voice hoặc tải ảnh.")

    if props["slides"]:
        with open(PROPS_PATH, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Đã tạo props.json thành công tại: {PROPS_PATH}")
        print(f"Tổng số cảnh được tạo: {len(props['slides'])}")
    else:
        print("❌ Không tạo được slide nào vào props.json.")