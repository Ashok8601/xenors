from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
DIST=ROOT/'dist'
if DIST.exists(): shutil.rmtree(DIST)
DIST.mkdir()
EX_DIR={'.git','dist','config','docs','tools','scripts','Design','__pycache__'}
EX_FILES={'build.py','validate_site.py','publish.py','render.yaml','requirements.txt','req.txt','README.md','DEPLOY_README.md','SEO_DEPLOY_README.txt','SEO_REPAIR_REPORT_2026-10-12.md','XENORS_SEO_TECHNICAL_AUDIT.md','SEO_VALIDATION_REPORT.txt','SEO_AUDIT_REPORT.csv','GSC_CRAWLED_NOT_INDEXED_READINESS.csv','GSC_LEGACY_URL_FIX_MAP.csv','GSC_NOINDEX_REVIEW.csv','FINAL_STATIC_AUDIT.json','AUDIT_FIX_SUMMARY.txt','FINAL_REPAIR_AUDIT.json','html.zip'}
ALLOWED={'.html','.css','.js','.xml','.txt','.json','.webmanifest','.png','.jpg','.jpeg','.webp','.gif','.svg','.ico','.mp4','.webm','.woff','.woff2'}
for p in ROOT.rglob('*'):
    if not p.is_file(): continue
    rel=p.relative_to(ROOT)
    if any(part in EX_DIR for part in rel.parts): continue
    if p.name in EX_FILES: continue
    if p.suffix.lower() not in ALLOWED and p.name not in {'ads.txt','robots.txt','_redirects'}: continue
    out=DIST/rel; out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,out)
print('Published',sum(1 for x in DIST.rglob('*') if x.is_file()),'files')
