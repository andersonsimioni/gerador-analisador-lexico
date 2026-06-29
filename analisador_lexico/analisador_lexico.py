import automato.automato

class AnalisadorLexo:
    
    def __init__(self, poth_definicoes_regulares):
        self.path_definicoes_regulares = poth_definicoes_regulares
        self.definicoes_regulares = {}
        self.build_defs_regulares()
        
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
                self.definicoes_regulares[classe] = automato.automato.Automato.parse_regex(regex)
                continue
            
    def get_tabela_tokens(self, path_arquivo_entrada):
        tabela_tokens = []
        with open(path_arquivo_entrada, 'r') as file:
            for i, l in enumerate(file.readlines()):
                aux = l
                if(aux.endswith('\n')): aux = aux[:-1]
                
                try: 
                    classe = next(dr for dr in self.definicoes_regulares.keys() if self.definicoes_regulares[dr].reconhece(aux))
                    tabela_tokens.append(f'<{aux},{classe}>')
                except: 
                    tabela_tokens.append(f"<{aux},erro!>")
                    print(f'problema na linha {i}')
        
        return '\n'.join(tabela_tokens)