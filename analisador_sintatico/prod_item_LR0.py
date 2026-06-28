import producao
class ProdItemLR0:
    
    def __init__(self, producao, index_ponto):
        self.producao = producao
        self.index_ponto = index_ponto
    
    def get_simbolo_atual(self): 
        if(self.finalizo()): return "$"
        return self.producao.corpo[self.index_ponto]
    
    def avanca_simbolo_atual(self): return ProdItemLR0(self.producao, self.index_ponto + 1)
    
    def volta_simbolo_atual(self): return ProdItemLR0(self.producao, self.index_ponto - 1)
    
    def finalizo(self): return self.index_ponto >= len(self.producao.corpo)
    
    def __str__(self): 
        aux = [s.simbolo for s in self.producao.corpo]
        if(not self.finalizo()): aux[self.index_ponto] = f"·{aux[self.index_ponto]}"
        return f"{self.producao.cabeca} ::= {' '.join(aux)}{'·' if self.finalizo() else ''}"