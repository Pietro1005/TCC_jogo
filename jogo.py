import pygame
import sys
import random

# --- CONFIGURAÇÕES GERAIS ---
LARGURA_TELA = 800
ALTURA_TELA = 600
FPS = 60

# --- CLASSE DO PROJÉTIL ---
class Projetil(pygame.sprite.Sprite):
    def __init__(self, x, y, direcao, velocidad, cor):
        super().__init__()
        self.image = pygame.Surface((20, 8))
        self.image.fill(cor)
        self.rect = self.image.get_rect(center=(x, y))
        self.velocidade = velocidad * direcao

    def update(self):
        self.rect.x += self.velocidade
        if self.rect.x < -500 or self.rect.x > 4500:
            self.kill()

# --- CLASSE DOS OBSTÁCULOS / PLATAFORMAS ---
class Plataforma(pygame.sprite.Sprite):
    def __init__(self, x, y, largura, altura, cor=(40, 100, 40)):
        super().__init__()
        self.image = pygame.Surface((largura, altura))
        self.image.fill(cor)
        self.rect = self.image.get_rect(topleft=(x, y))

# --- CLASSE DO JOGADOR (A MORTE) ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.image.fill((80, 80, 90)) 
        self.rect = self.image.get_rect(topleft=(x, y))

        # Física e Movimento
        self.vel_x = 0
        self.vel_y = 0
        self.velocidade = 6
        self.forca_pulo = -17  
        self.gravidade = 0.6
        self.multiplicador_pulo_curto = 0.5
        self.no_chao = False
        self.direcao_olhar = 1 

        # Atributos de Combate
        self.vida_maxima = 100
        self.vida_atual = self.vida_maxima
        self.mana_maxima = 100
        self.mana_atual = self.mana_maxima
        
        self.custo_espirito = 25
        self.ganho_foice = 20
        
        # Sistema de Ataque e Cooldown
        self.atacou_foice = False
        self.atacou_magia = False
        self.cooldown_foice = 0
        self.tempo_cooldown_foice = 60  # 60 frames = 1 segundo cravado a 60 FPS
        
        self.tempo_imune = 0 
        self.hitbox_ataque_atual = None
        self.frames_desenho_ataque = 0

    def update(self, teclas, mouse_botoes, plataformas, inimigos, projeteis_jogador, boss):
        if self.tempo_imune > 0: self.tempo_imune -= 1
        if self.frames_desenho_ataque > 0: self.frames_desenho_ataque -= 1
        else: self.hitbox_ataque_atual = None
        
        # Reduz o tempo de recarga da foice a cada frame
        if self.cooldown_foice > 0: 
            self.cooldown_foice -= 1

        # 1. Movimentação Horizontal
        self.vel_x = 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            self.vel_x = -self.velocidade
            self.direcao_olhar = -1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            self.vel_x = self.velocidade
            self.direcao_olhar = 1

        self.rect.x += self.vel_x
        self.checar_colisao_horizontal(plataformas)

        # 2. Gravidade e Pulo
        self.vel_y += self.gravidade
        self.rect.y += self.vel_y
        self.checar_colisao_vertical(plataformas)

        if (teclas[pygame.K_SPACE] or teclas[pygame.K_w]) and self.no_chao:
            self.vel_y = self.forca_pulo
            self.no_chao = False
        if not (teclas[pygame.K_SPACE] or teclas[pygame.K_w]) and self.vel_y < 0:
            self.vel_y *= self.multiplicador_pulo_curto

        # 3. Ataques
        self.controlar_ataques(teclas, mouse_botoes, inimigos, projeteis_jogador, boss)

    def checar_colisao_horizontal(self, plataformas):
        colisoes = pygame.sprite.spritecollide(self, plataformas, False)
        for bloco in colisoes:
            if self.vel_x > 0: self.rect.right = bloco.rect.left
            elif self.vel_x < 0: self.rect.left = bloco.rect.right

    def checar_colisao_vertical(self, plataformas):
        self.no_chao = False
        colisoes = pygame.sprite.spritecollide(self, plataformas, False)
        for bloco in colisoes:
            if self.vel_y > 0:
                self.rect.bottom = bloco.rect.top
                self.vel_y = 0
                self.no_chao = True
            elif self.vel_y < 0:
                self.rect.top = bloco.rect.bottom
                self.vel_y = 0

    def controlar_ataques(self, teclas, mouse_botoes, inimigos, projeteis_jogador, boss):
        # MUDANÇA: O ataque só inicia se o clique for feito E o cooldown for igual a zero
        if mouse_botoes[0]:
            if not self.atacou_foice and self.cooldown_foice == 0:
                self.ataque_foice(inimigos, boss)
                self.atacou_foice = True
        else:
            self.atacou_foice = False

        if teclas[pygame.K_r]:
            if not self.atacou_magia:
                self.ataque_espirito(projeteis_jogador)
                self.atacou_magia = True
        else:
            self.atacou_magia = False

    def ataque_foice(self, inimigos, boss):
        # Ativa o cooldown imediatamente ao golpear
        self.cooldown_foice = self.tempo_cooldown_foice
        
        alcance = 85 
        x_hitbox = self.rect.right if self.direcao_olhar == 1 else self.rect.left - alcance
        self.hitbox_ataque_atual = pygame.Rect(x_hitbox, self.rect.y + 5, alcance, self.rect.height - 10)
        self.frames_desenho_ataque = 10 
        
        for inimigo in inimigos:
            if self.hitbox_ataque_atual.colliderect(inimigo.rect):
                inimigo.receber_dano(35)
                self.mana_atual = min(self.mana_maxima, self.mana_atual + self.ganho_foice)
                
        if boss and boss.estado != "CAINDO" and boss.estado != "DERROTADO" and self.hitbox_ataque_atual.colliderect(boss.rect):
            boss.receber_dano(35)
            self.mana_atual = min(self.mana_maxima, self.mana_atual + self.ganho_foice)

    def ataque_espirito(self, projeteis_jogador):
        if self.mana_atual >= self.custo_espirito:
            self.mana_atual -= self.custo_espirito
            p = Projetil(self.rect.centerx, self.rect.centery, self.direcao_olhar, 12, (0, 150, 255))
            projeteis_jogador.add(p)

    def receber_dano(self, qtd):
        if self.tempo_imune == 0:
            self.vida_atual -= qtd
            self.tempo_imune = 45 
            if self.vida_atual < 0: self.vida_atual = 0

