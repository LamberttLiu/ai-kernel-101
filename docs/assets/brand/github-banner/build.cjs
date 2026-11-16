// Accepted grid: 32px pitch, 30px tiles, 2px inner gaps.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { chromium } = require('playwright');
const sharp = require('sharp');
const ROOT = __dirname;
const TOKENS = JSON.parse(fs.readFileSync(path.join(ROOT, '../tokens/colors.json')));
const [RED, CYAN, BG, SLATE, STEEL, MIST] = Object.values(TOKENS);
const FONT = 'Inter';
const CN = 'Microsoft YaHei';
const COPY = {
  brand: 'AI Kernel 101',
  positioning: '从 Hello World 到 Flash Attention',
  keywords: 'Ascend C · First Principles · Performance',
  slogan: 'UNDERSTAND THE COMPUTE. ENGINEER THE PERFORMANCE.',
  header: 'OPEN SOURCE · KERNEL ENGINEERING',
  author: '@LamberttLiu'
};
function fontIdentity(file) {
  const b = fs.readFileSync(file);
  const base = b.toString('ascii', 0, 4) === 'ttcf' ? b.readUInt32BE(12) : 0;
  let names;
  for (let i = 0; i < b.readUInt16BE(base + 4); i++) {
    const p = base + 12 + i * 16;
    if (b.toString('ascii', p, p + 4) === 'name') names = b.readUInt32BE(p + 8);
  }
  if (names === undefined) throw Error('Font has no name table');
  const versions = [];
  for (let i = 0; i < b.readUInt16BE(names + 2); i++) {
    const p = names + 6 + i * 12;
    if (b.readUInt16BE(p + 6) !== 5) continue;
    const offset = names + b.readUInt16BE(names + 4) + b.readUInt16BE(p + 10);
    const raw = Buffer.from(b.subarray(offset, offset + b.readUInt16BE(p + 8)));
    const unicode = [0, 3].includes(b.readUInt16BE(p));
    const value = unicode ? raw.swap16().toString('utf16le') : raw.toString('ascii');
    if (!versions.includes(value)) versions.push(value);
  }
  return { versions, sha256: crypto.createHash('sha256').update(b).digest('hex') };
}
function contrast(a, b) {
  const luminance = s => s.slice(1).match(/../g).map(v => parseInt(v, 16) / 255).map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4).reduce((s, v, i) => s + v * [0.2126, 0.7152, 0.0722][i], 0);
  const [x, y] = [luminance(a), luminance(b)].sort((a, b) => b - a);
  return Number(((x + 0.05) / (y + 0.05)).toFixed(2));
}
const esc = s => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;');
function text(id, x, y, size, value, { fill = MIST, weight = 400, family = FONT, style = 'normal', opacity = 1 } = {}) {
  return `<text id="${id}" x="${x}" y="${y}" font-family="${family}" font-size="${size}" font-weight="${weight}" font-style="${style}" opacity="${opacity}" fill="${fill}">${esc(value)}</text>`;
}
function rect(x, y, w, h, fill, extra = '') { return `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" ${extra}/>`; }
function line(d, color = CYAN, width = 4, extra = '') { return `<path d="${d}" fill="none" stroke="${color}" stroke-width="${width}" ${extra}/>`; }
function group(id, body) { return `<g id="${id}">\n${body}\n</g>`; }
function base(variant, layers) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1600" height="600" viewBox="0 0 1600 600" role="img" aria-labelledby="title description">
<title id="title">AI Kernel 101 — 方案 ${variant} · 像素矩阵</title>
<desc id="description">${COPY.header}。${COPY.positioning}。${COPY.keywords}。${COPY.slogan}。${COPY.author}。三个面板位置保持原样；底层矩阵与无描边的白色 101 共用 32 px 步距、30 px 色块和 2 px 内部间隙。青色流线从第一框顶部连接第二框顶部，再从第二框底部连接第三框底部，每段以圆点起始、实心锐角三角箭头结束。中央红色分块表示活跃计算。图形是品牌概念，不代表具体算法、设备或测量结果。</desc>
${group('background', rect(0, 0, 1600, 600, BG))}
${layers.join('\n')}
</svg>\n`;
}
function footer() {
  return group('auxiliary', text('slogan', 64, 544, 20, COPY.slogan, { fill: STEEL }) +
    text('header', 64, 88, 20, COPY.header, { weight: 600, fill: STEEL }) +
    text('author', 1536, 568, 20, COPY.author, { fill: STEEL, style: 'italic', opacity: 0.65 }).replace('x="1536"', 'text-anchor="end" x="1536"'));
}
function content(y = 374) {
  return group('content', text('positioning', 64, y, 34, COPY.positioning, { family: CN, fill: STEEL }) + text('keywords', 64, y + 56, 26, COPY.keywords, { fill: STEEL }));
}
function c() {
  // White square pixels, independent of typography and any bitmap assets.
  const digits = [
    ['010', '110', '010', '010', '010', '010', '111'],
    ['111', '101', '101', '101', '101', '101', '111'],
    ['010', '110', '010', '010', '010', '010', '111']
  ];
  let grid = '', compute = '', pixels = '';
  for (let d = 0; d < 3; d++) {
    const x = 992 + d * 192;
    let cells = '';
    for (let r = 0; r < 13; r++) for (let c = 0; c < 5; c++) {
      cells += rect(x + 1 + c * 32, 81 + r * 32, 30, 30, d === 1 ? RED : CYAN);
    }
    compute += `<g id="matrix-box-${d + 1}" data-cell-size="30" data-cell-pitch="32">${cells}</g>`;
    let digit = '';
    for (let r = 0; r < 7; r++) for (let c = 0; c < 3; c++) if (digits[d][r][c] === '1') {
      digit += rect(x + 33 + c * 32, 177 + r * 32, 30, 30, MIST);
    }
    pixels += group(`pixel-digit-${d + 1}`, digit);
  }
  // Each connection has exactly one circular source and one filled triangle.
  const flow = group('flow-box-1-to-2',
    line('M 1072 72 V 66 Q 1072 56 1082 56 H 1254 Q 1264 56 1264 66 V 68', CYAN, 3, 'stroke-linecap="round"') +
    `<circle cx="1072" cy="72" r="4" fill="${CYAN}"/>` +
    `<path d="M 1258 68 L 1270 68 L 1264 80 Z" fill="${CYAN}"/>`) +
    group('flow-box-2-to-3',
      line('M 1264 504 V 510 Q 1264 520 1274 520 H 1446 Q 1456 520 1456 510 V 508', CYAN, 3, 'stroke-linecap="round"') +
      `<circle cx="1264" cy="504" r="4" fill="${CYAN}"/>` +
      `<path d="M 1450 508 L 1462 508 L 1456 496 Z" fill="${CYAN}"/>`);
  return base('C', [
    group('compute', compute), group('pixel-numerals', pixels), group('grid', grid), group('data-flow', flow),
    group('brand', text('brand-name', 64, 244, 120, COPY.brand, { weight: 700 })),
    content(), footer()
  ]);
}
async function main() {
  const fontPath = path.join(ROOT, 'fonts/Inter.ttf');
  if (!fs.existsSync(fontPath)) throw Error('Missing pinned Inter font: see README.md');
  const inter = fs.readFileSync(fontPath).toString('base64');
  const italicPath = path.join(ROOT, 'fonts/Inter-Italic.ttf');
  const italic = fs.readFileSync(italicPath).toString('base64');
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 600 }, deviceScaleFactor: 1 });
  const report = {
    renderer: await browser.version(), node: process.version, sharp: sharp.versions,
    fonts: { Inter: fontIdentity(fontPath), 'Inter Italic': fontIdentity(italicPath), 'Microsoft YaHei': fontIdentity(path.join(process.env.WINDIR || 'C:/Windows', 'Fonts/msyh.ttc')) },
    contrastOnGraphite: Object.fromEntries(Object.entries(TOKENS).filter(([k]) => k !== 'neutral.900').map(([k, v]) => [k, contrast(v, BG)])), variants: {}
  };
  for (const [variant, make] of Object.entries({ C: c })) {
    const stem = 'ai-kernel-101_github-hero_brand-c_1600x600';
    const svg = make();
    const colors = [...new Set(svg.match(/#[0-9a-fA-F]{6}/g))];
    if (colors.some(c => !Object.values(TOKENS).includes(c))) throw Error('Unexpected color');
    if (/<script|foreignObject|onload=|https?:\/\//.test(svg.replaceAll('http://www.w3.org/2000/svg', '').replaceAll('http://www.w3.org/1999/xlink', ''))) throw Error('External or active SVG content');
    fs.writeFileSync(path.join(ROOT, stem + '.svg'), svg);
    await page.setContent(`<style>@font-face{font-family:Inter;src:url(data:font/ttf;base64,${inter}) format('truetype');font-weight:100 900;font-style:normal}@font-face{font-family:Inter;src:url(data:font/ttf;base64,${italic}) format('truetype');font-weight:100 900;font-style:italic}html,body{margin:0;background:${BG}}svg{display:block}</style>${svg}`);
    await page.evaluate(() => document.fonts.ready);
    const pixelCheck = await page.evaluate(() => {
      const pixels = [...document.querySelectorAll('#pixel-numerals rect')];
      const author = document.getElementById('author');
      const cells=[...document.querySelectorAll('#compute rect')];
      return { count: pixels.length, whiteSquares: pixels.every(p => p.getAttribute('fill') === '#F3F5F7' && p.getAttribute('width') === '30' && p.getAttribute('height') === '30' && !p.hasAttribute('stroke')), gridAligned: [...pixels,...cells].every(p => (Number(p.getAttribute('x')) - 993) % 32 === 0 && (Number(p.getAttribute('y')) - 81) % 32 === 0), tileCount:cells.length,tileSize:30,tilePitch:32,innerGap:2,watermarkItalic: getComputedStyle(author).fontStyle === 'italic', watermarkFill: author.getAttribute('fill'), watermarkOpacity: author.getAttribute('opacity'), flowCount: document.querySelectorAll('#data-flow > g').length, circularSources: document.querySelectorAll('#data-flow circle').length, noVisibleConceptNote: ![...document.querySelectorAll('svg text')].some(t => t.textContent.includes('概念示意')) };
    });
    if (!pixelCheck.count || !pixelCheck.whiteSquares || !pixelCheck.gridAligned || !pixelCheck.watermarkItalic || pixelCheck.flowCount !== 2 || pixelCheck.circularSources !== 2 || !pixelCheck.noVisibleConceptNote) throw Error('Pixel / watermark revision check failed');
    const sourceCheck = await page.evaluate(() => {
      const ids = [...document.querySelectorAll('svg [id]')].map(n => n.id);
      const get = id => document.getElementById(id).textContent.replace(/\s+/g, ' ').trim();
      return { duplicateIds: ids.filter((v, i) => ids.indexOf(v) !== i), brand: get('brand-name'), positioning: get('positioning'), keywords: get('keywords'), slogan: get('slogan'), header: get('header'), author: get('author') };
    });
    if (sourceCheck.duplicateIds.length || Object.entries(COPY).some(([k, v]) => sourceCheck[k] !== v)) throw Error('Copy / ID validation failed');
    const bounds = await page.evaluate(() => [...document.querySelectorAll('svg text')].map(t => { const b = t.getBBox(); return { id: t.id, text: t.textContent, x: b.x, y: b.y, width: b.width, height: b.height, font: getComputedStyle(t).fontFamily }; }));
    // Author explicitly moved the watermark down one measured text height (24 px).
    for (const b of bounds) if (b.x < 48 || b.y < 48 || b.x + b.width > 1552 || b.y + b.height > (b.id === 'author' ? 576 : 552)) throw Error(`Unsafe text ${variant}: ${JSON.stringify(b)}`);
    const client = await page.context().newCDPSession(page);
    const { root } = await client.send('DOM.getDocument');
    let platformFonts = {};
    for (const id of ['brand-name', 'positioning', 'keywords', 'slogan', 'header', 'author']) {
      const { nodeId } = await client.send('DOM.querySelector', { nodeId: root.nodeId, selector: '#' + id });
      const { fonts } = await client.send('CSS.getPlatformFontsForNode', { nodeId }).catch(async () => { await client.send('DOM.enable'); await client.send('CSS.enable'); return client.send('CSS.getPlatformFontsForNode', { nodeId }); });
      platformFonts[id] = fonts;
      const expected = id === 'positioning' ? 'Microsoft YaHei' : 'Inter';
      if (!fonts.length || fonts.some(f => !f.familyName.includes(expected))) throw Error(`Font fallback ${variant}/${id}: ${JSON.stringify(fonts)}`);
    }
    const png = await page.screenshot();
    await sharp(png).withIccProfile('srgb').png().toFile(path.join(ROOT, stem + '.png'));
    await sharp(png).resize(320, 120).withIccProfile('srgb').png().toFile(path.join(ROOT, `preview-${variant.toLowerCase()}-320.png`));
    const pngInfo = await sharp(path.join(ROOT, stem + '.png')).metadata();
    if (pngInfo.width !== 1600 || pngInfo.height !== 600 || !pngInfo.hasProfile) throw Error('Invalid PNG output');
    report.variants[variant] = { file: stem, sourceCheck, pixelCheck, colors, bounds, platformFonts, png: { width: pngInfo.width, height: pngInfo.height, space: pngInfo.space, hasProfile: pngInfo.hasProfile }, svgSha256: crypto.createHash('sha256').update(svg).digest('hex'), pngSha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT, stem + '.png'))).digest('hex') };
    await client.detach();
  }
  await browser.close();
  fs.writeFileSync(path.join(ROOT, 'validation.json'), JSON.stringify(report, null, 2) + '\n');
  console.log('Built revised C: editable SVG, sRGB PNG, 320px preview; font and text bounds checks passed.');
}
main().catch(e => { console.error(e); process.exit(1); });
