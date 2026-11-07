(()=>{"use strict";
const d=document,body=d.body;if(!body)return;
const bar=d.createElement("div");bar.className="xenors-reading-progress";bar.setAttribute("aria-hidden","true");body.appendChild(bar);
const update=()=>{const h=d.documentElement;const max=h.scrollHeight-innerHeight;bar.style.width=(max>0?Math.min(100,Math.max(0,scrollY/max*100)):0)+"%"};
addEventListener("scroll",update,{passive:true});addEventListener("resize",update,{passive:true});update();
const main=d.querySelector("main")||body;const h2=[...main.querySelectorAll("h2")].filter(x=>x.textContent.trim().length>3);
if(h2.length>=4){h2.forEach((h,i)=>{if(!h.id)h.id="section-"+(i+1)+"-"+h.textContent.trim().toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,48)});
 const box=d.createElement("details");box.className="xenors-on-page";box.open=innerWidth>900;box.innerHTML='<summary>On this page</summary><nav aria-label="On this page">'+h2.slice(0,12).map(h=>'<a href="#'+h.id+'">'+h.textContent.trim().replace(/[<>&]/g,s=>({"<":"&lt;",">":"&gt;","&":"&amp;"}[s]))+'</a>').join("")+'</nav>';
 const anchor=main.querySelector("h1")||main.firstElementChild;if(anchor)anchor.insertAdjacentElement("afterend",box);
 const links=[...box.querySelectorAll("a")];if("IntersectionObserver" in window){const map=new Map(links.map(a=>[a.getAttribute("href").slice(1),a]));new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){links.forEach(a=>a.classList.remove("is-active"));const a=map.get(e.target.id);if(a)a.classList.add("is-active")}})},{rootMargin:"-15% 0px -70% 0px"}).observe; const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){links.forEach(a=>a.classList.remove("is-active"));const a=map.get(e.target.id);if(a)a.classList.add("is-active")}})},{rootMargin:"-15% 0px -70% 0px"});h2.forEach(h=>io.observe(h));}}
}
let sent50=false,sent90=false;addEventListener("scroll",()=>{const h=d.documentElement,max=h.scrollHeight-innerHeight;if(max<=0)return;const p=scrollY/max;if(typeof window.gtag==="function"){if(!sent50&&p>=.5){sent50=true;gtag("event","article_50_percent",{engagement_time_msec:1})}if(!sent90&&p>=.9){sent90=true;gtag("event","article_90_percent",{engagement_time_msec:1})}}},{passive:true});
})();