class NoArvoreSintax:
    def __init__(self, valor, tipo, left, right, first = None, last = None, follow = None):
        self.valor = valor
        self.tipo = tipo 
        
        self.left = left
        self.right = right
        
        self.first = first
        self.last = last
        self.follow = follow