import type { ReactNode } from 'react';
import { answerBlocks } from './answer-format';
export function AnswerContent({text,renderInline}:{text:string;renderInline:(text:string)=>ReactNode}) {
  return <div className="bot-message">{answerBlocks(text).map((block,i)=>{
    if(block.kind==='heading')return <h3 className="answer-heading" key={i}>{renderInline(block.lines[0])}</h3>;
    if(block.kind==='paragraph')return <p className="answer-paragraph" key={i}>{block.lines.map((line,j)=><span key={j}>{j>0&&<br/>}{renderInline(line)}</span>)}</p>;
    // Cite one list as a group instead of repeating the same chip in every row.
    const refs=[...new Set(block.lines.flatMap(line=>line.match(/\[\d+\]/g)||[]))];
    const citedRows=block.lines.map(line=>[...new Set(line.match(/\[\d+\]/g)||[])].join(' ')).filter(Boolean);
    const groupRefs=citedRows.length>0 && citedRows.every(row=>row===citedRows[0]);
    const Tag=block.kind==='ol'?'ol':'ul';
    return <div className="answer-list-group" key={i}><Tag className="answer-list" start={block.kind==='ol'?block.start:undefined}>
      {block.lines.map((line,j)=><li key={j}>{renderInline(groupRefs?line.replace(/\[\d+\]/g,''):line)}</li>)}
    </Tag>{groupRefs&&refs.length>0&&<div className="answer-group-sources">{renderInline(refs.join(' '))}</div>}</div>;
  })}</div>;
}
