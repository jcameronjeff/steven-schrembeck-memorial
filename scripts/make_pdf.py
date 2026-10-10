from pathlib import Path
from html.parser import HTMLParser
from html import escape
import json,re
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
ROOT=Path(__file__).resolve().parents[1];data=json.loads((ROOT/'output/pdf-content.json').read_text())
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleCustom',fontName='Times-Roman',fontSize=38,leading=41,textColor=colors.HexColor('#293c2d'),spaceAfter=22))
styles.add(ParagraphStyle(name='BodyCustom',fontName='Times-Roman',fontSize=11.5,leading=17,spaceAfter=11))
styles.add(ParagraphStyle(name='QuoteCustom',fontName='Times-Italic',fontSize=14,leading=19,leftIndent=17,spaceBefore=10,spaceAfter=16,textColor=colors.HexColor('#3d583d')))
styles.add(ParagraphStyle(name='SectionCustom',fontName='Times-Roman',fontSize=24,leading=28,spaceBefore=24,spaceAfter=15,keepWithNext=True))
styles.add(ParagraphStyle(name='SmallCustom',fontName='Helvetica',fontSize=8.5,leading=13,spaceAfter=10,textColor=colors.HexColor('#64695e')))
def clean(s):
 s=s.replace('❤️','[heart]').replace('😂','[laugh]').replace('\u2011','-').replace('✌️','').replace('…','...')
 return escape(s)
flow=[Spacer(1,35),Paragraph('Remembering<br/>Steven Schrembeck',styles['TitleCustom']),Paragraph('A curious mind. A generous soul.',styles['QuoteCustom']),Spacer(1,15),Image(str(ROOT/'site/assets/steven-schrembeck-family.jpg'),width=450,height=254),Spacer(1,22),Paragraph('Memories shared by friends and colleagues.',styles['BodyCustom']),Paragraph('Prepared October 10, 2026. A reading copy to keep and carry forward.',styles['SmallCustom'])]
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.target=None;self.buffer=[];self.quote=False
 def handle_starttag(self,tag,attrs):
  if tag=='blockquote':self.quote=True
  if tag in ['p','h2'] or tag=='span' and dict(attrs).get('class')=='when':self.target=tag;self.buffer=[]
 def handle_data(self,s):
  if self.target:self.buffer.append(s)
 def handle_endtag(self,tag):
  if tag==self.target:
   text=''.join(self.buffer).strip()
   if text:flow.append(Paragraph(clean(text),styles['SectionCustom' if tag=='h2' else 'SmallCustom' if tag=='span' else 'QuoteCustom' if self.quote else 'BodyCustom']))
   self.target=None
  if tag=='blockquote':self.quote=False
# The original first-person remembrance is linked, not reprinted.
flow += [PageBreak(),Paragraph('What stays with us',styles['TitleCustom']),Paragraph('Entries from the supplied Cox memorial export, saved October 10, 2026. Contributor names, wording, and assigned dates are retained. These dates describe memories, not a complete biography. Attachment images and two comment replies remain in the preservation archive.',styles['SmallCustom'])]
for p in data['posts']:
 if p['by'] in ['Jeff Cameron','Jefe']:continue
 by=('Steven, remembered by ' if p['type']=='words' else '')+p['by']
 by+=' - '+' '.join(str(p[k]) for k in ['month','year'] if p[k])
 flow.append(Paragraph(clean(by),styles['SectionCustom']))
 if p['context']:flow.append(Paragraph(clean(p['context']),styles['SmallCustom']))
 for para in p['text'].split('\n\n'):flow.append(Paragraph(clean(para),styles['QuoteCustom' if p['type']=='words' else 'BodyCustom']))
flow += [PageBreak(),Paragraph('Keep this with the collection',styles['SectionCustom']),Paragraph('This memory book preserves contributor wording from the supplied memorial entries. Jeff Cameron’s personal remembrance remains at its original URL and is not reprinted here. It does not contain the complete audio, video, writing, or photograph archive. Keep the website files, original collection, and caretaker instructions alongside it.',styles['BodyCustom']),Paragraph('Sources: Jeff Cameron’s remembrance at remembering-steven-schrembeck.opzero.sh, first published September 30, 2026; supplied Cox memorial export dated October 10, 2026. No dates of birth, missing biographical details, or new memories have been invented.',styles['SmallCustom'])]
def footer(c,d):
 c.setStrokeColor(colors.HexColor('#d9ddce'));c.line(54,45,558,45);c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#64695e'));c.drawString(54,30,'Remembering Steven Schrembeck');c.drawRightString(558,30,str(d.page))
p=ROOT/'site/downloads/remembering-steven.pdf'
SimpleDocTemplate(str(p),pagesize=(612,792),rightMargin=58,leftMargin=58,topMargin=52,bottomMargin=65,title='Remembering Steven Schrembeck',author='Collected by Jeff Cameron').build(flow,onFirstPage=footer,onLaterPages=footer)
print(p)
