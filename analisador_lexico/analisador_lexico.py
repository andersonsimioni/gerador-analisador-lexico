import automato.automato

class AnalisadorLexo:
    
    def __init__(self, poth_definicoes_regulares, path_palavras_reservadas=None):
        self.path_definicoes_regulares = poth_definicoes_regulares
        self.path_palavras_reservadas = path_palavras_reservadas
        self.definicoes_regulares = {}
        self.palavras_reservadas = {}
        self.tabela_simbolos = {}
        self.build_defs_regulares()
        self.build_palavras_reservadas()
        
    def build_defs_regulares(self):
        file_path = self.path_definicoes_regulares
        with open(file_path, 'r') as file:
            for l in file.readlines():
                aux = l
                if(aux.endswith('\n')): aux = aux[:-1]
                separador = aux.index(":")
                classe= aux[:separador]
                if(classe.endswith(' ')): classe = classe[:-1]
                regex= aux[separador+1:]
                if(regex.startswith(' ')): regex = regex[1:]
                regex = regex.replace(" ", "")
                self.definicoes_regulares[classe] = automato.automato.Automato.parse_regex(regex)
                continue

    def build_palavras_reservadas(self):
        if(self.path_palavras_reservadas is None): return

        with open(self.path_palavras_reservadas, 'r') as file:
            for l in file:
                aux = l.strip()
                if(aux == ''): continue

                if(':' in aux):
                    palavra, classe = aux.split(':', 1)
                    palavra = palavra.strip()
                    classe = classe.strip()
                else:
                    palavra = aux
                    classe = "PR"

                self.palavras_reservadas[palavra] = classe
                self.tabela_simbolos[palavra] = classe

    def get_token_id(self, lexema):
        if(lexema not in self.tabela_simbolos):
            self.tabela_simbolos[lexema] = len(self.tabela_simbolos) + 1

        return f"<id,{self.tabela_simbolos[lexema]}>"
            
    def get_tabela_tokens(self, path_arquivo_entrada):
        tabela_tokens = []
        with open(path_arquivo_entrada, 'r') as file:
            for i, l in enumerate(file.readlines()):
                aux = l
                if(aux.endswith('\n')): aux = aux[:-1]
                
                try: 
                    if(aux in self.palavras_reservadas):
                        classe = self.palavras_reservadas[aux]
                        tabela_tokens.append(f'<{aux},{classe}>')
                    else:
                        classe = next(dr for dr in self.definicoes_regulares.keys() if self.definicoes_regulares[dr].reconhece(aux))
                        if(classe == "id"):
                            tabela_tokens.append(self.get_token_id(aux))
                        else:
                            tabela_tokens.append(f'<{aux},{classe}>')
                except: 
                    tabela_tokens.append(f"<{aux},erro!>")
                    print(f'problema na linha {i}')
        
        return '\n'.join(tabela_tokens)
