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

class TestSsh :
    def get_testf_contents(self, file_path):
        import sys
        import zipfile
        #with zipfile.ZipFile('/data/data/com.bitburrow.app/files/python3.8.zip', 'r') as zip_ref:
        #    zip_ref.extractall('/data/data/com.bitburrow.app/files/python3.8')
        # `import` doesn't find .so libraries in .zip, need to extract
        with zipfile.ZipFile('/data/data/com.bitburrow.app/files/nonstdlib.zip', 'r') as zip_ref:
            zip_ref.extractall('/data/data/com.bitburrow.app/files/python3.8')
        sys.path = [  # Termux has: python39.zip python3.9 python3.9/lib-dynload python3.9/site-packages
            '',
            '/data/data/com.bitburrow.app/files',  # binary libraries, e.g. _socket.cpython-38.so
            #'/data/data/com.bitburrow.app/files/python3.8',
            '/data/data/com.bitburrow.app/files/python3.8.zip',
            '/data/data/com.bitburrow.app/files/python3.8/site-packages',
            '/data/data/com.bitburrow.app/files/python3.8/lib-dynload',
            #'/data/data/com.bitburrow.app/files/libs64',
            #'/data/data/com.googlecode.pythonforandroid/files',
            #'/sdcard/com.googlecode.pythonforandroid/extras/python',
            #'/data/data/com.googlecode.pythonforandroid/files/python/lib/python2.6/lib-dynload',
            #'/data/data/com.googlecode.pythonforandroid/files/python/lib/python2.6',
            #'/data/data/com.googlecode.pythonforandroid/files/python/lib/python26.zip',
            #'/data/data/com.googlecode.pythonforandroid/files/python/lib/python39.zip',
            #'/data/data/com.googlecode.pythonforandroid/files/python/lib/python3.9',
            #'/data/data/com.googlecode.pythonforandroid/files/python/lib/python3.9/lib-dynload',
            #'/data/app/com.bitburrow.app-NZ5ZQRQ74435Y3IC5Pe43A==/lib/arm64',
            #'/data/data/com.srplab.starcore/lib'
        ]
        import subprocess
        def list_folder(f):
            print(f"Output of: ls -al {f}")
            proc = subprocess.run(['/system/bin/ls', '-al', f], capture_output=True)
            for line in proc.stdout.decode('utf-8').splitlines():
                print(line)
        list_folder("/data/data/com.bitburrow.app/files/")
        list_folder("/data/data/com.bitburrow.app/files/python3.8/")
        list_folder("/data/data/com.bitburrow.app/files/python3.8/site-packages/")
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect('192.168.8.1', username='root', password='XXXXXXXXXXXXXXXXXXXX')
        except paramiko.ssh_exception.NoValidConnectionsError:
            return "unable to connect"
        except paramiko.ssh_exception.AuthenticationException:
            return "authentication error"
        stdin, stdout, stderr = ssh.exec_command(f"date")
        opt = stdout.readlines()
        return "".join(opt)

