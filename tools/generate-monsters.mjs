#!/usr/bin/env node
// 몬스터 그림을 Gemini API로 한 번에 뽑아 art/monsters/ 에 저장한다.
//
//   GEMINI_API_KEY=키 node tools/generate-monsters.mjs --limit 5      ← 먼저 5종만 시험
//   GEMINI_API_KEY=키 node tools/generate-monsters.mjs                ← 나머지 전부
//   GEMINI_API_KEY=키 node tools/generate-monsters.mjs --only ogre,goblin --force   ← 골라서 다시 뽑기
//
// 이미 파일이 있는 몬스터는 건너뛴다(--force 로 덮어쓰기). 키는 절대 파일에 적지 않는다.
import { readFile, writeFile, mkdir, readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(ROOT, 'art', 'monsters');
const MODEL = process.env.GEMINI_IMAGE_MODEL || 'gemini-nano-banana-2.1';
const KEY = process.env.GEMINI_API_KEY;
const WAIT_MS = Number(process.env.GEMINI_WAIT_MS || 4000); // 주문 사이 쉬는 시간

const args = process.argv.slice(2);
const opt = name => { const i = args.indexOf('--' + name); return i < 0 ? null : (args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true); };
const only = opt('only') ? String(opt('only')).split(',') : null;
const limit = opt('limit') ? Number(opt('limit')) : Infinity;
const force = !!opt('force');
const sleep = ms => new Promise(r => setTimeout(r, ms));

if (!KEY) { console.error('GEMINI_API_KEY 환경변수가 없습니다. Google AI Studio에서 API 키를 만들어 넣어 주세요.'); process.exit(1); }

const spec = JSON.parse(await readFile(path.join(ROOT, 'concepts', 'prompts.json'), 'utf8'));
await mkdir(OUT, { recursive: true });
const have = new Set((await readdir(OUT)).map(f => f.replace(/\.[^.]+$/, '')));

async function generate(m) {
  const body = {
    contents: [{ parts: [{ text: `${spec.style}. Subject: ${m.en}.` }] }],
    generationConfig: { responseModalities: ['Image'], imageConfig: { aspectRatio: '1:1' } },
  };
  const res = await fetch(`https://generativelanguage.googleapis.com/v1/models/${MODEL}:generateContent`, {
    method: 'POST',
    headers: { 'x-goog-api-key': KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) { const e = new Error(`HTTP ${res.status}: ${(await res.text()).slice(0, 300)}`); e.status = res.status; throw e; }
  const json = await res.json();
  const part = json.candidates?.[0]?.content?.parts?.find(p => p.inlineData || p.inline_data);
  const data = part?.inlineData || part?.inline_data;
  if (!data) throw new Error('그림이 돌아오지 않았습니다: ' + JSON.stringify(json).slice(0, 300));
  const ext = (data.mimeType || data.mime_type || 'image/png').includes('jpeg') ? 'jpg' : 'png';
  const file = path.join(OUT, `${m.id}.${ext}`);
  await writeFile(file, Buffer.from(data.data, 'base64'));
  return file;
}

const todo = spec.monsters.filter(m => (!only || only.includes(m.id)) && (force || !have.has(m.id))).slice(0, limit);
console.log(`모델 ${MODEL} · 뽑을 몬스터 ${todo.length}종 (전체 ${spec.monsters.length}종, 이미 있는 것 ${have.size}종)`);
const failed = [];
for (const [i, m] of todo.entries()) {
  for (let attempt = 1; ; attempt++) {
    try {
      const file = await generate(m);
      console.log(`[${i + 1}/${todo.length}] ${m.ko} → ${path.relative(ROOT, file)}`);
      break;
    } catch (e) {
      const retry = attempt < 4 && (!e.status || e.status === 429 || e.status >= 500);
      console.error(`[${i + 1}/${todo.length}] ${m.ko} 실패(${attempt}회): ${e.message}`);
      if (e.status === 401 || e.status === 403) { console.error('키가 틀렸거나 권한이 없습니다. 중단합니다.'); process.exit(1); }
      if (e.status === 429 && /free_tier|limit: 0/.test(e.message)) {
        console.error('이 키는 무료 등급이라 그림 생성 한도가 0입니다. Google AI Studio에서 결제(유료 등급)를 켠 뒤 다시 실행하세요.'); process.exit(1); }
      if (!retry) { failed.push(m.id); break; }
      await sleep(WAIT_MS * attempt * 3);
    }
  }
  await sleep(WAIT_MS);
}
if (failed.length) console.log(`실패한 것: ${failed.join(',')}\n다시 뽑기: node tools/generate-monsters.mjs --only ${failed.join(',')}`);
else console.log('끝.');
