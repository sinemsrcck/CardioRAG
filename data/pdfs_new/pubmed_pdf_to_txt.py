# -*- coding: utf-8 -*-
"""PDF makalelerinden örnekteki biçimde TXT metadata + abstract üretir; PDF'leri silmez."""
import re, time, xml.etree.ElementTree as ET
from pathlib import Path
try:
    import fitz
    import requests
except ImportError as exc:
    print('Eksik paket:', exc, '\nTXT_DONUSTUR_BASLAT.bat dosyasını çalıştırıp tekrar deneyin.')
    input('Çıkmak için Enter...'); raise SystemExit(1)
BASE=Path(__file__).resolve().parent
OUT=BASE/'TXT_ciktilari'; OUT.mkdir(exist_ok=True)
EUTILS='https://eutils.ncbi.nlm.nih.gov/entrez/eutils'
HEAD={'User-Agent':'PDF-to-PubMed-TXT/1.0'}
def clean(s): return re.sub(r'\s+',' ',s or '').strip()
def pdftext(p):
    try:
        with fitz.open(p) as d: return '\n'.join(pg.get_text('text') for pg in d[:3])
    except Exception as e: print('PDF okunamadı:',p.name,e); return ''
def ids(text, filename):
    t=text+'\n'+filename
    a=re.search(r'\bPMID\s*[:#]?\s*(\d{6,9})\b',t,re.I)
    b=re.search(r'\bPMC\d{5,10}\b',t,re.I)
    c=re.search(r'\b10\.\d{4,9}/[^\s<>"\]]+',t,re.I)
    return (a.group(1) if a else '', b.group(0).upper() if b else '', c.group(0).rstrip('.,;:)').lower() if c else '')
def find_pmid(pmid,pmcid,doi):
    if pmid: return pmid
    terms=([f'"{doi}"[AID]',f'"{doi}"[DOI]'] if doi else [])+([f'"{pmcid}"[pmc]'] if pmcid else [])
    for term in terms:
        try:
            r=requests.get(EUTILS+'/esearch.fcgi',params={'db':'pubmed','term':term,'retmode':'json'},headers=HEAD,timeout=25); r.raise_for_status()
            ids_=r.json().get('esearchresult',{}).get('idlist',[])
            if ids_: return ids_[0]
        except Exception: pass
    return ''
def record(pmid):
    if not pmid:return None
    try:
        r=requests.get(EUTILS+'/efetch.fcgi',params={'db':'pubmed','id':pmid,'retmode':'xml'},headers=HEAD,timeout=30); r.raise_for_status()
        root=ET.fromstring(r.content); art=root.find('.//PubmedArticle')
        if art is None:return None
        def tx(path):
            e=art.find(path); return clean(' '.join(e.itertext())) if e is not None else ''
        title=tx('.//ArticleTitle'); authors=[]
        for a in art.findall('.//AuthorList/Author'):
            collective=a.findtext('CollectiveName')
            if collective: authors.append(clean(collective)); continue
            last=clean(a.findtext('LastName','')); fore=clean(a.findtext('ForeName','') or a.findtext('Initials',''))
            name=' '.join(x for x in (last,fore) if x)
            if name: authors.append(name)
        journal=tx('.//Journal/Title'); year=tx('.//Journal/JournalIssue/PubDate/Year')
        if not year:
            md=tx('.//Journal/JournalIssue/PubDate/MedlineDate'); m=re.search(r'\b(?:19|20)\d{2}\b',md); year=m.group(0) if m else ''
        abstract=[]
        for e in art.findall('.//Abstract/AbstractText'):
            label=clean(e.attrib.get('Label','') or e.attrib.get('NlmCategory','')); val=clean(' '.join(e.itertext()))
            if val: abstract.append(f'{label}: {val}' if label else val)
        pmcid=doi=''
        for e in art.findall('.//PubmedData/ArticleIdList/ArticleId'):
            typ=e.attrib.get('IdType','').lower(); val=clean(''.join(e.itertext()))
            if typ=='pmc':pmcid=val.upper()
            elif typ=='doi':doi=val
        types=[clean(''.join(e.itertext())) for e in art.findall('.//PublicationTypeList/PublicationType')]
        mesh=[clean(''.join(e.itertext())) for e in art.findall('.//MeshHeading/DescriptorName')]
        return dict(title=title,authors=authors,journal=journal,year=year,pmid=pmid,pmcid=pmcid,doi=doi,
          doi_link=('https://doi.org/'+doi if doi else ''),pubmed_link='https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/',
          pmc_link=('https://pmc.ncbi.nlm.nih.gov/articles/'+pmcid+'/' if pmcid else ''),types=types,mesh=mesh,abstract='\n'.join(abstract))
    except Exception as e: print('PubMed kaydı alınamadı:',pmid,e); return None
