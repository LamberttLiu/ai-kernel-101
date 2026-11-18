// Fixed raster master + independently rendered editable vector typography.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { chromium } = require('playwright');
const sharp = require('sharp');
const ROOT = __dirname;
const config = JSON.parse(fs.readFileSync(path.resolve(ROOT, process.argv[2] || 'layout.json'), 'utf8'));
const { canvas, copy, positions, colors } = config;
const stem = 'ai-kernel-101-digital-banner';
const version = config.exportVersion || 'v1';
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const escape = s => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;');
function label(id, { fill, family='Inter', style='normal', anchor='start', opacity=1 }={}) {
  const p=positions[id];
  return `<text id="${id}" x="${p.x}" y="${p.y}" font-family="${family}" font-size="${p.size}" font-weight="400" font-style="${style}" text-anchor="${anchor}" opacity="${opacity}" fill="${fill}">${escape(copy[id])}</text>`;
}
function typography() {
  const p=positions.title;
  return `<g id="brand"><text id="title-text" x="${p.x}" y="${p.y}" font-family="Inter" font-size="${p.size}" font-weight="700" fill="${colors.title}"><tspan id="title-prefix">AI Kernel </tspan><tspan id="title-101" fill="url(#title-gradient)">101</tspan></text></g>
<g id="content">${label('subtitle',{fill:colors.subtitle,family:'Microsoft YaHei'})}${label('keywords',{fill:colors.keywords,family:'Microsoft YaHei'})}</g>
<g id="auxiliary">${label('slogan1',{fill:colors.slogan})}${label('slogan2',{fill:colors.slogan})}${label('author',{fill:colors.author,style:'italic',anchor:'end',opacity:0.72})}</g>`;
}
function svgDocument(background='', width=canvas.width, height=canvas.height) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${canvas.width} ${canvas.height}" role="img" aria-labelledby="svg-title svg-description">
<title id="svg-title">AI Kernel 101 · 数字粒子横幅</title>
<desc id="svg-description">${Object.values(copy).map(escape).join('。')}。原始粒子 101 基底固定不变，左侧添加可编辑文字，标题的 101 为冷白至蓝色渐变。</desc>
<defs><linearGradient id="title-gradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="${colors.gradient[0]}"/><stop offset="58%" stop-color="${colors.gradient[1]}"/><stop offset="100%" stop-color="${colors.gradient[2]}"/></linearGradient></defs>
${background}
${typography()}
</svg>\n`;
}
async function main() {
  const basePath=path.resolve(ROOT,config.base);
  const base=fs.readFileSync(basePath);
  const baseHash=hash(base);
  const info=await sharp(base).metadata();
  if(info.width!==canvas.width||info.height!==canvas.height) throw Error('Master dimensions do not match layout; never stretch or crop it.');
  const regular=fs.readFileSync(path.join(ROOT,'fonts/Inter.ttf'));
  const italic=fs.readFileSync(path.join(ROOT,'fonts/Inter-Italic.ttf'));
  const report={base:{file:config.base,sha256:baseHash,width:info.width,height:info.height},node:process.version,sharp:sharp.versions,fonts:{Inter:hash(regular),InterItalic:hash(italic)},copy,layout:positions,gradient:colors.gradient};
  const browser=await chromium.launch({channel:'msedge',headless:true});
  let overlay;
  try {
    report.browser=await browser.version();
    const page=await browser.newPage({viewport:{width:canvas.width,height:canvas.height},deviceScaleFactor:1});
    const css=`@font-face{font-family:Inter;src:url(data:font/ttf;base64,${regular.toString('base64')}) format('truetype');font-style:normal;font-weight:100 900}@font-face{font-family:Inter;src:url(data:font/ttf;base64,${italic.toString('base64')}) format('truetype');font-style:italic;font-weight:100 900}html,body{margin:0;background:transparent}svg{display:block}`;
    await page.setContent(`<style>${css}</style>${svgDocument()}`);
    await page.evaluate(()=>document.fonts.ready);
    const bounds=await page.evaluate(()=>[...document.querySelectorAll('svg text')].map(el=>{const b=el.getBBox();return {id:el.id,text:el.textContent,x:b.x,y:b.y,width:b.width,height:b.height};}));
    const expected={'title-text':copy.title,...copy};
    for(const b of bounds) {
      if(b.text!==expected[b.id]) throw Error(`Unexpected copy: ${b.id}`);
      const rightLimit=b.id==='author'?canvas.width-64:960;
      if(b.x<64||b.y<64||b.x+b.width>rightLimit||b.y+b.height>canvas.height-48) throw Error(`Text overflow: ${JSON.stringify(b)}`);
    }
    report.bounds=bounds;
    const session=await page.context().newCDPSession(page);
    await session.send('DOM.enable');
    await session.send('CSS.enable');
    const {root}=await session.send('DOM.getDocument');
    report.platformFonts={};
    for(const b of bounds) {
      const {nodeId}=await session.send('DOM.querySelector',{nodeId:root.nodeId,selector:'#'+b.id});
      const {fonts}=await session.send('CSS.getPlatformFontsForNode',{nodeId});
      const expectedFont=['subtitle','keywords'].includes(b.id)?'Microsoft YaHei':'Inter';
      if(!fonts.length||fonts.some(f=>!f.familyName.includes(expectedFont))) throw Error(`Font fallback: ${b.id}`);
      if(b.id==='author'&&!fonts.every(f=>f.postScriptName.includes('Italic'))) throw Error('Author mark did not use the real italic font.');
      report.platformFonts[b.id]=fonts;
    }
    overlay=await page.screenshot({omitBackground:true});
  } finally { await browser.close(); }
  // Source image stays byte-identical; only alpha-covered text pixels change.
  const composed=await sharp(base).composite([{input:overlay,top:0,left:0}]).png().toBuffer();
  const baseRaw=await sharp(base).ensureAlpha().raw().toBuffer();
  const finalRaw=await sharp(composed).ensureAlpha().raw().toBuffer();
  const overlayRaw=await sharp(overlay).ensureAlpha().raw().toBuffer();
  let untouchedPixels=0,changedOutsideText=0;
  for(let p=0;p<overlayRaw.length;p+=4) {
    if(overlayRaw[p+3]!==0) continue;
    untouchedPixels++;
    for(let c=0;c<4;c++) if(baseRaw[p+c]!==finalRaw[p+c]) {changedOutsideText++;break;}
  }
  if(changedOutsideText) throw Error(`${changedOutsideText} background pixels outside text changed.`);
  if(hash(fs.readFileSync(basePath))!==baseHash) throw Error('The master file changed.');
  fs.writeFileSync(path.join(ROOT,`${stem}-2048x768-${version}.png`),composed);
  await sharp(composed).resize(1600,600).withIccProfile('srgb').png().toFile(path.join(ROOT,`${stem}-1600x600-${version}.png`));
  for(const width of [320,160]) await sharp(composed).resize(width,width*3/8).withIccProfile('srgb').png().toFile(path.join(ROOT,`preview-${width}.png`));
  const background=`<g id="visual-base"><image id="base-image" x="0" y="0" width="${canvas.width}" height="${canvas.height}" href="data:image/png;base64,${base.toString('base64')}"/></g>`;
  fs.writeFileSync(path.join(ROOT,`${stem}-1600x600-${version}.svg`),svgDocument(background,1600,600));
  report.preservation={masterUnchanged:true,untouchedPixels,changedOutsideText};
  report.outputs={};
  for(const file of [`${stem}-2048x768-${version}.png`,`${stem}-1600x600-${version}.png`,`${stem}-1600x600-${version}.svg`]) report.outputs[file]=hash(fs.readFileSync(path.join(ROOT,file)));
  fs.writeFileSync(path.join(ROOT,'validation.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report.preservation));
  console.log('Built editable SVG and PNGs; exact copy, fonts and text bounds passed.');
}
main().catch(error=>{console.error(error);process.exit(1);});
