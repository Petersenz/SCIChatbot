export type AnswerBlock = {kind: 'heading'|'paragraph'|'ul'|'ol'; lines: string[]; start?: number};
const legacyHeading = /^(?:[•*-]\s*)?(ปรัชญา|ปณิธาน|วิสัยทัศน์|พันธกิจ|ค่านิยมองค์กร|อัตลักษณ์|เอกลักษณ์คณะ|เอกลักษณ์มหาวิทยาลัย)\s*[:：]\s*(.*)$/;
export function answerBlocks(text: string): AnswerBlock[] {
  const blocks: AnswerBlock[]=[];
  let last: AnswerBlock|undefined;
  const add=(kind:AnswerBlock['kind'],value:string,start?:number)=>{
    if(last?.kind===kind && kind!=='heading' && (kind!=='ol' || start===(last.start||1)+last.lines.length)) last.lines.push(value);
    else {last={kind,lines:[value],start};blocks.push(last);}
  };
  for(const raw of text.replace(/\r\n?/g,'\n').split('\n')){
    const line=raw.trim(); if(!line){last=undefined;continue;}
    const heading=/^#{1,4}\s+(.+)$/.exec(line)||/^\*\*(.+?)\*\*\s*:?((?:\s*\[\d+\])*)\s*$/.exec(line);
    const legacy=legacyHeading.exec(line);
    if(heading){add('heading',(heading[1]+(heading[2]?' '+heading[2].trim():'')).replace(/\*\*/g,''));continue;}
    if(legacy){add('heading',legacy[1]);if(legacy[2])add('paragraph',legacy[2]);continue;}
    const ordered=/^(\d+)[.)]\s*(?!\d)(.+)$/.exec(line);
    const bullet=/^[•*-]\s+(.+)$/.exec(line);
    if(ordered){add('ol',ordered[2],Number(ordered[1]));continue;}
    if(bullet){add('ul',bullet[1]);continue;}
    add('paragraph',line);
  }
  return blocks;
}
export function copyAnswerText(text:string, sourceCount:number):string {
  // Remove only citation tokens resolving to provided sources; keep meaningful
  // numbers, dates, list numbering, unknown brackets and explicit URLs.
  const clean=text.replace(/\[(\d+)\]/g,(token,n)=>Number(n)>=1&&Number(n)<=sourceCount?'':token);
  return answerBlocks(clean).map(block=>block.lines.map((line,i)=>{
    const content=line.trimEnd();
    return block.kind==='ul'?`• ${content}`:block.kind==='ol'?`${(block.start||1)+i}. ${content}`:content;
  }).join('\n')).join('\n\n').replace(/[ \t]+\n/g,'\n').trim();
}
