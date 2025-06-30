const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');
const https = require('https');
const sharp = require('sharp');

const keyword = process.argv[2];
const index = parseInt(process.argv[3], 10);

const IMAGE_DIR = path.join(__dirname, '../video-template-1/public/images');

if (!keyword || isNaN(index)) {
  console.error('❌ Thiếu keyword hoặc index');
  process.exit(1);
}

if (!fs.existsSync(IMAGE_DIR)) {
  fs.mkdirSync(IMAGE_DIR, { recursive: true });
}

(async () => {
  const query = encodeURIComponent(keyword);
  const url = `https://www.bing.com/images/search?q=${query}&form=HDRSC2&first=1&tsc=ImageHoverTitle`;

  try {
    const { data: html } = await axios.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
      },
    });

    const $ = cheerio.load(html);
    const imageUrls = [];

    $('a.iusc').each((_, el) => {
      try {
        const meta = JSON.parse($(el).attr('m'));
        if (meta?.murl) imageUrls.push(meta.murl);
      } catch (e) {}
    });

    if (imageUrls.length === 0) {
      console.log('');
      return;
    }

    const filename = `img${index + 1}.jpg`;
    const savePath = path.join(IMAGE_DIR, filename);

    for (let i = 0; i < imageUrls.length; i++) {
      const url = imageUrls[i];
      console.error(`🟡 Thử ảnh ${i + 1}/${imageUrls.length}: ${url}`);

      try {
        await downloadImage(url, savePath);

        const valid = await waitForValidImageWithSharp(savePath);
        if (valid) {
          console.error(`✅ Ảnh hợp lệ: ${filename}`);
          console.log(`/images/${filename}`); // 👉 duy nhất dòng này được stdout
          return;
        } else {
          if (fs.existsSync(savePath)) fs.unlinkSync(savePath);
          console.error(`❌ Ảnh không hợp lệ (sharp fail): ${url}`);
        }
      } catch (e) {
        if (fs.existsSync(savePath)) fs.unlinkSync(savePath);
        console.error(`⚠️ Lỗi tải ảnh: ${url}`);
        console.error(`   ↳ ${e.message}`);
      }
    }

    console.log('');
  } catch (err) {
    console.error(`❌ Lỗi tải trang Bing: ${err.message}`);
    console.log('');
  }
})();

function downloadImage(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, response => {
      if (response.statusCode !== 200) {
        return reject(new Error(`HTTP ${response.statusCode}`));
      }

      response.pipe(file);
      file.on('finish', () => {
        file.close(() => {
          setTimeout(() => resolve(), 100); // Đợi ghi file hoàn tất
        });
      });
    }).on('error', err => {
      fs.unlink(dest, () => reject(err));
    });
  });
}

async function waitForValidImageWithSharp(filepath, maxRetries = 5) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await sharp(filepath).metadata();
      return true;
    } catch (err) {
      await new Promise(res => setTimeout(res, 300));
    }
  }
  return false;
}
