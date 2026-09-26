"use client";
import { motion, useReducedMotion } from "motion/react";
export function ShiningText({text}: {text: string}) {
  const reduced = useReducedMotion();
  return <motion.span className="shining-text" initial={false}
    animate={reduced ? {backgroundPosition:"0% 0"} : {backgroundPosition:["200% 0","-200% 0"]}}
    transition={reduced ? {duration:0} : {repeat:Infinity,duration:2,ease:"linear"}}>{text}</motion.span>;
}
