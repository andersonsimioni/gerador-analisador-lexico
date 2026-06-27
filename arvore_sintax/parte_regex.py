import definicoes

class ParteRegex:
    def __init__(self, _id, valor):
        self.id = _id
        self.valor = valor
        
        if(self.valor == "|"): self.tipo = definicoes.RegexParteTipo.UNIAO
        elif(self.valor == "."): self.tipo = definicoes.RegexParteTipo.CONCAT
        elif(self.valor == "*"): self.tipo = definicoes.RegexParteTipo.ESTRELA
        elif(self.valor == "+"): self.tipo = definicoes.RegexParteTipo.SOMA
        elif(self.valor == "?"): self.tipo = definicoes.RegexParteTipo.OPCIONAL
        elif(self.valor == "("): self.tipo = definicoes.RegexParteTipo.L_PARENTESES
        elif(self.valor == ")"): self.tipo = definicoes.RegexParteTipo.R_PARENTESES
        elif(self.valor == definicoes.EPISLON): self.tipo = definicoes.RegexParteTipo.EPISLON
        else: self.tipo = definicoes.RegexParteTipo.SIMBOLO_OU_LITERAL_OU_PADRAO
        
    def get_valor(self): return self.valor
    
    def get_id(self): return self.id
        