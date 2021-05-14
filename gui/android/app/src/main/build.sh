#!/bin/bash
#
# build or update the folders 'assets' and 'jniLibs'
#
# prerequisites: sudo apt install -y unzip zip wget
#
set -e
# this must be run from the directory .../android/app/src/main
if ! (pwd |grep --quiet /android/app/src/main$); then exit 1; fi
export TARGET=$(pwd)
mkdir -p assets jniLibs
#
# extract dependencies from the two large srplab GitHub repos
#
cd ../../../../../../flutter/  # your Flutter code repo
if [ ! -d starcore_for_android ]; then
    git clone https://github.com/srplab/starcore_for_android.git
fi
if [ ! -d starcore_for_flutter ]; then
    git clone https://github.com/srplab/starcore_for_flutter.git
fi
cp starcore_for_flutter/starflut/example/android/app/src/main/assets/python3.9.zip "$TARGET/assets"
# note that Termux libpython also works instead of the starcore one: /data/data/com.termux/files/usr/lib/libpython3.9.so.1.0
unzip -q starcore_for_android/android.python.3.9.0.zip 'python-3.9.0/*/libpython3.9.so'
unzip -q starcore_for_android/starcore_for_android.3.7.6.zip 'libs/*/libstar_python39.so'
cp -R libs/* python-3.9.0/
cp -R python-3.9.0/* "$TARGET/jniLibs"
rm -R libs python-3.9.0
#
# extract CPython binaries
#
export CPYTHON="unicodedata zlib _socket math select array _hashlib _struct binascii _blake2 _contextvars _random _posixsubprocess _csv"
#available in android.python.3.9.0.zip: array audioop binascii cmath fcntl grp math mmap ossaudiodev parser pyexpat resource select syslog termios unicodedata xxlimited zlib _asyncio _bisect _blake2 _codecs_cn _codecs_hk _codecs_iso2022 _codecs_jp _codecs_kr _codecs_tw _contextvars _csv _ctypes_test _datetime _decimal _elementtree _hashlib _heapq _json _lsprof _md5 _multibytecodec _multiprocessing _opcode _pickle _posixsubprocess _queue _random _sha1 _sha256 _sha3 _sha512 _socket _sqlite3 _ssl _statistics _struct _testbuffer _testcapi _testimportmultiple _testinternalcapi _testmultiphase _xxsubinterpreters _xxtestfuzz _zoneinfo
for M in $CPYTHON; do
    unzip -q starcore_for_android/android.python.3.9.0.zip 'python-3.9.0/*/lib-dynload/'$M'.cpython-39.so'
done
cp -R python-3.9.0/* "$TARGET/assets"
rm -R python-3.9.0
cd "$TARGET/assets"
find . -name lib-dynload -type d |xargs --max-args=1 -d '\n' -I DEV find DEV -type f -exec mv {} DEV/.. \;
rmdir */lib-dynload
#
# download and merge needed Python modules into python3.9.zip
#
export MODULES="paramiko-2.7.2 cryptography-3.4.7 six-1.16.0 bcrypt-3.2.0 PyNaCl-1.4.0 coloredlogs-15.0 humanfriendly-9.1"
cd /tmp
# from https://pypi.org/project/paramiko/
wget --no-clobber -q https://files.pythonhosted.org/packages/cf/a1/20d00ce559a692911f11cadb7f94737aca3ede1c51de16e002c7d3a888e0/paramiko-2.7.2.tar.gz
# from https://pypi.org/project/cryptography/
wget --no-clobber -q https://files.pythonhosted.org/packages/9b/77/461087a514d2e8ece1c975d8216bc03f7048e6090c5166bc34115afdaa53/cryptography-3.4.7.tar.gz
# from https://pypi.org/project/six/
wget --no-clobber -q https://files.pythonhosted.org/packages/71/39/171f1c67cd00715f190ba0b100d606d440a28c93c7714febeca8b79af85e/six-1.16.0.tar.gz
# from https://pypi.org/project/bcrypt/
wget --no-clobber -q https://files.pythonhosted.org/packages/d8/ba/21c475ead997ee21502d30f76fd93ad8d5858d19a3fad7cd153de698c4dd/bcrypt-3.2.0.tar.gz
# from https://pypi.org/project/PyNaCl/
wget --no-clobber -q https://files.pythonhosted.org/packages/cf/5a/25aeb636baeceab15c8e57e66b8aa930c011ec1c035f284170cacb05025e/PyNaCl-1.4.0.tar.gz
# from https://pypi.org/project/coloredlogs/
wget --no-clobber -q https://files.pythonhosted.org/packages/ce/ef/bfca8e38c1802896f67045a0c9ea0e44fc308b182dbec214b9c2dd54429a/coloredlogs-15.0.tar.gz
# from https://pypi.org/project/humanfriendly/
wget --no-clobber -q https://files.pythonhosted.org/packages/31/0e/a2e882aaaa0a378aa6643f4bbb571399aede7dbb5402d3a1ee27a201f5f3/humanfriendly-9.1.tar.gz
for M in $MODULES; do
    export N=$(echo $M |sed 's/-[0-9\.]*$//; s/PyNaCl/nacl/; s/six/six.py/;')  # N is name without version
    cd "$TARGET/assets"
    tar xzf /tmp/$M.tar.gz
    cd $M
    if [ -d src ]; then cd src; fi  # for cryptography, bcrypt
    #if [ ! -d $N ]; then export N=$N.py; fi  # for six
    zip -r --quiet "$TARGET/"assets/python3.9.zip $N
    rm -r "$TARGET/assets/$M"
done

