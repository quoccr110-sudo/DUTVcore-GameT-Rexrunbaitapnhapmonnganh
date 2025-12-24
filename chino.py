import pygame, os, random, sys

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("T-Rex Run")
FONT = pygame.font.Font('freesansbold.ttf', 20)
FONT_BIG = pygame.font.Font('freesansbold.ttf', 30)

def get_path(f, n):
    for p in [os.path.join(f, n), os.path.join("Assets", f, n)]:
        if os.path.exists(p): return p
    return os.path.join(f, n)

def get_score(): return int(open("highscore.txt","r").read()) if os.path.exists("highscore.txt") else 0
def save_score(s): open("highscore.txt","w").write(str(s)) if s > get_score() else None

# Load Assets
try:
    RUN = [pygame.image.load(get_path("Dino", f"DinoRun{i}.png")) for i in (1,2)]
    JUMP = pygame.image.load(get_path("Dino", "DinoJump.png"))
    DUCK = [pygame.image.load(get_path("Dino", f"DinoDuck{i}.png")) for i in (1,2)]
    S_CAC = [pygame.image.load(get_path("Cactus", f"SmallCactus{i}.png")) for i in (1,2,3)]
    L_CAC = [pygame.image.load(get_path("Cactus", f"LargeCactus{i}.png")) for i in (1,2,3)]
    BIRD = [pygame.image.load(get_path("Bird", f"Bird{i}.png")) for i in (1,2)]
    CLOUD, BG = pygame.image.load(get_path("Other", "Cloud.png")), pygame.image.load(get_path("Other", "Track.png"))
except Exception as e: print(f"Loi: {e}"); pygame.quit(); sys.exit()

class Bullet:
    def __init__(self, x, y): self.rect = pygame.Rect(x, y, 20, 10)
    def update(self): self.rect.x += 20
    def draw(self, s): pygame.draw.rect(s, (255,0,0), self.rect)