# --- INIMIGO TERRESTRE ---
class InimigoTerrestre(pygame.sprite.Sprite):
    def __init__(self, x, y, limite_patrulha):
        super().__init__()
        self.image = pygame.Surface((35, 55))
        self.image.fill((200, 70, 70)) 
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vida = 30
        self.velocidade = 2
        self.inicio_x = x
        self.limite = limite_patrulha
        self.direcao = 1
        self.perto_do_jogador = False
        self.hitbox_ataque_inimigo = None

    def update(self, jogador_rect, jogador_obj):
        distancia = abs(self.rect.centerx - jogador_rect.centerx)
        if distancia < 70 and abs(self.rect.centery - jogador_rect.centery) < 50:
            self.perto_do_jogador = True
            alcance_ataque = 40
            x_ataque = self.rect.left - alcance_ataque if jogador_rect.centerx < self.rect.centerx else self.rect.right
            self.hitbox_ataque_inimigo = pygame.Rect(x_ataque, self.rect.y + 10, alcance_ataque, self.rect.height - 20)
            if self.hitbox_ataque_inimigo.colliderect(jogador_rect):
                jogador_obj.receber_dano(15)
        else:
            self.perto_do_jogador = False
            self.hitbox_ataque_inimigo = None
            self.rect.x += self.velocidade * self.direcao
            if abs(self.rect.x - self.inicio_x) > self.limite:
                self.direcao *= -1

    def receber_dano(self, qtd):
        self.vida -= qtd
        if self.vida <= 0: self.kill()

