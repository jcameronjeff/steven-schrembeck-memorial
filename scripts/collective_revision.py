from pathlib import Path
p=Path(__file__).with_name('build.py');s=p.read_text()
s=s.replace("page('story.html','The person behind the glasses',head('His story','The person behind<br>the glasses.',story_intro)","page('remembrance-jeff.html','A remembrance by Jeff Cameron',head('A shared remembrance','Remembering a friend.',story_intro)")
start=s.index('<section class="section story-grid">')
end=s.index('<section class="voice"',start)
s=s[:start]+'''<section class="section story-grid"><div><p class="eyebrow">The person behind the glasses</p><h2 style="margin-top:16px">A different way<br>of seeing.</h2><div class="portrait-label"><img src="assets/steven-schrembeck.jpg" alt="Steven in his green glasses" width="62" height="62" loading="lazy"><div>Engineer. Writer. Storyteller.<span>Husband, father, and friend.</span></div></div></div><div class="story-prose"><p>Steven brought a designer’s eye to his work and a restless curiosity to the world. He built interfaces, imagined other worlds, and followed questions wherever they led.</p><p>To the people around him, he was also the person who made time. The encouraging voice. The offer to help. The colleague whose colorful glasses could make you smile.</p><a class="text-link" href="story.html">More about Steven <span aria-hidden="true">→</span></a></div></section>
''' +s[end:]
s=s.replace("'“If you only read one thing here, read him.”<br><span class=\"small\">— Jeff Cameron</span>'","'Essays, imagined worlds, and questions worth following. A place to meet Steven through the things he made.'")
s=s.replace('“Man am I going to miss those glasses.”<br>— Jeff Cameron','Steven, and those unmistakable green glasses.')
s=s.replace('A remembrance by his friend Jeff Cameron. The original words, collected here with love.','One friend’s remembrance, part of a wider collection of memories.')
s=s.replace("ROOT/'output/pdf-content.json'","ROOT/'output/pdf-content.json'")
s=s.replace('This local preview has not been published.','Each contribution is one person’s recollection. The collection makes room for all of them.')
s=s.replace('Colleague memories and workplace materials need a publication decision before this local preview becomes public.','Original materials and their source notes remain available in the complete collection.')
p.write_text(s)
