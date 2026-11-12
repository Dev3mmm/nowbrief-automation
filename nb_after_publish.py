"""NOWBRIEF server-side helper (runs on GitHub Actions, PC can be off).
1. Kicks wp-cron when a scheduled post is overdue.
2. For every task in tasks.json: once `when_published` post is live, appends the related-link paragraph to the older posts (idempotent via marker URL)."""
import os,json,datetime as dt,requests
S=requests.Session(); S.auth=(os.environ['WP_USER'],os.environ['WP_APP_PASSWORD'])
B='https://nowbrief.news/wp-json/wp/v2'
now=dt.datetime.now(dt.timezone.utc)
fut=S.get(B+'/posts',params={'status':'future','per_page':50,'_fields':'id,date_gmt'}).json()
over=[p['id'] for p in fut if dt.datetime.fromisoformat(p['date_gmt']).replace(tzinfo=dt.timezone.utc)<now]
if over:
    print('overdue scheduled posts',over,'-> kicking wp-cron')
    for u in ('https://nowbrief.news/','https://nowbrief.news/wp-cron.php?doing_wp_cron'): requests.get(u,timeout=40)
tasks=json.load(open('tasks.json'))
open_tasks=0
for t in tasks:
    st=S.get(f"{B}/posts/{t['when_published']}",params={'_fields':'status,link'}).json()
    if st.get('status')!='publish': open_tasks+=1; print(t['when_published'],'not live yet:',st.get('status')); continue
    for a in t['add_to']:
        raw=S.get(f"{B}/posts/{a['post']}",params={'context':'edit','_fields':'content'}).json()['content']['raw']
        if a['marker'] in raw: print(a['post'],'already linked'); continue
        blk=f"\n\n<!-- wp:paragraph -->\n<p>{a['html']}</p>\n<!-- /wp:paragraph -->"
        r=S.post(f"{B}/posts/{a['post']}",json={'content':raw.rstrip()+blk}); print(a['post'],'linked',r.status_code)
print('open tasks:',open_tasks)