# --- INIMIGO VOADOR ---
class InimigoVoador(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill((240, 220, 80)) 
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vida = 20
        self.tempo_tiro = 0
        self.frequencia_tiro = 90 

    def update(self, jogador_x, projeteis_inimigos):
        self.tempo_tiro += 1
        if self.tempo_tiro >= self.frequencia_tiro:
            self.tempo_tiro = 0
            direcao = 1 if jogador_x > self.rect.centerx else -1
            flecha = Projetil(self.rect.centerx, self.rect.centery, direcao, 6, (255, 255, 150))
            projeteis_inimigos.add(flecha)

    def receber_dano(self, qtd):
        self.vida -= qtd
        if self.vida <= 0: self.kill()

# --- CLASSE DO CHEFÃO (ARCANJO SUPREMO) ---
class BossAnjo(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((80, 120))
        self.image.fill((255, 223, 0)) 
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.vida_maxima = 250
        self.vida_atual = self.vida_maxima
        
        self.estado = "INATIVO" 
        self.timer_estado = 0
        self.cooldown_acao = 120 
        
        self.direcao_dash = -1
        self.contador_rajada = 0
        self.cor_atual = (255, 223, 0)

    def update(self, jogador_rect, jogador_obj, projeteis_inimigos, arena_fechada):
        if self.vida_atual <= 0 and self.estado != "CAINDO" and self.estado != "DERROTADO":
            self.estado = "CAINDO"
            pos_x_antiga, pos_y_antiga = self.rect.x, self.rect.y
            self.image = pygame.Surface((120, 40)) 
            self.rect = self.image.get_rect()
            self.rect.x = pos_x_antiga
            self.rect.y = pos_y_antiga
            self.cor_atual = (100, 100, 100) 
            return

        if self.estado == "CAINDO":
            self.rect.y += 6 
            if self.rect.bottom >= 500: 
                self.rect.bottom = 500
                self.estado = "DERROTADO"
            self.image.fill(self.cor_atual)
            return

        if self.estado == "DERROTADO":
            self.image.fill(self.cor_atual)
            return

        if not arena_fechada:
            self.estado = "INATIVO"
            return
        elif self.estado == "INATIVO" and arena_fechada:
            self.estado = "IDLE"

        self.timer_estado += 1
        
        if self.estado == "IDLE":
            self.cor_atual = (255, 223, 0)
            if self.timer_estado >= self.cooldown_acao:
                self.timer_estado = 0
                self.estado = random.choice(["RAJADA", "DASH"])
                
        elif self.estado == "RAJADA":
            self.cor_atual = (135, 206, 250) 
            if self.timer_estado % 20 == 0:
                direcao = -1 if jogador_rect.centerx < self.rect.centerx else 1
                tiro = Projetil(self.rect.left if direcao == -1 else self.rect.right, self.rect.centery + random.randint(-20, 20), direcao, 9, (255, 255, 200))
                projeteis_inimigos.add(tiro)
                self.contador_rajada += 1
                
            if self.contador_rajada >= 3:
                self.contador_rajada = 0
                self.estado = "IDLE"
                self.timer_estado = 0

        elif self.estado == "DASH":
            self.cor_atual = (255, 69, 0) 
            if self.timer_estado == 1:
                self.direcao_dash = -1 if jogador_rect.centerx < self.rect.centerx else 1
            if self.timer_estado > 30 and self.timer_estado <= 60:
                self.rect.x += 14 * self.direcao_dash
                if self.rect.colliderect(jogador_rect):
                    jogador_obj.receber_dano(25)
            
            if self.timer_estado > 60:
                self.estado = "IDLE"
                self.timer_estado = 0
        
        if self.rect.left < 2400: self.rect.left = 2400
        if self.rect.right > 3400: self.rect.right = 3400
        
        self.image.fill(self.cor_atual)

    def receber_dano(self, qtd):
        if self.estado != "CAINDO" and self.estado != "DERROTADO":
            self.vida_atual -= qtd
            if self.vida_atual < 0: self.vida_atual = 0


# --- FUNÇÃO PARA GERAR O MUNDO ---
def inicializar_mundo():
    global jogador, plataformas, inimigos, projeteis_jogador, projeteis_inimigos, boss, arena_fechada
    jogador = Player(100, 300)
    plataformas = pygame.sprite.Group()
    inimigos = pygame.sprite.Group()
    projeteis_jogador = pygame.sprite.Group()
    projeteis_inimigos = pygame.sprite.Group()
    arena_fechada = False

    blocos_cenario = [
        Plataforma(0, 500, 750, 100),       
        Plataforma(400, 380, 180, 30),      
        Plataforma(680, 280, 220, 30),      
        
        Plataforma(1000, 500, 650, 100),  
        Plataforma(1100, 380, 150, 30),
        Plataforma(1350, 280, 180, 30),  
        Plataforma(1650, 420, 300, 180),   
        Plataforma(1800, 270, 150, 30),  

        Plataforma(2100, 460, 300, 140),
        Plataforma(2400, 500, 1000, 100), 
        Plataforma(3350, 100, 50, 400, (100, 110, 120)) 
    ]
    plataformas.add(blocos_cenario)

    inimigos.add(InimigoTerrestre(420, 325, 40))  
    inimigos.add(InimigoTerrestre(1150, 445, 80))
    inimigos.add(InimigoTerrestre(1700, 365, 60))
    inimigos.add(InimigoVoador(750, 160))         
    inimigos.add(InimigoVoador(1300, 180))        

    boss = BossAnjo(2950, 380)

# --- SETUP INICIAL PYGAME ---
pygame.init()
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("TCC - Morte: Ritmo de Combate")
relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("Arial", 22)
fonte_titulo = pygame.font.SysFont("Arial", 48, bold=True)

inicializar_mundo()
estado_jogo = "MENU" 

# --- LOOP PRINCIPAL ---
rodando = True
while rodando:
    relogio.tick(FPS)
    
    # 1. CAPTURA DE EVENTOS
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        if evento.type == pygame.KEYDOWN:
            if estado_jogo == "MENU" and evento.key == pygame.K_RETURN:
                estado_jogo = "JOGANDO"
            if (estado_jogo == "GAME_OVER" or estado_jogo == "VITORIA") and evento.key == pygame.K_r:
                inicializar_mundo()
                estado_jogo = "JOGANDO"

    # 2. LÓGICA DO GAMEPLAY
    if estado_jogo == "JOGANDO":
        teclas = pygame.key.get_pressed()
        mouse_botoes = pygame.mouse.get_pressed() 
        
        jogador.update(teclas, mouse_botoes, plataformas, inimigos, projeteis_jogador, boss)
        projeteis_jogador.update()
        projeteis_inimigos.update()

        if jogador.rect.x > 2420 and not arena_fechada:
            arena_fechada = True
            parede_traseira = Plataforma(2380, 100, 40, 400, (100, 110, 120))
            plataformas.add(parede_traseira)

        for inimigo in inimigos:
            if isinstance(inimigo, InimigoVoador):
                inimigo.update(jogador.rect.centerx, projeteis_inimigos)
            elif isinstance(inimigo, InimigoTerrestre):
                inimigo.update(jogador.rect, jogador)

        boss.update(jogador.rect, jogador, projeteis_inimigos, arena_fechada)
        
        if boss.estado == "DERROTADO":
            estado_jogo = "VITORIA"

        for proj in projeteis_jogador:
            atingidos = pygame.sprite.spritecollide(proj, inimigos, False)
            if atingidos:
                for inimigo in atingidos: inimigo.receber_dano(25)
                proj.kill()
            if boss.estado not in ["CAINDO", "DERROTADO"] and proj.rect.colliderect(boss.rect):
                boss.receber_dano(25)
                proj.kill()

        if pygame.sprite.spritecollide(jogador, projeteis_inimigos, True):
            jogador.receber_dano(10)

        if jogador.vida_atual <= 0 or jogador.rect.top > ALTURA_TELA + 40:
            estado_jogo = "GAME_OVER"

        camera_x = jogador.rect.centerx - LARGURA_TELA // 2
        if camera_x < 0: camera_x = 0

    # 3. EXIBIÇÃO DE GRÁFICOS
    tela.fill((18, 18, 24)) 

    if estado_jogo == "MENU":
        t1 = fonte_titulo.render("A JORNADA DA MORTE", True, (240, 240, 240))
        t2 = fonte.render("Controles: A/D (Mover) - W/Espaço (Pular Alto) - Clique Esq. (Foice) - R (Magia)", True, (180, 180, 180))
        t3 = fonte.render("Pressione ENTER para iniciar", True, (0, 200, 100))
        tela.blit(t1, (LARGURA_TELA//2 - t1.get_width()//2, 180))
        tela.blit(t2, (LARGURA_TELA//2 - t2.get_width()//2, 300))
        tela.blit(t3, (LARGURA_TELA//2 - t3.get_width()//2, 380))

    elif estado_jogo == "GAME_OVER":
        t_go = fonte_titulo.render("FALHA NA CEIFA", True, (255, 50, 50))
        t_res = fonte.render("Pressione R para tentar novamente", True, (200, 200, 200))
        tela.blit(t_go, (LARGURA_TELA//2 - t_go.get_width()//2, 220))
        tela.blit(t_res, (LARGURA_TELA//2 - t_res.get_width()//2, 320))
        
    elif estado_jogo == "VITORIA":
        for plat in plataformas: tela.blit(plat.image, (plat.rect.x - camera_x, plat.rect.y))
        tela.blit(boss.image, (boss.rect.x - camera_x, boss.rect.y))
        tela.blit(jogador.image, (jogador.rect.x - camera_x, boss_y := jogador.rect.y))
        
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        tela.blit(overlay, (0, 0))

        t_vi = fonte_titulo.render("VITÓRIA CONCLUÍDA", True, (0, 255, 150))
        t_sub = fonte.render("O Arcanjo desabou. A colheita foi realizada com sucesso.", True, (220, 220, 220))
        t_res = fonte.render("Pressione R para recomeçar o teste", True, (150, 150, 150))
        tela.blit(t_vi, (LARGURA_TELA//2 - t_vi.get_width()//2, 180))
        tela.blit(t_sub, (LARGURA_TELA//2 - t_sub.get_width()//2, 280))
        tela.blit(t_res, (LARGURA_TELA//2 - t_res.get_width()//2, 360))

    elif estado_jogo == "JOGANDO":
        for plat in plataformas:
            tela.blit(plat.image, (plat.rect.x - camera_x, plat.rect.y))
            
        for inimigo in inimigos:
            tela.blit(inimigo.image, (inimigo.rect.x - camera_x, inimigo.rect.y))
            pygame.draw.rect(tela, (255, 255, 255), (inimigo.rect.x - camera_x, inimigo.rect.y, inimigo.rect.width, inimigo.rect.height), 1)

        tela.blit(boss.image, (boss.rect.x - camera_x, boss.rect.y))
        if boss.estado not in ["CAINDO", "DERROTADO"]:
            pygame.draw.rect(tela, (255, 215, 0), (boss.rect.x - camera_x, boss.rect.y, boss.rect.width, boss.rect.height), 2)
        else:
            pygame.draw.rect(tela, (150, 150, 150), (boss.rect.x - camera_x, boss.rect.y, boss.rect.width, boss.rect.height), 1)

        for proj in projeteis_jogador: tela.blit(proj.image, (proj.rect.x - camera_x, proj.rect.y))
        for proj in projeteis_inimigos: tela.blit(proj.image, (proj.rect.x - camera_x, proj.rect.y))

        if jogador.tempo_imune % 4 < 2:
            tela.blit(jogador.image, (jogador.rect.x - camera_x, jogador.rect.y))
        pygame.draw.rect(tela, (0, 255, 0), (jogador.rect.x - camera_x, jogador.rect.y, jogador.rect.width, jogador.rect.height), 1)

        if jogador.hitbox_ataque_atual:
            pygame.draw.rect(tela, (0, 180, 255), (jogador.hitbox_ataque_atual.x - camera_x, jogador.hitbox_ataque_atual.y, jogador.hitbox_ataque_atual.width, jogador.hitbox_ataque_atual.height), 2)

        # UI FIXA (HUD)
        pygame.draw.rect(tela, (30, 30, 40), (15, 15, 200, 85)) # Expandida para caber a info do Cooldown
        tela.blit(fonte.render(f"Vida: {jogador.vida_atual}/{jogador.vida_maxima}", True, (255, 80, 80)), (20, 20))
        tela.blit(fonte.render(f"Mana: {jogador.mana_atual}/{jogador.mana_maxima}", True, (0, 180, 255)), (20, 45))
        
        # Indicador visual textual do Cooldown da Foice
        if jogador.cooldown_foice == 0:
            tela.blit(fonte.render("Foice: PRONTA", True, (0, 255, 100)), (20, 70))
        else:
            # Mostra os segundos restantes de forma amigável
            segundos_restantes = jogador.cooldown_foice / 60
            tela.blit(fonte.render(f"Foice: {segundos_restantes:.1f}s", True, (200, 150, 30)), (20, 70))

        if arena_fechada and boss.vida_atual > 0:
            largura_barra_boss = 500
            x_barra = LARGURA_TELA // 2 - largura_barra_boss // 2
            pygame.draw.rect(tela, (50, 20, 20), (x_barra, 25, largura_barra_boss, 20))
            proporcao_vida = boss.vida_atual / boss.vida_maxima
            pygame.draw.rect(tela, (255, 215, 0), (x_barra, 25, int(largura_barra_boss * proporcao_vida), 20))
            t_boss_name = fonte.render("ARCANJO SUPREMO", True, (255, 255, 255))
            tela.blit(t_boss_name, (LARGURA_TELA // 2 - t_boss_name.get_width() // 2, 48))

    pygame.display.flip()

pygame.quit()
sys.exit()