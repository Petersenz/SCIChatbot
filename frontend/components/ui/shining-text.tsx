"use client";
import { motion, useReducedMotion } from "motion/react";
export function ShiningText({text}: {text: string}) {
  const reduced = useReducedMotion();
  return <motion.span className="shining-text" initial={{backgroundPosition:"100% 0"}}
    animate={reduced ? {backgroundPosition:"0% 0"} : {backgroundPosition:["100% 0","-100% 0"]}}
    transition={reduced ? {duration:0} : {repeat:Infinity,duration:2,ease:"linear"}}>{text}</motion.span>;
}
