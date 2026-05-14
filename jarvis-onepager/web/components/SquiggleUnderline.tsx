import React from 'react';

export default function SquiggleUnderline({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 800 20"
      preserveAspectRatio="none"
      className={className}
      style={{ display: 'block', ...style }}
    >
      <path
        d="M2,14 C40,6 80,18 140,12 C200,6 240,18 300,11 C360,4 400,17 460,10 C520,3 560,16 620,9 C680,2 720,15 798,8"
        stroke="var(--accent)"
        strokeWidth="1.5"
        strokeOpacity="0.9"
        fill="none"
        strokeLinecap="round"
      />
    </svg>
  );
}
