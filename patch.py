from pathlib import Path
import json,re
p=Path('/tmp/alta/index.html'); s=p.read_text()
# Add player CSS before media query
css='''
/* Scheduled, full-screen frame-by-frame presentation player */
.player-section{position:relative;height:100svh;min-height:520px;background:#090908;overflow:hidden;isolation:isolate}
.player-section .sticky-stage{position:absolute;inset:0;height:100%;min-height:0;top:0}
.player-section .frame-wrap{padding:18px;inset:0}
.player-section .frame-image{max-width:100vw;max-height:100svh;width:100%;height:100%;object-fit:contain;border-radius:0;box-shadow:none}
.player-section .frame-wrap:after{background:linear-gradient(180deg,#0009,transparent 20%,transparent 78%,#000a)}
.player-section .stage-head{top:24px;left:24px;right:24px;max-width:none;pointer-events:none;text-align:center}
.player-section .stage-head .eyebrow{text-align:center}
.player-section .stage-head h2{font-size:clamp(20px,3vw,36px);margin:8px 0}
.player-section .stage-head p{margin:auto;font-size:12px;max-width:540px}
.player-section .frame-side{display:none}.player-section .time-label{bottom:20px;right:24px}.player-section .scroll-note{bottom:20px;left:24px}
.player-section .player-status{position:absolute;z-index:10;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:24px;background:#090908f2}
.player-status h2{font-size:clamp(28px,5vw,54px);margin:0 0 14px}.player-status p{color:#c4c0b6;line-height:1.9;max-width:580px;margin:0 0 20px}.player-status .status-time{font:600 clamp(24px,5vw,48px) ui-monospace,monospace;color:var(--accent);direction:ltr}.player-status[hidden]{display:none!important}
.player-controls{position:absolute;z-index:8;bottom:48px;left:50%;transform:translateX(-50%);display:flex;gap:8px;align-items:center}
.player-controls button{font:inherit;color:#f5f1e8;background:#171714d9;border:1px solid #ffffff50;border-radius:999px;padding:10px 16px;backdrop-filter:blur(10px);cursor:pointer}
.player-controls button:active{background:var(--accent);color:#111}.player-section.is-paused .progress-bar{opacity:.7}
@media(max-width:760px){.player-section .stage-head{top:16px;left:12px;right:12px}.player-section .stage-head h2{font-size:22px}.player-section .stage-head p{font-size:11px}.player-section .frame-wrap{padding:0}.player-section .time-label{right:14px;bottom:18px}.player-section .scroll-note{left:14px;bottom:18px}.player-controls{bottom:48px}.player-controls button{padding:9px 13px;font-size:12px}}
'''
s=s.replace('@media(max-width:760px){',css+'\n@media(max-width:760px){',1)
# Extract existing scrub section and place it at the very beginning of main
start=s.index('<section class="scrub-section"')
end=s.index('</section>',start)+len('</section>')
section=s[start:end]
# modify section class and player elements
section=section.replace('class="scrub-section"','class="player-section"',1)
section=section.replace('<div class="stage-head"><div class="eyebrow">02 — PRODUCT WALKTHROUGH</div><h2 id="stageTitle">از نزدیک ببین.</h2><p id="stageDesc">با اسکرول، فریم‌های ویدئوی معرفی را مرور کن.</p></div>', '<div class="stage-head"><div class="eyebrow">ALTA · PRESENTATION MODE</div><h2 id="stageTitle">معرفی ALTA</h2><p id="stageDesc">ویدئو به‌صورت خودکار پخش می‌شود؛ لمس طولانی مکث و اسکرول، جلو/عقب رفتن را کنترل می‌کند.</p></div>')
section=section.replace('<div class="scroll-note">SCROLL TO EXPLORE</div>', '<div class="scroll-note" id="playHint">نگه‌داشتن لمس = مکث · بالا/پایین = عقب/جلو</div>')
section=section.replace('</div></div></section>', '</div><div class="player-status" id="playerStatus"><h2 id="statusTitle">در حال آماده‌سازی ارائه…</h2><p id="statusMessage">فریم‌ها بارگذاری می‌شوند.</p><div class="status-time" id="statusTime"></div></div><div class="player-controls"><button type="button" id="togglePlayback">مکث</button><button type="button" id="skipBack">۱۰ ثانیه عقب</button><button type="button" id="skipForward">۱۰ ثانیه جلو</button><button type="button" id="skipToContent">رفتن به توضیحات ↓</button></div></div></section>')
s=s[:start]+s[end:]
# insert at start main
s=s.replace('<main>','<main>\n'+section,1)
# Update header CTA
s=s.replace('<a class="pill" href="#experience">شروع تجربه ↓</a>','<a class="pill" href="#experience">مشاهده فریم‌ها ↓</a>',1)
# Make content experience anchor still points to section? old scrub removed; set anchor on hero section
s=s.replace('<section class="hero">','<section class="hero" id="experience">',1)
# Replace JS from opening script to observer line, retain observer logic
js_start=s.index('<script>')
obs=s.index("const observer=new IntersectionObserver",js_start)
newjs='''<script>
let segments=[],frames=[],active=-1,playing=false,ended=false,manualUntil=0,raf=0,config={startAt:null,enabled:true,playbackRate:1};
const img=document.getElementById('frameImage'),scrub=document.querySelector('.player-section'),progress=document.getElementById('progressBar');
const stageTitle=document.getElementById('stageTitle'),stageDesc=document.getElementById('stageDesc'),frameHeading=document.getElementById('frameHeading'),frameCopy=document.getElementById('frameCopy'),frameCount=document.getElementById('frameCount'),timeLabel=document.getElementById('timeLabel');
const status=document.getElementById('playerStatus'),statusTitle=document.getElementById('statusTitle'),statusMessage=document.getElementById('statusMessage'),statusTime=document.getElementById('statusTime'),toggleBtn=document.getElementById('togglePlayback');
const chapters=[{at:0,title:'از نزدیک ببین.',desc:'ویدئوی معرفی ALTA در حال پخش است.',head:'تجربه ALTA',copy:'مرور محصول'},{at:.16,title:'یک نگاه به محصول.',desc:'رابط کاربری و اجزای تجربه را دنبال کن.',head:'رابط کاربری',copy:'جزئیات محصول'},{at:.36,title:'استایل، مرحله‌به‌مرحله.',desc:'بخش‌های ویدئو به ترتیب زمانی نمایش داده می‌شوند.',head:'فرآیند استفاده',copy:'مرور محصول'},{at:.60,title:'از تصویر تا پیشنهاد.',desc:'تجربه شخصی و استایل موضوع اصلی‌اند.',head:'تجربه بصری',copy:'مرور محصول'},{at:.82,title:'فناوری در خدمت انتخاب.',desc:'در پایان توضیحات تکمیلی سایت را ببین.',head:'جمع‌بندی',copy:'پایان ویدئو'}];
function fmt(s){let m=Math.floor(s/60),r=Math.floor(s%60);return String(m).padStart(2,'0')+':'+String(r).padStart(2,'0')}
function setFrame(i){if(!frames.length)return;i=Math.max(0,Math.min(frames.length-1,Math.round(i)));if(i===active)return;active=i;const next=new Image();next.onload=()=>{img.src=next.src;img.classList.remove('loading')};next.onerror=()=>img.classList.remove('loading');img.classList.add('loading');next.src=frames[i].src;frameCount.textContent='FRAME '+String(i+1).padStart(3,'0');timeLabel.textContent=fmt(frames[i].time)+' / '+fmt(frames[frames.length-1].time);let prog=i/Math.max(1,frames.length-1);progress.style.width=(prog*100)+'%';let ch=chapters[0];chapters.forEach(c=>{if(prog>=c.at)ch=c});stageTitle.textContent=ch.title;stageDesc.textContent=ch.desc;frameHeading.textContent=ch.head;frameCopy.textContent=ch.copy;}
function pause(){playing=false;scrub.classList.add('is-paused');toggleBtn.textContent='ادامه پخش';if(raf)cancelAnimationFrame(raf);}
function play(){if(ended){setFrame(0);ended=false}playing=true;scrub.classList.remove('is-paused');toggleBtn.textContent='مکث';lastTick=performance.now();raf=requestAnimationFrame(tick)}
let lastTick=0,videoTime=0;
function tick(now){if(!playing)return;const delta=Math.min(.1,(now-lastTick)/1000||0);lastTick=now;videoTime+=delta*(Number(config.playbackRate)||1);let idx=0;while(idx<frames.length-1 && frames[idx+1].time<=videoTime)idx++;setFrame(idx);if(idx>=frames.length-1){pause();ended=true;status.hidden=true;document.getElementById('playHint').textContent='ویدئو تمام شد · برای دیدن توضیحات به پایین برو';return}raf=requestAnimationFrame(tick)}
function seek(seconds){if(!frames.length)return;pause();videoTime=Math.max(0,Math.min(frames[frames.length-1].time,videoTime+seconds));let idx=0;while(idx<frames.length-1&&frames[idx+1].time<=videoTime)idx++;setFrame(idx);ended=idx===frames.length-1;}
function goContent(){pause();document.querySelector('.hero').scrollIntoView({behavior:'smooth'});}
document.getElementById('togglePlayback').addEventListener('click',()=>playing?pause():play());document.getElementById('skipBack').addEventListener('click',()=>seek(-10));document.getElementById('skipForward').addEventListener('click',()=>seek(10));document.getElementById('skipToContent').addEventListener('click',goContent);
// Wheel and trackpad move the timeline manually; this is not page-scroll-driven playback.
scrub.addEventListener('wheel',e=>{if(status.hidden){e.preventDefault();seek(e.deltaY>0?1.5:-1.5)}},{passive:false});
// Holding a finger on the video pauses playback; release resumes it.
let touchPaused=false;scrub.addEventListener('touchstart',()=>{if(playing){touchPaused=true;pause()}},{passive:true});scrub.addEventListener('touchend',()=>{if(touchPaused){touchPaused=false;play()}},{passive:true});
scrub.addEventListener('keydown',e=>{if(e.code==='Space'){e.preventDefault();playing?pause():play()}else if(e.code==='ArrowDown')seek(2);else if(e.code==='ArrowUp')seek(-2)});scrub.tabIndex=0;
function showStatus(title,message,time=''){status.hidden=false;statusTitle.textContent=title;statusMessage.textContent=message;statusTime.textContent=time}
function scheduleCheck(){if(!config.enabled){showStatus('ارائه غیرفعال است','برای فعال‌سازی، فایل presentation-config.json را در GitHub ویرایش کن.');return}if(!config.startAt){status.hidden=true;play();return}const start=new Date(config.startAt).getTime(),now=Date.now();if(!Number.isFinite(start)){showStatus('زمان شروع معتبر نیست','مقدار startAt را در presentation-config.json با تاریخ ISO معتبر وارد کن.');return}if(now>=start){status.hidden=true;play();return}const left=Math.ceil((start-now)/1000);showStatus('ارائه هنوز شروع نشده','این صفحه در زمان تعیین‌شده به‌صورت خودکار پخش را آغاز می‌کند. زمان باید همراه با اختلاف منطقه زمانی وارد شود.',fmt(left));setTimeout(scheduleCheck,Math.min(1000,Math.max(100,left%1000||1000)))}
Promise.all([fetch('segments.json').then(r=>{if(!r.ok)throw Error('segments.json');return r.json()}),fetch('presentation-config.json').then(r=>{if(!r.ok)throw Error('presentation-config.json');return r.json()})]).then(([data,cfg])=>{config={...config,...cfg};segments=data;data.forEach(s=>s.frames.forEach((src,i)=>frames.push({src,time:s.start+(i/(s.frames.length-1||1))*(s.end-s.start)})));if(!frames.length)throw Error('No frames');videoTime=frames[0].time;setFrame(0);frames.slice(0,8).forEach(f=>{const im=new Image();im.src=f.src});scheduleCheck()}).catch(err=>{showStatus('بارگذاری ناموفق بود','فایل‌های segments.json یا presentation-config.json پیدا نشدند. مطمئن شو هر دو کنار index.html هستند.');console.error(err)});
'''
s=s[:js_start]+newjs+s[obs:]
# ensure ending observer uses document reveal unchanged
p.write_text(s)
config={"enabled":True,"startAt":None,"playbackRate":1,"timezone":"Asia/Tehran","instructions":"برای زمان‌بندی، startAt را به تاریخ و ساعت ISO 8601 همراه با اختلاف ساعت ایران تغییر بده؛ مثال: 2026-10-20T09:00:00+03:30. برای شروع فوری، startAt را null بگذار. enabled=false نمایش را غیرفعال می‌کند. تغییر این فایل در GitHub برای همه بازدیدکنندگان اعمال می‌شود؛ دانشجوها باید صفحه را باز یا تازه‌سازی کنند تا زمان‌بندی جدید دریافت شود."}
Path('/tmp/alta/presentation-config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
# update README
readme=Path('/tmp/alta/README_FA.txt')
r=readme.read_text(encoding='utf-8')
r+='''\n\nزمان‌بندی ارائه\n----------------\nفایل presentation-config.json را در GitHub باز کن و Edit بزن.\n- enabled: برای فعال/غیرفعال کردن نمایش\n- startAt: برای شروع فوری null؛ یا تاریخ/ساعت ISO همراه با اختلاف ساعت، مثلاً 2026-10-20T09:00:00+03:30\n- playbackRate: سرعت پخش؛ 1 سرعت اصلی، 0.8 آهسته‌تر، 1.2 سریع‌تر\n\nپخش فریم‌به‌فریم از ابتدای صفحه و تمام‌صفحه آغاز می‌شود. لمس طولانی مکث می‌کند و با برداشتن انگشت ادامه می‌دهد؛ اسکرول/چرخ ماوس داخل پلیر برای جلو و عقب رفتن است. بعد از پایان، توضیحات ALTA پایین صفحه قرار دارند. این زمان‌بندی سمت مرورگر است و نیاز به سرور ندارد؛ برای دریافت تنظیم تازه، صفحه باید باز یا تازه‌سازی شود.\n'''
readme.write_text(r,encoding='utf-8')
