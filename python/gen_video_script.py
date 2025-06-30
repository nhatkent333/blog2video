# gen_script.py

import os
import json
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

GOOGLE_API_KEY = "YOUR_GOOGLE_GEMINI_API_KEY"  # Thay bằng API thật
BLOG_URL = "https://lifestyle.znews.vn/dau-hieu-nhan-biet-tre-thong-minh-tu-nho-post1303366.html"
SCRIPT_PATH = "/workspaces/blog2video/python/script.json"

def get_blog_content(url: str) -> str | None:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        main_content = soup.find('article') or soup.find('main') or soup.find(class_='content-detail') or soup.body
        paragraphs = main_content.find_all('p') if main_content else []
        cleaned_paragraphs = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
        return ' '.join(cleaned_paragraphs)
    except Exception as e:
        print(f"❌ Lỗi lấy nội dung blog: {e}")
        return None

def generate_video_script_with_gemma(api_key: str, content: str, output_path: str = SCRIPT_PATH) -> bool:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemma-3-27b-it')
    prompt = f"""
Bạn là một chuyên gia tạo nội dung video từ bài blog.

Từ nội dung bài viết sau, nhiệm vụ của bạn là phân tích nội dung blog bên dưới và chuyển đổi thành một danh sách các cảnh (scenes) theo cấu trúc JSON.

Yêu cầu:

1. Phân chia nội dung thành các scene hợp lý, đảm bảo bao phủ toàn bộ ý chính trong blog.
2. Mỗi scene gồm:
    - "title": tiêu đề ngắn gọn (tối đa 10 từ).
    - "script_sentence": câu thoại dễ hiểu (tối đa 30 từ).
    - "overlay_text": dòng chữ nổi bật (tối đa 15 từ).
    - "image_keyword": từ khóa tiếng Anh minh hoạ (tối đa 5 từ).

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
    try:
        response = model.generate_content(prompt, generation_config={"temperature": 0.4})
        result_text = response.text
        if '```json' in result_text:
            result_text = result_text.split('```json\n')[1].split('```')[0]
        video_script_data = json.loads(result_text)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(video_script_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Lỗi tạo/sử lý script: {e}")
        return False

if __name__ == '__main__':
    if GOOGLE_API_KEY == "YOUR_GOOGLE_GEMINI_API_KEY":
        print("❌ Bạn chưa cấu hình API Key.")
        exit()

    print(f"📥 Lấy nội dung từ: {BLOG_URL}")
    blog_content = get_blog_content(BLOG_URL)
    if not blog_content:
        print("❌ Không lấy được nội dung.")
        exit()

    print("⚙️ Đang tạo script.json bằng Gemini...")
    if generate_video_script_with_gemma(GOOGLE_API_KEY, blog_content):
        print(f"✅ Đã tạo {SCRIPT_PATH}")
    else:
        print("❌ Thất bại khi tạo script.")
