import { AbsoluteFill, Img, interpolate, useCurrentFrame, staticFile, Audio, Easing } from 'remotion';
import React from 'react';

interface SlideProps {
  text: string;
  image: string;
  voice: string;
  duration: string;
}

// 🔧 Shadow dùng lại
const shadowStyle = `
  0px 3px 6px rgba(0,0,0,0.16),
  0px 3px 6px rgba(0,0,0,0.23)
`;

const sceneContainer: React.CSSProperties = {
  flex: 1,
  background: 'rgba(255, 0, 0, 0.3)',
};

const layout: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100%',
  padding: '80px',
  boxSizing: 'border-box',
  gap: 40, // khoảng cách giữa các khối
};

const imageContainer: React.CSSProperties = {
  width: 1000,
  height: 600,
  overflow: 'hidden',
  borderRadius: 20,
  position: 'relative',
  boxShadow: shadowStyle,
};

const titleStyle: React.CSSProperties = {
  fontSize: 85,
  fontWeight: 900,
  lineHeight: 1.2,
  textAlign: 'center',
  color: 'white',
  textShadow: '-1px -1px 1px rgba(255,255,255,.1), 1px 1px 1px rgba(0,0,0,.5)',
  fontFamily: 'Roboto',
};

const descriptionStyle: React.CSSProperties = {
  fontSize: 40,
  fontWeight: 400,
  lineHeight: 1.6,
  color: 'white',
  fontFamily: 'Roboto',
  maxWidth: 1000,
  textAlign: 'center',
};

const imageStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
  objectFit: 'cover',
  position: 'absolute',
  top: 0,
  left: 0,
};

export const Slide: React.FC<SlideProps> = ({ text, image, voice, duration }) => {
  const frame = useCurrentFrame();
  const [title, description] = text.split('|');

  const fps = 30;
  const voiceDurationInSeconds = parseFloat(duration);
  const imageDurationInSeconds = voiceDurationInSeconds + 1; // ⏱ thêm 1 giây cho hình
  const imageDurationFrames = Math.floor(imageDurationInSeconds * fps);

  // Animations
  const titleY = interpolate(frame, [10, 30], [100, 0], { extrapolateRight: 'clamp' });
  const titleOpacity = interpolate(frame, [10, 30], [0, 1], { extrapolateRight: 'clamp' });

  const containerOpacity = interpolate(frame, [30, 50], [0, 1], { extrapolateRight: 'clamp' });

  const descY = interpolate(frame, [50, 70], [100, 0], { extrapolateRight: 'clamp' });
  const descOpacity = interpolate(frame, [50, 70], [0, 1], { extrapolateRight: 'clamp' });

  // Ken Burns Effect
  const panZoomEndFrame = Math.max(60, imageDurationFrames - 15);
  const panZoomProgress = interpolate(frame, [30, panZoomEndFrame], [0, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.ease),
  });

  const imageScale = interpolate(panZoomProgress, [0, 1], [1.1, 1.25]);
  const imageTranslateX = interpolate(panZoomProgress, [0, 1], [-10, 10]);
  const imageTranslateY = interpolate(panZoomProgress, [0, 1], [-10, 10]);

  const imageFadeIn = interpolate(frame, [30, 50], [0, 1], { extrapolateRight: 'clamp' });
  const imageFadeOut = interpolate(
    frame,
    [imageDurationFrames - 10, imageDurationFrames],
    [1, 0],
    { extrapolateLeft: 'clamp' }
  );

  const finalImageOpacity = imageFadeIn * imageFadeOut;


  return (
    <AbsoluteFill style={sceneContainer}>
      <div style={layout}>
        <div style={{ overflow: 'hidden' }}>
          <h1 style={{ ...titleStyle, transform: `translateY(${titleY}%)`, opacity: titleOpacity }}>
            {title}
          </h1>
        </div>

        <div style={{ ...imageContainer, opacity: containerOpacity }}>
          <Img
            src={staticFile(image)}
            style={{
              ...imageStyle,
              opacity: finalImageOpacity,
              transform: `scale(${imageScale}) translate(${imageTranslateX}px, ${imageTranslateY}px)`,
            }}
          />
        </div>

        <div style={{ overflow: 'hidden' }}>
          <p style={{ ...descriptionStyle, transform: `translateY(${descY}%)`, opacity: descOpacity }}>
            {description}
          </p>
        </div>
      </div>

      <Audio src={staticFile(voice)} />
    </AbsoluteFill>
  );
};
