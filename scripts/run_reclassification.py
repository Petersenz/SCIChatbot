"""Run only after the scoped production rollout is approved; dry-run by default."""
import argparse,json,sys,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.db import Session
from backend.reclassify import validate,apply
from backend.reclassify_backup import capture
p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--apply',action='store_true');p.add_argument('--backup');a=p.parse_args()
plan=json.loads(Path(a.plan).read_text(encoding='utf-8-sig'))
with Session() as db:
 validate(db,plan,lock=a.apply)
 if not a.apply:
  print(json.dumps({'validated':True,'updates':len(plan['updates']),'retire':len(plan['retire']),'committed':False}));sys.exit(0)
 if not a.backup:raise SystemExit('--backup required')
 backup=capture(db,plan)
 fd=os.open(a.backup,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'w') as f:json.dump(backup,f,ensure_ascii=False)
 from backend.main import sync_doc
 try:
  apply(db,plan,sync_doc)
  db.commit()
 except Exception:
  db.rollback();raise
 print(json.dumps({'committed':True,'updates':len(plan['updates']),'retired':len(plan['retire'])}))