def fallback(p,text,pmid,pmcid,doi):
    lines=[clean(x) for x in text.splitlines() if clean(x)]
    title=next((x for x in lines[:35] if len(x)>25 and not re.search(r'^(abstract|background|introduction|doi|https?://)',x,re.I)),p.stem)
    return dict(title=title,authors=[],journal='',year='',pmid=pmid,pmcid=pmcid,doi=doi,doi_link='https://doi.org/'+doi if doi else '',pubmed_link='https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/' if pmid else '',pmc_link='https://pmc.ncbi.nlm.nih.gov/articles/'+pmcid+'/' if pmcid else '',types=[],mesh=[],abstract='')
def format_record(d):
    return '\n'.join([f"BASLIK: {d['title']}",f"YAZARLAR: {'; '.join(d['authors'])}",f"DERGI: {d['journal']}",f"YIL: {d['year']}",f"PMID: {d['pmid']}",f"PMCID: {d['pmcid']}",f"DOI: {d['doi']}",f"DOI LINK: {d['doi_link']}",f"PUBMED LINK: {d['pubmed_link']}",f"PMC LINK: {d['pmc_link']}",f"YAYIN TURLERI: {'; '.join(d['types'])}",f"MESH TERIMLERI: {'; '.join(d['mesh'])}",'','='*70,'ABSTRACT:',d['abstract']]).rstrip()+'\n'
def main():
    pdfs=sorted(p for p in BASE.rglob('*.pdf') if OUT not in p.parents)
    if not pdfs:
        print('PDF bulunamadı. PDF dosyalarını bu betiğin bulunduğu klasöre veya alt klasörlerine koyun.'); input('Çıkmak için Enter...'); return
    print(f'{len(pdfs)} PDF bulundu. TXT dosyaları {OUT} klasörüne yazılacak. PDF’ler silinmeyecek.\n')
    report=['PDF_DOSYASI\tTXT_DOSYASI\tDURUM\tPMID']; ok=0
    for i,p in enumerate(pdfs,1):
        print(f'[{i}/{len(pdfs)}] {p.name}')
        txt=pdftext(p); pmid,pmcid,doi=ids(txt,p.name); pid=find_pmid(pmid,pmcid,doi); d=record(pid)
        if d:
            d['pmcid']=d['pmcid'] or pmcid; d['doi']=d['doi'] or doi
            d['doi_link']=d['doi_link'] or ('https://doi.org/'+d['doi'] if d['doi'] else '')
            d['pmc_link']=d['pmc_link'] or ('https://pmc.ncbi.nlm.nih.gov/articles/'+d['pmcid']+'/' if d['pmcid'] else '')
            status='PubMed kaydından oluşturuldu'
        else: d=fallback(p,txt,pmid,pmcid,doi); status='Kısmi: PubMed kaydı bulunamadı; kontrol edin'
        out=OUT/(p.stem+'.txt')
        try: out.write_text(format_record(d),encoding='utf-8'); ok+=1; report.append(f'{p.name}\t{out.name}\t{status}\t{d["pmid"]}'); print(' -> TXT oluşturuldu:',status)
        except Exception as e: report.append(f'{p.name}\t\tHATA: {e}\t{d.get("pmid","")}'); print(' -> HATA:',e)
        time.sleep(.35)
    (OUT/'donusturme_raporu.tsv').write_text('\n'.join(report),encoding='utf-8')
    print(f'\nBitti: {ok}/{len(pdfs)} TXT oluşturuldu. Çıktı: {OUT}'); print('Kısmi kayıtları donusturme_raporu.tsv dosyasından kontrol edin.'); input('Pencereyi kapatmak için Enter...')
if __name__=='__main__': main()
