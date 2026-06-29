import arvore_sintax.no_arvore_sintax, arvore_sintax.parte_regex, definicoes

class ArvoreSintax:
    def __init__(self, regex):
        self.nos = {} #chave(id no arvore) = (regex parte, no arvore)
        self.regex = regex
        self.regex_partes = self.get_partes_regex()
        self.raiz = self.build_arvore(self.regex_partes)
        self.calcular_nullable_first_last(self.raiz)
        self.calcular_follows(self.raiz)
    
    def get_parte_by_id(self, _id):
        return [x for x in self.regex_partes if x.id == _id][0]
    
    #divide o regex em partes indexadas, 
    # ex: [a-zA-z]*ab [[a-zA-z], *, a, CONCAT, b]
    def get_partes_regex(self):
        regex_partes = []
        
        padrao = ''
        last = None
        lendo_padrao = False
        lendo_literal = False
        parte_atual = None
        for i, c in enumerate(self.regex):
            
            #se achar barra o proximo simbolo eh literal
            if(c == '\\' and not (lendo_padrao or lendo_literal)):
                padrao = "\\"
                lendo_literal = True
                continue

            #se achar [ comeca a ler um padrao inteiro
            elif(c == '[' and not (lendo_padrao or lendo_literal)): 
                padrao = c
                lendo_padrao = True
                continue
            
            #se tiver lendo padrao junta tudo ate fechar ]
            if(lendo_padrao):
                padrao += c
                if(c == "]"): 
                    lendo_padrao = False
                    parte_atual = arvore_sintax.parte_regex.ParteRegex(i, padrao)
                else: continue

            #se tiver lendo literal junta com a barra lida anteriormente
            elif(lendo_literal):
                padrao += c
                lendo_literal = False
                parte_atual = arvore_sintax.parte_regex.ParteRegex(i, padrao)
                
            
            #caso comum, cria parte usando o proprio caractere
            if(parte_atual == None): parte_atual = arvore_sintax.parte_regex.ParteRegex(i, c)
            
            tipos = definicoes.RegexParteTipo
            
            tipos_direita = [ tipos.SIMBOLO_OU_LITERAL_OU_PADRAO, tipos.EPISLON, tipos.L_PARENTESES]
            tipos_esquerda = [tipos.SIMBOLO_OU_LITERAL_OU_PADRAO, tipos.EPISLON, tipos.R_PARENTESES, tipos.ESTRELA, tipos.SOMA, tipos.OPCIONAL ]
            
            #se puder adiciona concat implicito entre as partes
            if(last != None and last.tipo in tipos_esquerda and parte_atual.tipo in tipos_direita):
                regex_partes.append(arvore_sintax.parte_regex.ParteRegex(-1, "."))
                
            regex_partes.append(parte_atual)

            #guarda a ultima parte pra saber se precisa concatenar na proxima
            last = parte_atual
            parte_atual = None
                
        return regex_partes
    
    
    #monta arvore sintax sem calular first, last e follow
    def build_arvore(self, parts):
        tipos = definicoes.RegexParteTipo
        no = arvore_sintax.no_arvore_sintax
        paranteses = 0
        
        externo = True
        #caso tenha parenteses por fora, tenta remover e montar o miolo
        if(parts[0].tipo == tipos.L_PARENTESES  and parts[-1].tipo == tipos.R_PARENTESES):
            for i, p in enumerate(parts):
                if(p.tipo == tipos.L_PARENTESES): paranteses +=1
                if(p.tipo == tipos.R_PARENTESES): paranteses -=1
                if(paranteses == 0 and i != len(parts)-1): 
                    externo = False
                    break
            if externo: 
                return self.build_arvore(parts[1:-1])
        
        paranteses=0
        #caso 1: procura uniao fora dos parenteses
        for i, p in enumerate(parts):
            if p.tipo == tipos.L_PARENTESES: paranteses += 1
            if p.tipo == tipos.R_PARENTESES: paranteses -= 1
            if p.tipo == tipos.UNIAO and paranteses == 0:
                return no.NoArvoreSintax(p, self.build_arvore(parts[:i]), self.build_arvore(parts[i+1:]))
        
        paranteses=0
        #caso 2: procura concat fora dos parenteses
        for i, p in enumerate(parts):
            if p.tipo == tipos.L_PARENTESES: paranteses += 1
            if p.tipo == tipos.R_PARENTESES: paranteses -= 1
            if p.tipo == tipos.CONCAT and paranteses == 0:
                return no.NoArvoreSintax(p, self.build_arvore(parts[:i]), self.build_arvore(parts[i+1:]))
            
        #caso 3: se terminar com *, + ou ? entao vira filho unico
        if parts[-1].tipo in [tipos.ESTRELA, tipos.SOMA, tipos.OPCIONAL]:
            return no.NoArvoreSintax(parts[-1], child=self.build_arvore(parts[:-1]))
        
        #caso 4: sobrou um simbolo, entao cria folha da arvore
        no_novo = no.NoArvoreSintax(parts[0])
        self.nos[parts[0].get_id()] = (parts[0], no_novo)
        return no_novo
    
    #calcula first, last e follow na arvore de sintax pronta
    def calcular_nullable_first_last(self, no):
        tipos = definicoes.RegexParteTipo
        tipo = no.parte_regex_original.tipo
        
        #vai fazer recursao ate' chegar nas folhas, depois
        # as folhas voao retornando e calculando first e last em cascata
        if no.left is not None: self.calcular_nullable_first_last(no.left)
        if no.right is not None: self.calcular_nullable_first_last(no.right)
        if no.child is not None: self.calcular_nullable_first_last(no.child)
        
        if(tipo == tipos.SIMBOLO_OU_LITERAL_OU_PADRAO):
            """
                caso 1
                se for simbolo normal entao:
                    nullable = False
                    first = ele mesmo
                    last = ele mesmo
            """
            no.nullable = False
            no.first = {no}
            no.last = {no}

        elif(tipo == tipos.EPISLON):
            """
                caso 2
                se for epsilon entao:
                    nullable = True
                    first = vazio
                    last = vazio
            """
            no.nullable = True
            no.first = set()
            no.last = set()

        elif(tipo == tipos.UNIAO):
            """
                caso 3
                se for uniao A | B entao:
                    nullable = A nullable ou B nullable
                    first = first de A unido com first de B
                    last = last de A unido com last de B
            """
            no.nullable = no.left.nullable or no.right.nullable
            no.first = no.left.first | no.right.first
            no.last = no.left.last | no.right.last

        elif tipo == tipos.CONCAT:
          """
              caso 4
              se for concat A B entao:
                  nullable = A nullable e B nullable
                  first depende se A eh nullable
                  last depende se B eh nullable
          """
          no.nullable = no.left.nullable and no.right.nullable

          if no.left.nullable: no.first = no.left.first | no.right.first
          else: no.first = no.left.first

          if no.right.nullable: no.last = no.left.last | no.right.last
          else: no.last = no.right.last

        elif tipo == tipos.ESTRELA:
            """
                caso 5
                se for estrela A* entao:
                    nullable = True
                    first = first de A
                    last = last de A
            """
            no.nullable = True
            no.first = no.child.first
            no.last = no.child.last

        elif tipo == tipos.SOMA:
            """
                caso 6
                se for soma A+ entao:
                    nullable = nullable de A
                    first = first de A
                    last = last de A
            """
            no.nullable = no.child.nullable
            no.first = no.child.first
            no.last = no.child.last

        elif tipo == tipos.OPCIONAL:
            """
                caso 7
                se for opcional A? entao:
                    nullable = True
                    first = first de A
                    last = last de A
            """
            no.nullable = True
            no.first = no.child.first
            no.last = no.child.last
    
    def calcular_follows(self, no):
        tipos = definicoes.RegexParteTipo
        tipo = no.parte_regex_original.tipo
        
        #mesmo esquema do first e last, vai fazer recursao ate nas folhas
        if no.left is not None: self.calcular_follows(no.left)
        if no.right is not None: self.calcular_follows(no.right)
        if no.child is not None: self.calcular_follows(no.child)
        
        if(tipo == tipos.CONCAT):
            """
                caso 1
                se for concat A B entao:
                    pra cada last de A
                    follow recebe first de B
            """
            for last in no.left.last: last.follow |= no.right.first

        elif(tipo == tipos.ESTRELA):
            """
                caso 2
                se for estrela A* entao:
                    pra cada last de A
                    follow recebe first de A
            """
            for last in no.child.last: last.follow |= no.child.first

        elif(tipo == tipos.SOMA):
            """
                caso 3
                se for soma A+ entao:
                    pra cada last de A
                    follow recebe first de A
            """
            for last in no.child.last: last.follow  |=  no.child.first
            
    def get_nos(self, ids_partes):
        #chave(id no arvore) = (regex parte, no arvore)
        nos = [self.nos[x] for x in ids_partes]
        return nos
    
    def get_id_hastag(self):
        return [self.nos[x][1].get_parte_regex_id() for x in self.nos.keys() if self.nos[x][1].get_parte_regex_valor() == '#'][0]
        
