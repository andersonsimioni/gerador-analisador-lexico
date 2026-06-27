

class NoArvoreSintax:
    def __init__(self, parte_regex_original, left = None, right = None, child = None, nullable=False, first = None, last = None, follow = None):
        self.parte_regex_original = parte_regex_original
        
        self.left = left
        self.right = right
        self.child = child
        
        self.nullable = nullable
        self.first = set() if first is None else first
        self.last = set() if last is None else last
        self.follow = set() if follow is None else follow
    
    def get_parte_regex_valor(self): return self.parte_regex_original.get_valor()
    
    def get_parte_regex_id(self): return self.parte_regex_original.get_id()
    
    def build_nome_estado(collection): 
        items = [str(x.get_parte_regex_id()) for x in sorted(collection, key = lambda y: y.get_parte_regex_id())]
        items.sort()
        return "-".join(items)
    
    def get_ids_partes(collection):
        items = [x.get_parte_regex_id() for x in sorted(collection, key = lambda y: y.get_parte_regex_id())]
        return frozenset(items)