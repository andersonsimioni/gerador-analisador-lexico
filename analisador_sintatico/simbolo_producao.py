class SimboloProducao:
    
    def __init__(self, simbolo, is_terminal):
        self.simbolo = simbolo
        self.is_terminal = is_terminal
     
    def __str__(self): return self.simbolo
    #def __str__(self): return str.lower(self.simbolo) if self.is_terminal else str.upper(self.simbolo)