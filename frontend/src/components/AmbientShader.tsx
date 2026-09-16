import { GrainGradient } from "@paper-design/shaders-react";
import { useReducedMotion } from "motion/react";

/** Decorative only: all portfolio data remains rendered independently of WebGL. */
export function AmbientShader() {
  const reduceMotion = useReducedMotion();

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <GrainGradient
        width="100%"
        height="100%"
        colors={["#ebf6e9", "#eff6ec", "#e8f1f6", "#fbf7eb"]}
        colorBack="#f8faf7"
        softness={0.92}
        intensity={0.13}
        noise={0.1}
        shape="corners"
        speed={reduceMotion ? 0 : 0.08}
        scale={1.1}
        minPixelRatio={1}
        maxPixelCount={700000}
      />
      <div className="absolute inset-0 bg-gradient-to-r from-white/35 via-white/5 to-white/25" />
    </div>
  );
}
