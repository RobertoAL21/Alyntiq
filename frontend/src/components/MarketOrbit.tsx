import { motion, useReducedMotion } from "motion/react";

import marketOrbit from "../assets/market-orbit-3d.png";

export function MarketOrbit() {
  const reduceMotion = useReducedMotion();

  return (
    <div className="relative mx-auto aspect-square w-full max-w-[490px]" aria-label="3D market signal sculpture">
      <motion.div
        className="absolute inset-[8%] rounded-full border border-[#b6dac7]/60"
        animate={reduceMotion ? undefined : { rotate: 360 }}
        transition={{ duration: 32, repeat: Infinity, ease: "linear" }}
        aria-hidden="true"
      >
        <span className="absolute -top-1 left-1/2 h-2.5 w-2.5 rounded-full bg-[#32aa76] shadow-[0_0_0_5px_rgba(50,170,118,0.12)]" />
      </motion.div>
      <motion.img
        src={marketOrbit}
        alt="A translucent 3D market signal sculpture with candlesticks and a rising price curve"
        className="relative z-[1] h-full w-full object-contain drop-shadow-[0_30px_28px_rgba(11,48,37,0.18)]"
        animate={reduceMotion ? undefined : { y: [0, -10, 0], rotate: [-1, 1, -1] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      />
    </div>
  );
}
