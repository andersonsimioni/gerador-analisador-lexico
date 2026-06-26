import arvore_sintax.no_arvore_sintax, arvore_sintax.parte_regex, definicoes

class ArvoreSintax:
    def __init__(self, regex):
        self.regex = regex
        self.regex_partes = self.get_partes_regex()
        self.raiz = self.build_arvore(0)
    
    
    #divide o regex em partes indexadas, 
    # ex: [a-zA-z]*ab [[a-zA-z], *, a, CONCAT, b]
    def get_partes_regex(self):
        regex_partes = []
        
        padrao = ''
        last = None
        lendo_padrao = False
        lendo_literal = False
        for c in self.regex:
            
            if(lendo_padrao):
                padrao += c
                if(c == "]"): 
                    lendo_padrao = False
                    parte_atual = arvore_sintax.parte_regex.ParteRegex(padrao)
                else: continue
            elif(lendo_literal):
                padrao += c
                lendo_literal = False
                parte_atual = arvore_sintax.parte_regex.ParteRegex(padrao)
            else:
                parte_atual = arvore_sintax.parte_regex.ParteRegex(c)
                
            if(c == '\\'):
                padrao = "\\"
                lendo_literal = True
                continue
            
            if(c == '['): 
                padrao = c
                lendo_padrao = True
                continue
            
            tipos = definicoes.RegexParteTipo
            
            tipos_direita = [ tipos.SIMBOLO_OU_LITERAL_OU_PADRAO, tipos.EPISLON, tipos.L_PARENTESES]
            tipos_esquerda = [tipos.SIMBOLO_OU_LITERAL_OU_PADRAO, tipos.EPISLON, tipos.R_PARENTESES, tipos.ESTRELA, tipos.SOMA, tipos.OPCIONAL ]
            
            if(last != None and last.tipo in tipos_esquerda and parte_atual.tipo in tipos_direita):
                regex_partes.append(arvore_sintax.parte_regex.ParteRegex("."))
                
            regex_partes.append(parte_atual)
            last = parte_atual
                
        return regex_partes
    
    
    def build_arvore(self, index):
        
        pass