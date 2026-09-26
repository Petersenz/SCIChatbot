const fs=require('fs'),ts=require('../frontend/node_modules/typescript'),vm=require('vm'),assert=require('node:assert/strict');
const file=require('path').join(__dirname,'../frontend/components/request.ts');
const apiExports={};let fakeFetch=fetch;
vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:apiExports,Response,AbortController,setTimeout,clearTimeout,fetch:(...args)=>fakeFetch(...args)});
(async()=>{
assert.equal(apiExports.remainingThinkingMs(100,300),800);assert.equal(apiExports.remainingThinkingMs(100,1400),0);
assert.deepEqual(JSON.parse(JSON.stringify(await apiExports.readApiResponse(new Response('{"ok":true}')))),{ok:true});
for(const status of [401,403,409,413,422,429,500,502,503,504]){
 let error;try{await apiExports.readApiResponse(new Response('{"detail":"server message","request_id":"abcdef123456"}',{status,headers:{'Retry-After':'12'}}),'POST')}catch(e){error=e}
 assert.equal(error.status,status);assert.equal(error.requestId,'abcdef123456');assert.equal(error.retryAfter,12);if(status>=500){assert(!error.message.includes('server message'));assert(error.message.includes('ก่อนส่งซ้ำ'));}
}
await assert.rejects(apiExports.readApiResponse(new Response('<html>proxy failure</html>',{status:502}),'POST'),e=>!e.message.includes('<html>')&&e.message.includes('ก่อนส่งซ้ำ'));
await assert.rejects(apiExports.readApiResponse(new Response('not json',{status:200}),'POST'),e=>e.code==='invalid_response');
fakeFetch=async()=>{throw new TypeError('PRIVATE_NETWORK_DETAIL')};await assert.rejects(apiExports.requestJson('/test',{method:'POST'}),e=>e.code==='network_error'&&!e.message.includes('PRIVATE')&&e.message.includes('ก่อนส่งซ้ำ'));
fakeFetch=(_url,{signal})=>new Promise((_,reject)=>signal.addEventListener('abort',()=>reject(new Error('aborted'))));await assert.rejects(apiExports.requestJson('/test',{},5),e=>e.code==='timeout');
console.log('PASS: minimum timing fast/slow, JSON success, 10 HTTP statuses, HTML proxy, invalid JSON, network, timeout');
})().catch(e=>{console.error(e);process.exitCode=1});

