from transicao import Transicao
import definicoes

PATTERN_CACHE = {}

class Estado:
    
    def __init__(self, nome, inicial, final):
        self.nome = nome
        self.inicial = inicial
        self.final = final
        self.transicoes = {}
        
    def add_transicao(self, transicao: Transicao):
        if(transicao.simbolo not in self.transicoes.keys()):
            self.transicoes[transicao.simbolo] = []
        
        self.transicoes[transicao.simbolo].append(transicao)
    
    def in_pattern(self, simbolo, pattern):
        blocos = []
        
        # esse loop constroe os patterns
        # caso seja range o item sera = (from_char, to_char)
        # caso seja char o item = char do literal
        # PRECISA USAR PATTERN_CACHE pra nao ficar
        #fazendo parse toda transicao..
        aux = pattern[1:-1]
        while('-' in aux):
            _range_index = str(aux).index('-')
            _range = aux[_range_index-1: _range_index+2]
            aux = str(aux).replace(_range, '')
            blocos.append(_range.split('-'))
        
        blocos.append(aux)
        
        #se item do bloco eh do tipo [] entao eh range, se nao eh char
        #caso seja range (from <= simbolo <= to)
        #caso seja char (simbolo in chars) obs: as chars ficam agrupadas em apenas um item da lista de blocos
        return any([b for b in blocos if (b[0] <= simbolo <= b[1] if type(b) == type([]) else simbolo in b)])
    
    def get_transicoes(self, simbolo):
        return set(

                #traz transicoes normais por simbolo
                self.transicoes.get(simbolo, []) +
                #trata transicoes por literal
                [t for _t in self.transicoes.keys() if len(_t) > 1 and str(_t).startswith('\\') and str(_t)[1] == simbolo  for t in self.transicoes[_t]] +
                #traz transicoes por pattern [x-y]..
                [t for _t in self.transicoes.keys() if len(_t) > 1 and str(_t).startswith('[') and self.in_pattern(simbolo, str(_t))  for t in self.transicoes[_t]]
                
            
        )
    
    def get_proximos_estados(self, simbolo):
        return [x.estado_destino for x in self.get_transicoes(simbolo)]