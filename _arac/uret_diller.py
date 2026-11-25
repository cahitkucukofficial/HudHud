# index.html (Türkçe ana sayfa) -> /en/, /de/ ... dil sayfalarını, sitemap.xml'i üretir.
# Çalıştır: python3 _arac/uret_diller.py   (repo kökünden)
import re,json,os,glob
BASE='https://www.hudhudapps.com'
s=open('index.html',encoding='utf-8').read()

# 1) Ana sayfa JS: dil URL'den gelir; tarayıcı diline göre yönlendirme yalnız kökte
OLD_DET=s[s.index("var kd=null;"):s.index("dil=kd;")+len("dil=kd;")] if "var kd=null;" in s else None
if OLD_DET:
    NEW_DET=("var kd=document.documentElement.lang||'tr';"
    "if(kd==='tr'&&!/bot|crawl|spider|slurp|lighthouse/i.test(navigator.userAgent)){var sv=null,ds=null;try{sv=localStorage.getItem('dil');ds=sessionStorage.getItem('dilsec')}catch(e){}"
    "if(!ds){var nl=sv&&T[sv]?sv:((navigator.languages&&navigator.languages[0])||navigator.language||'tr').slice(0,2).toLowerCase();if(!T[nl])nl='en';"
    "if(nl!=='tr')location.replace('/'+nl+'/'+location.hash)}}\ndil=kd;")
    s=s.replace(OLD_DET,NEW_DET)
s=s.replace("b.onclick=function(){dil=d[0];kaydet('dil',dil);dilKapat();uygula()}",
 "b.onclick=function(){kaydet('dil',d[0]);try{sessionStorage.setItem('dilsec','1')}catch(e){}dilKapat();if(d[0]!==dil)location.href=(d[0]==='tr'?'/':'/'+d[0]+'/')+location.hash}")
s=s.replace("var md=$('meta[name=description]');if(md)md.content=t('hero_p');","")
open('index.html','w',encoding='utf-8').write(s)

s=re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">','',s)
s=re.sub(r'<meta property="og:locale" content="[^"]*">','',s)
# 2) T sözlüğü
i=s.index(',T={')+3; j=i
d=0
for k in range(i,len(s)):
    c=s[k]
    if c=='{':d+=1
    elif c=='}':
        d-=1
        if d==0:break
T=json.loads(s[i:k+1])
langs=[l for l in T if l!='tr']
def tt(l,key):
    return T.get(l,{}).get(key) or T['en'].get(key) or T['tr'].get(key)
def url(l): return BASE+'/' if l=='tr' else f'{BASE}/{l}/'
alts=''.join(f'<link rel="alternate" hreflang="{l}" href="{url(l)}">' for l in ['tr']+langs)+f'<link rel="alternate" hreflang="x-default" href="{url("en")}">'
OGL={'tr':'tr_TR','en':'en_US','de':'de_DE','fr':'fr_FR','es':'es_ES','it':'it_IT','ru':'ru_RU','pl':'pl_PL','pt':'pt_BR'}

def head(page,l):
    title=tt(l,'title')
    desc=re.search(r'<meta name="description" content="([^"]*)">',s).group(1) if l=='tr' else tt(l,'hero_p')
    desc=re.sub(r'<[^>]+>','',desc).replace('"','&quot;')
    title_e=title.replace('"','&quot;')
    page=re.sub(r'<html lang="tr"',f'<html lang="{l}"',page,count=1)
    page=re.sub(r'<title>.*?</title>',f'<title>{title}</title>',page,count=1)
    page=re.sub(r'<meta name="description" content="[^"]*">',f'<meta name="description" content="{desc}">',page,count=1)
    page=re.sub(r'<link rel="canonical" href="[^"]*">',f'<link rel="canonical" href="{url(l)}">'+alts,page,count=1)
    page=re.sub(r'(<meta property="og:title" content=")[^"]*',r'\g<1>'+title_e,page,count=1)
    page=re.sub(r'(<meta property="og:description" content=")[^"]*',r'\g<1>'+desc,page,count=1)
    page=re.sub(r'(<meta property="og:url" content=")[^"]*',r'\g<1>'+url(l),page,count=1)
    page=page.replace('<meta property="og:type" content="website">',f'<meta property="og:type" content="website"><meta property="og:locale" content="{OGL[l]}">',1)
    page=re.sub(r'(<meta name="twitter:title" content=")[^"]*',r'\g<1>'+title_e,page,count=1)
    page=re.sub(r'(<meta name="twitter:description" content=")[^"]*',r'\g<1>'+desc,page,count=1)
    return page

def bake(page,l):
    def f(m):
        key=m.group(3); v=tt(l,key)
        return m.group(0) if v is None else m.group(1)+v+m.group(4)
    return re.sub(r'(<(\w+)[^>]*\sdata-i="([^"]+)"[^>]*>)(?:.*?)(</\2>)',lambda m:(m.group(1)+(tt(l,m.group(3)) if tt(l,m.group(3)) is not None else '')+m.group(4)) if tt(l,m.group(3)) is not None else m.group(0),page,flags=re.S)

def absol(page):
    return re.sub(r'(\\?")((?:gorseller/[^"\\]+|[a-z\-]+\.html(?:#[^"\\]*)?))(?=\\?")',r'\1/\2',page)

# kök (tr)
root=head(s,'tr')
open('index.html','w',encoding='utf-8').write(root)
for l in langs:
    p=absol(bake(head(s,l),l))
    os.makedirs(l,exist_ok=True)
    open(f'{l}/index.html','w',encoding='utf-8').write(p)

# sitemap
pages=sorted(f for f in glob.glob('*.html') if f!='index.html')
x='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
for l in ['tr']+langs:
    x+=f'<url><loc>{url(l)}</loc>'+''.join(f'<xhtml:link rel="alternate" hreflang="{m}" href="{url(m)}"/>' for m in ['tr']+langs)+f'<xhtml:link rel="alternate" hreflang="x-default" href="{url("en")}"/></url>\n'
for p in pages: x+=f'<url><loc>{BASE}/{p}</loc></url>\n'
x+='</urlset>\n'
open('sitemap.xml','w').write(x)
print('ok',langs)
