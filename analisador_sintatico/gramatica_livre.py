import producao,definicoes


class GramaticaLivreDeContexto:
    
    def __init__(self, GLC_em_string):
        self.GLC_em_string = GLC_em_string
        self.cabeca_inicial = None
        self.producoes = self.monta_GLC_obj()
        self.firsts = self.calcular_first()
        self.follows = self.calcular_follow()

    def monta_GLC_obj(self):
        cabecas = set()
        producoes = set()
        
        for l in self.GLC_em_string.split('\n'): 
            p = producao.Producao(l)
            if(self.cabeca_inicial == None): self.cabeca_inicial = p.cabeca
            cabecas.add(p.cabeca)
            
        for l in self.GLC_em_string.split('\n'): 
            producoes.add(producao.Producao(l, cabecas))
        
        return producoes
            
    def get_cabecas(self): return [p.cabeca for p in self.producoes]
    
    def __str__(self): return '\n'.join([str(x) for x in self.producoes])
    
    def calcular_first(self):
        firsts = {k:set() for k in self.get_cabecas()}
        
        mudou = True
        while mudou == True:
            mudou = False
            for p in self.producoes:
                for s in p.corpo:
                    _break = False
                    if(not s.is_terminal):
                        firsts_aux = firsts[s.simbolo]
                        for faux in [x for x in firsts_aux if x != definicoes.EPISLON]:
                            if(faux not in firsts[p.cabeca]):
                                firsts[p.cabeca].add(faux)
                                mudou = True
                        if(definicoes.EPISLON not in firsts_aux): _break = True
                                
                    elif(s.is_terminal):
                        if(s.simbolo not in firsts[p.cabeca]):
                            firsts[p.cabeca].add(s.simbolo)
                            mudou = True
                        _break = True
                    
                    if _break: break
            
            for p in self.producoes:
                if(all([not s.is_terminal for s in p.corpo])):
                    if(all([definicoes.EPISLON in firsts[s.simbolo] for s in p.corpo])):
                        if(definicoes.EPISLON not in firsts[p.cabeca]):
                            firsts[p.cabeca].add(definicoes.EPISLON)
                            mudou = True
        
        return firsts
    
    def calcular_follow(self):
        follows = {k:set() for k in self.get_cabecas()}
        follows[self.cabeca_inicial].add('$')
        
        mudou = True
        while mudou == True:
            mudou = False
            for p in self.producoes:
                
                #caso 1
                #S -> ABCa joga first de B em A, tambem first de C em A se B.nullable
                for i,s in enumerate(p.corpo):
                    simbolo = s.simbolo
                    if(s.is_terminal): continue
                    for i2,s2 in enumerate(p.corpo[i:]):
                        simbolo2 = s2.simbolo
                        if(s2.is_terminal): break
                        if(simbolo == simbolo2): continue
                        first_aux = self.firsts[simbolo2]
                        for fa in [x for x in first_aux if x != definicoes.EPISLON]:
                            if(fa not in follows[simbolo]):
                                follows[simbolo].add(fa)
                                mudou=True
                        if(definicoes.EPISLON not in first_aux): break
                    
                #caso 2
                #S -> ABa joga a em follow B, tambem em follow A se B.nullable
                for i,s in enumerate(list(reversed(p.corpo))):
                    simbolo = s.simbolo
                    if(not s.is_terminal): continue
                    for i2,s2 in enumerate(list(reversed(p.corpo))[i:]):
                        simbolo2 = s2.simbolo
                        if(simbolo == simbolo2): continue
                        if(s2.is_terminal): continue
                        if(simbolo not in follows[simbolo2]):
                            follows[simbolo2].add(simbolo)
                            mudou=True
                        if(definicoes.EPISLON not in self.firsts[simbolo2]): break

                #caso 3
                # S -> ABC joga follow de S em C, em B se C.nullable...
                for i,s in enumerate(reversed(p.corpo)):
                    simbolo = s.simbolo
                    terminal = s.is_terminal
                    if(terminal): break
                    
                    follow_aux = follows[p.cabeca]
                    for fa in [x for x in follow_aux if definicoes.EPISLON != x]:
                        if(fa not in follows[simbolo]):
                            follows[simbolo].add(fa)
                            mudou=True
                    
                    if(definicoes.EPISLON not in self.firsts[simbolo]): break
        
        return follows