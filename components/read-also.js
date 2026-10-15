(() => {
  "use strict";
  function init(section){
    if(!section || section.dataset.ready==="1") return;
    section.dataset.ready="1";
    const button=section.querySelector("[data-view-more]");
    const items=[...section.querySelectorAll(".xenors-related-item")];
    if(!button || !items.length) return;
    const batch=Number(button.dataset.batchSize||10);
    const hidden=()=>items.filter(x=>x.hidden);
    const update=()=>{
      const left=hidden().length;
      if(left<=0){button.hidden=true;button.setAttribute("aria-expanded","true");return;}
      const n=Math.min(batch,left);
      button.hidden=false;
      button.textContent=`View More (${n})`;
      button.setAttribute("aria-expanded","false");
    };
    button.addEventListener("click",()=>{
      const next=hidden().slice(0,batch);
      next.forEach(x=>{x.hidden=false;x.setAttribute("aria-hidden","false");});
      update();
      if(next.length) next[0].scrollIntoView({behavior:"smooth",block:"nearest"});
    });
    update();
  }
  const start=()=>document.querySelectorAll('[data-xenors-build="read-also"]').forEach(init);
  document.readyState==="loading"?document.addEventListener("DOMContentLoaded",start):start();
})();
