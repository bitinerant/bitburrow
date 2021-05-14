def tt(a,b) :
    print(a,b)
    return 666,777
g1 = 123
def yy(a,b,z) :
    print(a,b,z)
    return {'jack': 4098, 'sape': 4139}

class Multiply :
    def __init__(self,x,y) :
        self.a = x
        self.b = y
    
    def multiply(self,a,b):
        print("import coloredlogs ...")
        import logging
        import coloredlogs
        logger = logging.getLogger(__name__)
        coloredlogs.install(level='DEBUG')
        logger.info('Test phase 1')
        # import paramiko  # ImportError("cannot import name '_bcrypt' from 'bcrypt'
        return f"9×{a}×{b}={9*a*b}"
