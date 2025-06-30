const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');
const https = require('https');

const keyword = process.argv[2];
const index = parseInt(process.argv[3], 10);

// Thư mục lưu ảnh (nên trỏ đúng đến video-template-1/public/images)
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
      console.log(''); // In dòng trắng nếu không tìm được ảnh
      return;
    }

    const urlToDownload = imageUrls[0];
    const filename = `img${index + 1}.jpg`;
    const savePath = path.join(IMAGE_DIR, filename);

    // Tải ảnh bằng async promise
    await downloadImage(urlToDownload, savePath);
    console.log(`/images/${filename}`);
  } catch (err) {
    console.log('');
  }
})();

// Hàm tải ảnh async
function downloadImage(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, response => {
      response.pipe(file);
      file.on('finish', () => {
        file.close(resolve);
      });
    }).on('error', err => {
      fs.unlink(dest, () => reject(err));
    });
  });
}
