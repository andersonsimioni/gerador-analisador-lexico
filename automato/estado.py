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
        
    def get_proximos_estados(self, simbolo):
        return [x.estado_destino for x in self.transicoes.get(simbolo, [])]