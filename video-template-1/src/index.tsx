// src/index.tsx (Nội dung của file Root.tsx cũ)
import { Composition, registerRoot } from 'remotion';
import { ModernNewsfeedTemplate } from './templates/ModernNewsfeed/index';
// Đảm bảo đường dẫn này đúng nếu props.json nằm ở thư mục gốc của dự án
import slidesData from '../props.json'; // Hoặc './props.json' nếu props.json cùng cấp với index.tsx

export const RemotionRoot: React.FC = () => {
  const fps = 30; // Định nghĩa fps ở đây, Remotion thường dùng 30fps

  // Đảm bảo slidesData.slides là một mảng, nếu không sẽ là mảng rỗng để tránh lỗi
  const slides = slidesData?.slides || [];

  // Tính toán tổng thời lượng video dựa trên duration của mỗi slide
  const totalDurationInFrames = slides.reduce((sum, slide) => {
    // Chuyển đổi duration sang số nguyên, sử dụng radix 10
    // Nếu parseInt trả về NaN (ví dụ: slide.duration không tồn tại hoặc không phải số),
    // sẽ sử dụng giá trị mặc định là 7 (giây) để tránh lỗi.
    const durationSeconds = parseInt(slide.duration, 10);
    const validDurationSeconds = isNaN(durationSeconds) ? 7 : durationSeconds; // Mặc định 7 giây nếu không hợp lệ

    // Có thể thêm console.warn để phát hiện nếu có duration không hợp lệ trong props.json
    if (isNaN(durationSeconds)) {
      console.warn(`Cảnh báo: Duration không hợp lệ cho slide:`, slide);
      console.warn(`Sử dụng thời lượng mặc định ${7} giây.`);
    }

    return sum + (validDurationSeconds * fps);
  }, 0);

  // (Tùy chọn) In ra tổng thời lượng để kiểm tra trong console
  console.log('Tổng thời lượng video (frames):', totalDurationInFrames);

  return (
    <>
      <Composition
        id="ModernNewsfeed"
        component={ModernNewsfeedTemplate}
        // Sử dụng tổng thời lượng đã tính toán
        durationInFrames={totalDurationInFrames}
        fps={fps} // Sử dụng fps đã định nghĩa
        width={1920}
        height={1080}
        // Truyền toàn bộ mảng slides từ props.json vào component ModernNewsfeedTemplate
        defaultProps={{ slides: slides }}
      />
    </>
  );
};

// Lệnh này sẽ đăng ký component RemotionRoot của bạn với Remotion
registerRoot(RemotionRoot);