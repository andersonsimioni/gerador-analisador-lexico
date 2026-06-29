from automato.automato import Automato
from automato.estado import Estado
from automato.transicao import Transicao
import definicoes

class Unificador_de_automato:
    
    @staticmethod
    def uniao_de_automato(lista_de_AF):
        novo_af = Automato("AFN_Uniao")
        inicial_novo = Estado("q_inicial_uniao", True, False)
        novo_af.add_estado(inicial_novo)
        
        for i, af in enumerate(lista_de_AF):
            estado_inicial_do_automato_local = af.get_inicial()
        
            transicao_aux = Transicao(inicial_novo, estado_inicial_do_automato_local, definicoes.EPISLON)
            inicial_novo.add_transicao(transicao_aux)
            
            # Retira a flag de inicial dos estados antigos
            estado_inicial_do_automato_local.inicial = False
            
            for estado_obj in af.estados.values():
                # Gera um sufixo único para evitar que chaves iguais no dicionário se sobrescrevam
                estado_obj.nome = f"{estado_obj.nome}_AF{i}"
                
                novo_af.add_estado(estado_obj)
        return novo_af