document.querySelectorAll('.copy').forEach(b=>b.addEventListener('click',()=>{const p=b.closest('.code').querySelector('pre');navigator.clipboard.writeText(p.innerText);b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1200)}));addEventListener('scroll',()=>{const d=document.documentElement;const max=d.scrollHeight-d.clientHeight;document.querySelector('.progress').style.width=(max?100*d.scrollTop/max:0)+'%'});

document.addEventListener('click',function(e){
 if(e.target.matches('.try-copy')){const t=e.target.closest('.trybox').querySelector('textarea');navigator.clipboard.writeText(t.value);e.target.textContent='Copied';setTimeout(()=>e.target.textContent='Copy starter code',1200)}
 if(e.target.matches('.try-reset')){const t=e.target.closest('.trybox').querySelector('textarea');t.value=t.dataset.original||t.defaultValue}
});
document.querySelectorAll('.trybox textarea').forEach(t=>t.dataset.original=t.value);
