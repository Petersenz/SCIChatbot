const fs=require('fs'),assert=require('assert'),vm=require('vm'),ts=require('../frontend/node_modules/typescript');
const React=require('../frontend/node_modules/react'),{renderToStaticMarkup}=require('../frontend/node_modules/react-dom/server');
function load(file,deps={}){const exports={};vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText,{exports,require:n=>deps[n]||require('../frontend/node_modules/'+n)});return exports;}
const format=load('frontend/components/ui/answer-format.ts');
const {AnswerContent}=load('frontend/components/ui/answer-content.tsx',{'./answer-format':format});
const body='## วิสัยทัศน์\nผลิตบัณฑิตที่มีคุณภาพ [1]\n\n## พันธกิจ\n1. บริการวิชาการ [1]\n2. วิจัย [1]\n3. ผลิตบัณฑิต [1]\n4. ทำนุบำรุง [1]\n5. บริหาร [1]';
const copy=format.copyAnswerText(body,1);assert(!copy.includes('[1]'));assert(!copy.includes('##'));assert(copy.includes('5. บริหาร'));
assert.equal(format.copyAnswerText('เงินเดือน 28,000 บาท ปี 2569 วันที่ 27/09/2569 [1] [9]',1),'เงินเดือน 28,000 บาท ปี 2569 วันที่ 27/09/2569  [9]');
assert.equal(format.copyAnswerText('ข้อมูล [1]',0),'ข้อมูล [1]');
assert(format.copyAnswerText('https://example.test/a',1).includes('https://example.test/a'));
assert.equal(format.answerBlocks('1.5 ล้านบาท')[0].kind,'paragraph');
assert.equal(format.answerBlocks('**หัวข้อ** [1] [2]')[0].lines[0],'หัวข้อ [1] [2]');
const render=text=>renderToStaticMarkup(React.createElement(AnswerContent,{text,renderInline:t=>t}));
const html=render(body);assert.equal((html.match(/<h3/g)||[]).length,2);assert.equal((html.match(/<li>/g)||[]).length,5);assert.equal((html.match(/\[1\]/g)||[]).length,2);
assert(render('• วิสัยทัศน์: ข้อความ\n• พันธกิจ:\n1. หนึ่ง\n2. สอง').includes('<ol'));
const mixed=render('1. หนึ่ง [1]\n2. สอง [2]');assert(mixed.includes('หนึ่ง [1]</li>'));assert(mixed.includes('สอง [2]</li>'));
assert(!render('<img src=x onerror=alert(1)>').includes('<img'));
console.log('PASS answer copy, semantic headings/lists, provenance, escaping and numeric preservation');
