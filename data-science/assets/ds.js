(function(){
var bar=document.getElementById('bar');
function prog(){var h=document.documentElement;var s=h.scrollTop/(h.scrollHeight-h.clientHeight);bar.style.width=(Math.min(1,Math.max(0,s))*100)+'%'}
window.addEventListener('scroll',prog,{passive:true});prog();
document.querySelectorAll('.copy').forEach(function(b){b.addEventListener('click',function(){
var t=b.parentNode.querySelector('pre').innerText;
(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){b.textContent='Copied'}).catch(function(){
var r=document.createRange();r.selectNodeContents(b.parentNode.querySelector('pre'));var s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Selected'});
setTimeout(function(){b.textContent='Copy'},1600)})});
var links=[].slice.call(document.querySelectorAll('.toc a'));
if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){links.forEach(function(l){l.classList.toggle('on',l.getAttribute('href')==='#'+en.target.id)})}})},{rootMargin:'-20% 0px -70% 0px'});
document.querySelectorAll('article h2[id]').forEach(function(h){io.observe(h)})}
})();
