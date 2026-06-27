import transicao
import definicoes

class Estado:
    
    def __init__(self, nome, inicial, final):
        self.nome = nome
        self.inicial = inicial
        self.final = final
        self.transicoes = {}
        
    def add_transicao(self, transicao: Transicao):
        if(transicao.simbolo not in self.transicoes.keys()):
            self.transicoes[transicao.simbolo] = []
        
        self.transicoes[transicao.simbolo].append(transicao)
    
    def in_pattern(self, simbolo, pattern):
        blocos = []
        aux = pattern[1:-1]
        
        cache = ''
        fechar = False
        for i, c in enumerate(aux):
            if(fechar == True):
                cache += c
                fechar = False
                blocos.append(cache.split('-'))
                cache = ""
                continue
            
            if(fechar ==False and c == '-'):
                cache += c
                fechar = True
                continue
            
            cache += c
        
        return any([b for b in blocos if (len(b) > 0 and b[0] <= simbolo <= b[1])])
    
    def get_transicoes(self, simbolo):
        return set(
            
                self.transicoes.get(simbolo, []) +
                [t for _t in self.transicoes.keys() if len(_t) > 1 and str(_t).startswith('\\') and str(_t)[1] == simbolo  for t in self.transicoes[_t]] +
                [t for _t in self.transicoes.keys() if len(_t) > 1 and str(_t).startswith('[') and self.in_pattern(simbolo, str(_t))  for t in self.transicoes[_t]]
                
            
        )
    
    def get_proximos_estados(self, simbolo):
        return [x.estado_destino for x in self.get_transicoes(simbolo)]