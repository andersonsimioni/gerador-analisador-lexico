import simbolo_producao

class Producao:
    
    #E ::= E + T
    def __init__(self, cabeca_corpo, cabecas=None):
        aux = cabeca_corpo
        separador_index = str(aux).index('::=')
        
        self.cabeca = aux[:separador_index]
        if(str(self.cabeca).endswith(' ')): self.cabeca = self.cabeca[:-1]
        
        corpo = aux[separador_index+3:]
        
        if(cabecas is None): return
        
        if(str(corpo).startswith(' ')): corpo = corpo[1:]
        self.corpo = [simbolo_producao.SimboloProducao(x, x not in cabecas) for x in corpo.split(' ')]
        
    def __str__(self): return f"{self.cabeca} ::= {' '.join([str(x) for x in self.corpo])}"