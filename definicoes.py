from enum import Enum

EPISLON = '&'

MAX_BUSCA_LARGURA_AFND = 15000

class RegexParteTipo(Enum):
    L_PARENTESES = 0
    R_PARENTESES = 1
    
    UNIAO = 2
    CONCAT =3
    
    ESTRELA = 4
    SOMA = 5
    OPCIONAL = 6
    
    EPISLON = 7
    SIMBOLO_OU_LITERAL_OU_PADRAO = 8
    