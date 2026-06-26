import estado
import definicoes

class Transicao:
    
    def __init__(self, estado_origem, estado_destino, simbolo):
        self.estado_origem = estado_origem
        self.estado_destino = estado_destino
        self.simbolo = simbolo