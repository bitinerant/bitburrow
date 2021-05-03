# README

## to repopulate the folders 'assets' and 'jniLibs'

```
sudo apt install unzip
export TARGET=$(pwd)
mkdir assets jniLibs
cd /tmp
git clone https://github.com/srplab/starcore_for_android.git
git clone https://github.com/srplab/starcore_for_flutter.git
cp -i starcore_for_flutter/starflut/example/android/app/src/main/assets/python3.9.zip "$TARGET/assets"
unzip starcore_for_android/android.python.3.9.0.zip 'python-3.9.0/*/libpython3.9.so'
unzip starcore_for_android/starcore_for_android.3.7.6.zip 'libs/*/libstar_python39.so'
cp -R libs/* python-3.9.0/
cp -R python-3.9.0/* "$TARGET/jniLibs"
rm -R libs python-3.9.0
unzip starcore_for_android/android.python.3.9.0.zip 'python-3.9.0/*/lib-dynload/unicodedata.cpython-39.so'
unzip starcore_for_android/android.python.3.9.0.zip 'python-3.9.0/*/lib-dynload/zlib.cpython-39.so'
cp -R python-3.9.0/* "$TARGET/assets"
rm -R python-3.9.0
#optional: rm -R starcore_for_android
#optional: rm -R starcore_for_flutter
cd "$TARGET/assets"
find . -name lib-dynload -type d |xargs --max-args=1 -d '\n' -I DEV find DEV -type f -exec mv -i {} DEV/.. \;
rmdir */lib-dynload
```
