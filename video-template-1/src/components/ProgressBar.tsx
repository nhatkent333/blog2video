import { useCurrentFrame, useVideoConfig } from "remotion";
import React from "react";

export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const progress = frame / (durationInFrames - 1);

  return (
    <div
      style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        width: "100%",
        height: "10px",
        backgroundColor: "rgba(255, 255, 255, 0.2)",
      }}
    >
      <div
        style={{
          height: "100%",
          width: `${progress * 100}%`,
          backgroundColor: "#4290f5", // Màu xanh dương hiện đại
        }}
      />
    </div>
  );
};