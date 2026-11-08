(()=>{"use strict";
const cfg=window.XENORS_SUBSCRIBE_CONFIG||{};
function showFollow(){const f=document.querySelector(".x-follow");if(f)f.hidden=false}
function maybeFollow(){const h=document.documentElement.scrollHeight-innerHeight;if(h>0&&scrollY/h>=.45)showFollow()}
document.addEventListener("DOMContentLoaded",()=>{
 addEventListener("scroll",maybeFollow,{passive:true});setTimeout(showFollow,45000);maybeFollow();
 document.addEventListener("click",e=>{
  if(e.target.closest("[data-push-follow]")){
   if(!cfg.oneSignalAppId){alert("Web push is not configured yet.");return}
   if(!document.querySelector("[data-x-onesignal]")){
    const s=document.createElement("script");s.src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js";s.defer=true;s.dataset.xOnesignal="1";document.head.appendChild(s);
   }
   window.OneSignalDeferred=window.OneSignalDeferred||[];window.OneSignalDeferred.push(async O=>{await O.init({appId:cfg.oneSignalAppId,serviceWorkerPath:"/OneSignalSDKWorker.js"});await O.Notifications.requestPermission()});
  }
 });
 const form=document.querySelector("[data-email-subscribe]");
 if(form){if(cfg.emailFormAction)form.action=cfg.emailFormAction;else form.addEventListener("submit",e=>{e.preventDefault();alert("Email subscription is not configured yet.")})}
});
})();