class Dino:
    def __init__(self, x, y, c):
        self.x, self.yb, self.c = x, y, c
        self.yd = y + 35
        self.run_i, self.duck_i, self.jump_i = RUN, DUCK, JUMP
        self.img = self.run_i[0]
        self.rect = self.img.get_rect(); self.rect.x, self.rect.y = x, y
        self.jv, self.step, self.state = 8.5, 0, "run"
        self.ammo, self.shld, self.god, self.dead, self.tiny = 5, 0, 0, 0, 0
        self.spc, self.moon = 0, 0

    def update(self, ui, pts):
        if self.dead: return
        if pts>=6000 and not self.tiny:
            self.tiny=1; self.yb+=20; self.yd+=20
            self.run_i=[pygame.transform.scale(i,(44,47)) for i in RUN]
            self.duck_i=[pygame.transform.scale(i,(59,30)) for i in DUCK]
            self.jump_i=pygame.transform.scale(JUMP,(44,47))
            self.rect = self.img.get_rect(); self.rect.x = self.x

        if self.state != "jump":
            if ui[self.c['jump']]: self.state = "jump"
            elif ui[self.c['duck']]: self.state = "duck"
            else: self.state = "run"

        if self.state=="jump":
            self.img=self.jump_i; g,m = (0.15,2.5) if self.spc else ((0.4,5.2) if self.moon else (0.8,4))
            self.rect.y-=self.jv*m; self.jv-=g
            if self.jv<-8.5: 
                self.state, self.jv = "run", 8.5
                self.rect.y = self.yb 
        
        elif self.state=="duck": 
            self.img=self.duck_i[self.step//5]; self.rect=self.img.get_rect()
            self.rect.x, self.rect.y = self.x, self.yd
        else: 
            self.img=self.run_i[self.step//5]; self.rect=self.img.get_rect()
            self.rect.x, self.rect.y = self.x, self.yb

        self.step=(self.step+1)%10; self.mask=pygame.mask.from_surface(self.img)

    def draw(self, s):
        if self.dead: return
        s.blit(self.img, self.rect)
        if self.shld: pygame.draw.circle(s,(0,100,255),self.rect.center,25 if self.tiny else 50,4)
        if self.god: 
            pygame.draw.circle(s, (255, 215, 0), self.rect.center, 30 if self.tiny else 60, 4)
            s.blit(pygame.font.Font('freesansbold.ttf', 10).render("GOD", 1, (255, 215, 0)), (self.rect.x, self.rect.y - 20))

class Obj:
    def __init__(self, x, y, img): self.rect=img.get_rect(); self.rect.x, self.rect.y, self.img = x, y, img
    def draw(self, s): s.blit(self.img, self.rect)

class Item:
    def __init__(self, yb, tp): self.yb, self.tp, self.act, self.rect = yb, tp, 0, pygame.Rect(0,0,40,40); self.reset([],0)
    def reset(self, obs, pts):
        if self.tp=="portal" and pts<10000: self.act=0; return
        self.act=1; rng={"portal":(5,15),"ammo":(10,20),"atk":(10,25),"x2":(15,25),"shield":(30,50),"slow":(15,30)}
        while True:
            self.x=SCREEN_WIDTH+random.randint(*rng[self.tp])*1000
            if all(abs(self.x-o.rect.x)>400 for o in obs): break
        self.y=self.yb-50 if self.tp=="portal" else random.randint(self.yb-100,self.yb-30)
        self.rect=pygame.Rect(self.x,self.y,60 if self.tp=="portal" else 40, 80 if self.tp=="portal" else 40)
    def update(self, spd, obs, pts):
        if not self.act: return
        self.rect.x-=spd
        if self.rect.x<-100: self.reset(obs, pts)
    def draw(self, s):
        if not self.act: return
        f=pygame.font.Font('freesansbold.ttf',12); t=self.tp; r=self.rect
        if t=="portal": pygame.draw.ellipse(s,(138,43,226),r,5); s.blit(f.render("PORTAL",1,(255,255,255)),(r.x+5,r.y-15))
        elif t=="ammo": pygame.draw.circle(s,(255,0,0),r.center,15); s.blit(pygame.font.Font('freesansbold.ttf',15).render("+3",1,(255,255,255)),(r.x+10,r.y+10))
        elif t=="atk": pygame.draw.rect(s,(128,0,128),r); s.blit(f.render("ATK",1,(255,255,255)),(r.x+10,r.y+15))
        elif t=="x2": pygame.draw.circle(s,(255,215,0),r.center,20); s.blit(pygame.font.Font('freesansbold.ttf',16).render("x2",1,(0,0,0)),(r.x+10,r.y+12))
        elif t=="shield": pygame.draw.circle(s,(0,100,255),r.center,20); s.blit(f.render("SHIELD",1,(255,255,255)),(r.x+2,r.y+14))
        elif t=="slow": pygame.draw.rect(s,(0,255,0),r); s.blit(f.render("SLOW",1,(0,0,0)),(r.x+2,r.y+12))

class Obstacle:
    def __init__(self, img, tp, y_offset, y_base):
        self.img, self.tp = img, tp
        self.rect=self.img[self.tp].get_rect(); self.rect.x=SCREEN_WIDTH
        
        # Position Fix (DA CHINH SUA DO CAO CHIM)
        if self.img == S_CAC: self.rect.y = y_base - 15
        elif self.img == L_CAC: self.rect.y = y_base - 25
        elif self.img == BIRD: self.rect.y = y_base - 65 # <-- Ha thap xuong (cu la 85)
        
        self.mask=pygame.mask.from_surface(self.img[self.tp])

    def update(self, spd):
        self.rect.x-=spd
        return self.rect.x<-self.rect.width
    def draw(self, s): s.blit(self.img[self.tp], self.rect)

class GameState:
    def __init__(self, yf, hl, yb, ctrl, pid):
        self.yf, self.h, self.yb = yf, hl, yb; self.p=Dino(80,yb,ctrl)
        self.obs, self.bul, self.bgx = [], [], 0; self.itm=[Item(yb,t) for t in ["ammo","shield","x2","slow","portal","atk"]]
        self.spd, self.ospd, self.pts, self.mult = 14, 14, 0, 1
        self.tm={"spc":0,"slo":0,"bst":0,"mul":0}; self.dead, self.win, self.pid = 0, 0, pid
        self.cld=[Obj(SCREEN_WIDTH+i*400,random.randint(yf+20,yf+80),CLOUD) for i in range(2)]
        self.stars=[Obj(random.randint(0,900),random.randint(0,hl)+yf,pygame.Surface((2,2))) for _ in range(20)]

    def update(self, ui):
        if self.dead: return
        self.pts+=1*self.mult
        if self.pts%200==0 and self.tm["slo"]<=0 and self.tm["bst"]<=0: self.spd+=1; self.ospd=self.spd
        self.tm["slo"]=max(0,self.tm["slo"]-1); self.spd=8 if self.tm["slo"] else (30 if self.tm["bst"] else self.ospd)
        self.tm["bst"]=max(0,self.tm["bst"]-1); self.tm["mul"]=max(0,self.tm["mul"]-1); self.mult=2 if self.tm["mul"] else 1
        self.tm["spc"]=max(0,self.tm["spc"]-1); self.p.spc=1 if self.tm["spc"] else 0; 
        
        if not self.p.spc and self.p.rect.y != self.p.yb and self.p.state != "jump": self.p.rect.y = self.p.yb
            
        self.p.moon=1 if 2500<=self.pts<=3000 else 0
        self.p.update(ui, self.pts)
        
        for b in self.bul: b.update(); self.bul.remove(b) if b.rect.x>SCREEN_WIDTH else None
        if not self.obs:
            if self.p.spc: self.obs.append(Obstacle(BIRD,0,self.yf,self.yb)) if random.randint(0,50)==0 else None
            else:
                r=random.randint(0,2)
                if r==0: self.obs.append(Obstacle(S_CAC,random.randint(0,2),self.yf,self.yb))
                elif r==1: self.obs.append(Obstacle(L_CAC,random.randint(0,2),self.yf,self.yb))
                else: self.obs.append(Obstacle(BIRD,0,self.yf,self.yb))
        
        for o in self.obs: 
            o.rect.x-=self.spd; self.obs.remove(o) if o.rect.x<-100 else None
            if o.img == BIRD: o.tp = (self.pts//5)%2 
        
        for i in self.itm: i.update(self.spd, self.obs, self.pts); i.reset(self.obs, self.pts) if not i.act and random.randint(0,100)==0 else None
        
        return self.col()

    def col(self):
        pr=self.p.rect
        for b in self.bul[:]:
            for o in self.obs[:]: 
                if b.rect.colliderect(o.rect): self.bul.remove(b); self.obs.remove(o); break
        for i in self.itm:
            if i.act and pr.colliderect(i.rect):
                if i.tp=="atk": return "atk"
                i.act=0; i.reset(self.obs,self.pts)
                if i.tp=="x2": self.mult=2; self.tm["mul"]=150
                elif i.tp=="shield": self.p.shld=1
                elif i.tp=="ammo": self.p.ammo+=3
                elif i.tp=="slow": self.ospd=self.spd; self.tm["slo"]=150
                elif i.tp=="portal": self.p.spc=1; self.tm["spc"]=500; self.obs.clear()
        for o in self.obs:
            if pr.colliderect(o.rect):
                if not self.p.god and self.p.mask.overlap(o.mask,(o.rect.x-pr.x,o.rect.y-pr.y)):
                    if self.p.shld: self.p.shld=0; self.obs.remove(o)
                    else: self.dead=1; save_score(self.pts)
        return None

    def draw(self, s, f):
        if self.p.spc: 
            s.fill((0,0,20),(0,self.yf,SCREEN_WIDTH,self.h))
            [pygame.draw.circle(s,(255,255,255),(st.rect.x,st.rect.y),2) for st in self.stars]
        else:
            bgc=(255,255,255)
            if 1000<=self.pts<=1500: bgc=(15,10,35)
            elif (self.pts//700)%2: bgc=(30,30,30)
            s.fill(bgc,(0,self.yf,SCREEN_WIDTH,self.h))
            
            # Hieu ung hinh anh (Da khoi phuc)
            if 1000<=self.pts<=1500:
                for _ in range(5): pygame.draw.rect(s, (0, 255, 255), (random.randint(0, SCREEN_WIDTH), random.randint(self.yf, self.yf + self.h), random.randint(50, 150), 2))
            if 4000<=self.pts<=4200:
                for _ in range(3): pygame.draw.rect(s, (100, 100, 100), (random.randint(0, SCREEN_WIDTH), random.randint(self.yf, self.yf + self.h), 50, 10))

            s.blit(BG,(self.bgx,self.yb+50)); s.blit(BG,(self.bgx+BG.get_width(),self.yb+50))
            self.bgx-=self.spd; self.bgx=0 if self.bgx<=-BG.get_width() else self.bgx
            for c in self.cld: c.rect.x-=self.spd; s.blit(c.img,c.rect); c.rect.x=SCREEN_WIDTH+random.randint(0,500) if c.rect.x<-100 else c.rect.x
        
        [x.draw(s) for x in self.obs+self.itm+self.bul]; self.p.draw(s)
        tc=(255,255,255) if 1000<=self.pts<=1500 or (self.pts//700)%2 or self.p.spc else (0,0,0)
        yui=20 if self.yf==0 else SCREEN_HEIGHT//2+20
        s.blit(f.render(f"P{self.pid}: {self.pts}  Ammo: {self.p.ammo}",1,tc),(20 if self.pid==1 else 700,yui))
        if self.tm["bst"]: s.blit(f.render("SPEED UP!",1,(255,0,0)),(400,yui))
        if self.dead: s.blit(f.render("GAME OVER",1,(255,0,0)),(SCREEN_WIDTH//2-60,yui+30))
        if self.win: s.blit(f.render("WINNER",1,(0,255,0)),(SCREEN_WIDTH//2-50,yui+60))

def main(mode):
    clk=pygame.time.Clock(); f=FONT
    c1={'jump':pygame.K_UP,'duck':pygame.K_DOWN,'shoot':pygame.K_RIGHT}
    gms=[GameState(0,600,380,c1,1)] if mode==1 else [GameState(0,300,200,c1,1),GameState(300,300,500,{'jump':pygame.K_w,'duck':pygame.K_s,'shoot':pygame.K_d},2)]
    while True:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_g: [setattr(g.p,'god',not g.p.god) for g in gms]
                for g in gms:
                    if e.key==g.p.c['shoot'] and g.p.ammo>0: g.bul.append(Bullet(g.p.rect.x+30,g.p.rect.y+20)); g.p.ammo-=1
        SCREEN.fill((255,255,255)); pygame.draw.line(SCREEN,(0,0,0),(0,300),(900,300),5) if mode==2 else None
        k=pygame.key.get_pressed(); alv=0
        for i,g in enumerate(gms):
            r=g.update(k); g.draw(SCREEN,f); alv+=1 if not g.dead else 0
            if r=="atk" and mode==2: g.itm[5].act=0; g.itm[5].reset(g.obs,g.pts); t=gms[1-i]; t.ospd=t.spd; t.tm["bst"]=90
        if mode==1 and gms[0].dead: pygame.display.update(); pygame.time.delay(1000); return
        if mode==2 and alv<2: gms[1 if gms[0].dead else 0].win=1; gms[1 if gms[0].dead else 0].draw(SCREEN,f); pygame.display.update(); pygame.time.delay(2000); return
        clk.tick(30); pygame.display.update()

def help_screen():
    while True:
        SCREEN.fill((255,255,255)); f, fb = pygame.font.Font('freesansbold.ttf', 15), FONT_BIG
        SCREEN.blit(fb.render("HUONG DAN TRO CHOI",1,(0,0,0)),(300,30))
        lines=["PHIM 1: 1 NGUOI | PHIM 2: 2 NGUOI (PvP)","P1: MUI TEN | P2: W/S/D","G: GOD MODE | ESC: BACK","VAT PHAM:"]
        for i,l in enumerate(lines): SCREEN.blit(f.render(l,1,(0,0,0)),(50,80+i*25))
        idat=[((255,215,0),"c","X2 (Vang)"),((0,100,255),"c","KHIEN (Xanh)"),((255,0,0),"r","DAN +3 (Do)"),((0,255,0),"r","CHAM (La)"),((128,0,128),"r","ATK (Tim)"),((138,43,226),"e","VU TRU")]
        for i,(c,s,t) in enumerate(idat):
            y=200+i*40
            if s=="c": pygame.draw.circle(SCREEN,c,(70,y),15)
            elif s=="r": pygame.draw.rect(SCREEN,c,(55,y-15,30,30))
            else: pygame.draw.ellipse(SCREEN,c,(55,y-15,30,40))
            SCREEN.blit(f.render(t,1,(0,0,0)),(100,y-10))
        pygame.display.update()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: return

def menu(m):
    while True:
        SCREEN.fill((255,255,255))
        if m: SCREEN.blit(FONT_BIG.render(str(m),1,(255,0,0)),(300,50))
        t=["T-REX RUNNER: BATTLE","1: Single Player","2: PvP Mode","SPACE: Help",f"High Score: {get_score()}"]
        for i,x in enumerate(t): SCREEN.blit(FONT_BIG.render(x,1,(0,100,0) if i==4 else ((0,0,255) if i==3 else (0,0,0))),(250 if i==0 else 300, 150+i*60))
        SCREEN.blit(RUN[0],(400,500)); pygame.display.update()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_1: main(1)
                elif e.key==pygame.K_2: main(2)
                elif e.key==pygame.K_SPACE: help_screen()

if __name__=="__main__": menu(None)