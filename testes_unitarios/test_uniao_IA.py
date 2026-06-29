# ==========================================
# 1. MOCKS (Simulando o seu ecossistema)
# ==========================================
class MockTransicao:
    def __init__(self, origem, destino, simbolo):
        self.estado_origem = origem
        self.estado_destino = destino
        self.simbolo = simbolo

class MockEstado:
    def __init__(self, nome, inicial=False, final=False):
        self.nome = nome
        self.inicial = inicial
        self.final = final
        self.transicoes = {} 
        
    def add_transicao(self, transicao):
        if transicao.simbolo not in self.transicoes:
            self.transicoes[transicao.simbolo] = [] # <-- CORRIGIDO
        self.transicoes[transicao.simbolo].append(transicao)

class MockAutomato:
    def __init__(self, nome):
        self.nome = nome
        self.estados = {} 
        
    def add_estado(self, estado):
        self.estados[estado.nome] = estado
        
    def get_inicial(self):
        for e in self.estados.values():
            if e.inicial:
                return e
        return None

# ==========================================
# 2. A SUA CLASSE DE UNIÃO 
# ==========================================
class Unificador_de_automato:
    
    @staticmethod
    def uniao_de_automato(lista_de_AF):
        print("\n" + "="*70)
        print(" INICIANDO UNIÃO DE AUTÔMATOS (10 ESTADOS TOTAIS)")
        print("="*70)

        novo_af = MockAutomato("AFN_Uniao_Gigante")
        inicial_novo = MockEstado("q_inicial_uniao", inicial=True, final=False)
        novo_af.add_estado(inicial_novo)
        
        print(f"\n[ETAPA 1] Criado novo estado inicial global: [{inicial_novo.nome}]")

        for i, af in enumerate(lista_de_AF):
            print(f"\n[ETAPA 2.{i+1}] Acoplando Autômato: {af.nome}")
            estado_inicial_do_automato_local = af.get_inicial()
            
            # Ligação por Epsilon 
            transicao_aux = MockTransicao(inicial_novo, estado_inicial_do_automato_local, "&")
            inicial_novo.add_transicao(transicao_aux)
            
            print(f"  -> Ligando [{inicial_novo.nome}] ao [{estado_inicial_do_automato_local.nome}] via '&'")
            
            # Remove a flag de inicial dos antigos
            estado_inicial_do_automato_local.inicial = False
            
            # Renomeia e transfere todos os estados
            for estado_obj in list(af.estados.values()):
                nome_antigo = estado_obj.nome
                estado_obj.nome = f"{nome_antigo}_AF{i}"
                
                novo_af.add_estado(estado_obj)
                print(f"  -> Estado [{nome_antigo}] renomeado e transferido como [{estado_obj.nome}].")

        print("\n" + "="*70)
        return novo_af


# ==========================================
# 3. EXECUÇÃO DO TESTE COM 10 ESTADOS
# ==========================================
def executar_teste_uniao_maior():
    # --- AUTÔMATO 1: "ab" (3 estados) ---
    af1 = MockAutomato("AF_Letras")
    q0_af1 = MockEstado("q0", inicial=True)
    q1_af1 = MockEstado("q1")
    q2_af1 = MockEstado("q2", final=True)
    
    q0_af1.add_transicao(MockTransicao(q0_af1, q1_af1, "a"))
    q1_af1.add_transicao(MockTransicao(q1_af1, q2_af1, "b"))
    
    af1.add_estado(q0_af1)
    af1.add_estado(q1_af1)
    af1.add_estado(q2_af1)
    
    # --- AUTÔMATO 2: "123" (4 estados) ---
    af2 = MockAutomato("AF_Numeros")
    q0_af2 = MockEstado("q0", inicial=True) # Colisão de nome proposital
    q1_af2 = MockEstado("q1")               # Colisão de nome proposital
    q2_af2 = MockEstado("q2")               # Colisão de nome proposital
    q3_af2 = MockEstado("q3", final=True)
    
    q0_af2.add_transicao(MockTransicao(q0_af2, q1_af2, "1"))
    q1_af2.add_transicao(MockTransicao(q1_af2, q2_af2, "2"))
    q2_af2.add_transicao(MockTransicao(q2_af2, q3_af2, "3"))
    
    af2.add_estado(q0_af2)
    af2.add_estado(q1_af2)
    af2.add_estado(q2_af2)
    af2.add_estado(q3_af2)

    # --- AUTÔMATO 3: "x" (2 estados) ---
    af3 = MockAutomato("AF_X")
    q0_af3 = MockEstado("q0", inicial=True) # Terceira colisão no q0!
    q1_af3 = MockEstado("q1", final=True)
    
    q0_af3.add_transicao(MockTransicao(q0_af3, q1_af3, "x"))
    
    af3.add_estado(q0_af3)
    af3.add_estado(q1_af3)
    
    # --- REALIZANDO A UNIÃO TRIPLA ---
    lista_automatos = [af1, af2, af3]
    af_unido = Unificador_de_automato.uniao_de_automato(lista_automatos)
    
    # --- ASSERTS (Verificação Matemática) ---
    # Verifica se atingimos exatamente 10 estados
    assert len(af_unido.estados) == 10, f"Erro: Esperado 10 estados, mas encontrou {len(af_unido.estados)}."
    
    # Verifica se a colisão tripla do q0 foi resolvida
    assert "q0_AF0" in af_unido.estados, "q0 do AF1 sumiu!"
    assert "q0_AF1" in af_unido.estados, "q0 do AF2 sumiu!"
    assert "q0_AF2" in af_unido.estados, "q0 do AF3 sumiu!"
    
    # Verifica os finais de cada ramificação
    assert af_unido.estados["q2_AF0"].final is True, "AF1 perdeu sua flag final."
    assert af_unido.estados["q3_AF1"].final is True, "AF2 perdeu sua flag final."
    assert af_unido.estados["q1_AF2"].final is True, "AF3 perdeu sua flag final."
    
    # --- IMPRESSÃO DO RESULTADO FINAL ---
    print(" RESUMO DO AUTÔMATO UNIFICADO (10 ESTADOS)")
    print("="*70)
    
    # Ordenando as chaves para o print ficar bonito no terminal
    for nome_estado in sorted(af_unido.estados.keys()):
        estado = af_unido.estados[nome_estado]
        tipo = ""
        if estado.inicial: tipo += "[INICIAL] "
        if estado.final: tipo += "[FINAL]"
        
        print(f"Estado: {estado.nome: <18} {tipo}")
        for simb, transicoes in estado.transicoes.items():
            for t in transicoes:
                print(f"  -- {simb} --> {t.estado_destino.nome}")
                
    print("\n🚀 ASSERTIONS PASSARAM: União de 10 estados processada perfeitamente!\n")

if __name__ == "__main__":
    executar_teste_uniao_maior()