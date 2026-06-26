class NoArvoreSintax:
    def __init__(self, parte_regex_original, left = None, right = None, child = None, nullable=False, first = None, last = None, follow = None):
        self.parte_regex_original = parte_regex_original
        
        self.left = left
        self.right = right
        self.child = child
        
        self.nullable = nullable
        self.first = [] if first is None else first
        self.last = [] if last is None else last
        self.follow = [] if follow is None else follow