// src/templates/ModernNewsfeed/index.tsx
import { Sequence, Video, Audio, staticFile, useVideoConfig } from 'remotion';
import { Slide } from './Slide';
import { ProgressBar } from '../../components/ProgressBar';

interface ModernNewsfeedTemplateProps {
  slides: {
    text: string;
    image: string;
    voice: string;
    duration: string; // Đảm bảo duration có trong interface
  }[];
}

export const ModernNewsfeedTemplate: React.FC<ModernNewsfeedTemplateProps> = ({ slides }) => {
  const { fps } = useVideoConfig();

  let currentFromFrame = 0;

  return (
    <div style={{ flex: 1 }}>
      {/* Background Video */}
      <Video
        src={staticFile('/assets/grid-bg-video.mp4')}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          zIndex: -1,
        }}
        loop
      />

      {/* Background Music */}
      <Audio
        src={staticFile('/assets/mbn-music-bg.mp3')}
        loop
        volume={0.2}
      />

      {slides.map((slide, index) => {
        // Chuyển đổi duration từ giây (string) sang số frame
        // Thêm kiểm tra isNaN và giá trị mặc định (ví dụ 7 giây)
        const parsedDurationSeconds = parseInt(slide.duration, 10);
        const slideDurationSeconds = isNaN(parsedDurationSeconds) ? 7 : parsedDurationSeconds; // Mặc định 7 giây nếu duration không hợp lệ

        const slideDurationInFrames = slideDurationSeconds * fps;

        // Có thể thêm cảnh báo để gỡ lỗi nếu duration không hợp lệ
        if (isNaN(parsedDurationSeconds)) {
            console.warn(`Cảnh báo: Duration không hợp lệ cho slide ${index}:`, slide);
            console.warn(`Sử dụng thời lượng mặc định ${7} giây cho slide này.`);
        }

        const fromFrame = currentFromFrame;

        currentFromFrame += slideDurationInFrames; // Cập nhật frame bắt đầu cho sequence tiếp theo

        return (
          <Sequence
            key={index}
            from={fromFrame}
            durationInFrames={slideDurationInFrames} // Sử dụng duration đã được kiểm tra
          >
            <Slide text={slide.text} image={slide.image} voice={slide.voice} />
          </Sequence>
        );
      })}
      <ProgressBar />
    </div>
  );
};