import numpy as np, math
from PIL import Image, ImageDraw
D='art/시안/무기/'; names=['01-목검','02-녹슨검','03-수습기사의검','04-경비대의칼']
TIP=(212,918); POM=(805,645); ANG=math.degrees(math.atan2(918-645,805-212)); LEN=math.hypot(805-212,918-645)
HAND=[(690,615),(745,613),(752,663),(738,698),(722,723),(690,721),(672,698),(670,668),(688,653)]
def hold(g, fn, k=1.0):
    base=Image.open('art/knight/기본-%s.png'%g).convert('RGBA'); a=np.asarray(base).copy()
    # 옛 검에서 몸 밖으로 나온 날 부분을 지운다
    ux,uy=(TIP[0]-POM[0])/LEN,(TIP[1]-POM[1])/LEN
    yy,xx=np.mgrid[0:1024,0:1024]; t=(xx-POM[0])*ux+(yy-POM[1])*uy; dist=np.abs((xx-POM[0])*uy-(yy-POM[1])*ux)
    a[(dist<16)&(t>0)&(xx<452)]=0
    a[(dist<26)&(t<30)&(xx>752)]=0     # 손 뒤로 나온 손잡이 끝
    body=Image.fromarray(a)
    s=Image.open(D+fn+'.png'); L=int((LEN+18)*k); s=s.resize((L,int(s.height*L/s.width)),Image.LANCZOS)
    C=1600; cv=Image.new('RGBA',(C,C),(0,0,0,0)); cv.alpha_composite(s,(C//2-L,C//2-s.height//2))
    cv=cv.rotate(ANG,resample=Image.BICUBIC)
    out=body.copy(); lay=Image.new('RGBA',(1024,1024),(0,0,0,0))
    px,py=POM[0]+12-C//2,POM[1]-6-C//2
    lay.paste(cv,(px,py)); out.alpha_composite(lay)
    m=Image.new('L',(1024,1024),0); ImageDraw.Draw(m).polygon(HAND,fill=255)
    out.paste(base,(0,0),Image.composite(base.getchannel('A'),Image.new('L',(1024,1024),0),m))
    return out.crop((150,30,930,940))
def sheet(cells,path,cols):
    w,h=cells[0].size; rows=(len(cells)+cols-1)//cols
    sh=Image.new('RGBA',(w*cols,h*rows),(34,48,32,255))
    for i,c in enumerate(cells): sh.alpha_composite(c,((i%cols)*w,(i//cols)*h))
    sh=sh.resize((sh.width//2,sh.height//2),Image.LANCZOS); sh.convert('RGB').save(path)
sheet([hold(g,n) for g in '남여' for n in names],D+'일반-손에든모습.png',4)
sheet([hold('남','03-수습기사의검',k) for k in (1.0,0.85,0.7)],D+'일반-길이비교.png',3)
