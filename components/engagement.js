(()=>{"use strict";
const d=document,body=d.body;if(!body)return;
const send=(name,params={})=>{if(typeof window.gtag==="function")window.gtag("event",name,params)};
const bar=d.createElement("div");bar.className="xenors-reading-progress";bar.setAttribute("aria-hidden","true");body.appendChild(bar);
const progress=()=>{const h=d.documentElement,max=h.scrollHeight-innerHeight;const p=max>0?Math.min(1,Math.max(0,scrollY/max)):0;bar.style.width=(p*100)+"%";return p};
addEventListener("scroll",progress,{passive:true});addEventListener("resize",progress,{passive:true});progress();

const main=d.querySelector("main")||body;
const h2=[...main.querySelectorAll("h2")].filter(x=>x.textContent.trim().length>3);
if(h2.length>=4){
 h2.forEach((h,i)=>{if(!h.id)h.id="section-"+(i+1)+"-"+h.textContent.trim().toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,48)});
 const box=d.createElement("details");box.className="xenors-on-page";box.open=innerWidth>900;
 box.innerHTML='<summary>On this page</summary><nav aria-label="On this page">'+h2.slice(0,12).map(h=>'<a href="#'+h.id+'">'+h.textContent.trim().replace(/[<>&]/g,s=>({"<":"&lt;",">":"&gt;","&":"&amp;"}[s]))+'</a>').join("")+'</nav>';
 const anchor=main.querySelector("h1")||main.firstElementChild;if(anchor)anchor.insertAdjacentElement("afterend",box);
 const links=[...box.querySelectorAll("a")];
 links.forEach(a=>a.addEventListener("click",()=>send("toc_click",{link_text:a.textContent.trim(),link_url:a.getAttribute("href")})));
 if("IntersectionObserver" in window){
  const map=new Map(links.map(a=>[a.getAttribute("href").slice(1),a]));
  const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){links.forEach(a=>a.classList.remove("is-active"));const a=map.get(e.target.id);if(a)a.classList.add("is-active")}})},{rootMargin:"-15% 0px -70% 0px"});
  h2.forEach(h=>io.observe(h));
 }
}
send("article_start",{page_path:location.pathname});
[10,30,60].forEach(sec=>setTimeout(()=>{if(!d.hidden)send(sec+"_sec_engaged",{engagement_time_msec:sec*1000})},sec*1000));
const marks=[[.25,"article_25_percent"],[.5,"article_50_percent"],[.75,"article_75_percent"],[.9,"article_90_percent"]],done=new Set();
addEventListener("scroll",()=>{const p=progress();marks.forEach(([n,event])=>{if(p>=n&&!done.has(event)){done.add(event);send(event,{engagement_time_msec:1})}})},{passive:true});
d.addEventListener("click",e=>{
 const copy=e.target.closest(".copy,[data-copy],button[aria-label*='Copy'],button[aria-label*='copy']");if(copy)send("code_copy",{page_path:location.pathname});
 const a=e.target.closest("a[href]");if(!a)return;const href=a.href;
 if(a.closest(".xenors-on-page"))return;
 try{const u=new URL(href,location.href);if(u.origin===location.origin&&u.pathname!==location.pathname)send("internal_article_click",{link_text:a.textContent.trim().slice(0,100),link_url:u.pathname});else if(u.origin!==location.origin)send("source_click",{link_text:a.textContent.trim().slice(0,100),link_url:u.href})}catch(_){}
});
d.querySelectorAll("video").forEach(v=>v.addEventListener("play",()=>send("video_play",{page_path:location.pathname}),{once:true}));
})();