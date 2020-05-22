# BitBurrow

[![Travis Build Status][travis-build-status-svg]][travis-build-status] 
[![Code Style][black-code-style-svg]][black-code-style]

A safe internet tunnel for the whole home that anyone can set up.

The goal of the BitBurrow project is to make it really easy for non-technical people to set up
a secure VPN for their whole home. We hope to eventually automate most of these steps.

## Development Status

This software is not yet ready for general use.

## Developer Guide

To run on Linux:

* make sure you have Python 3.6 or newer
* install Python package dependencies:

    ```bash
    python -m pip install --upgrade --user pip setuptools virtualenv
    mkdir -p <your_python_virtual_env_directory> && cd $_
    python -m virtualenv bitburrow
    source bitburrow/bin/activate
    cd <your_code_dir>/bitburrow
    export TO_PIP_INSTALL=$(grep -Po '^requirements *= *\K.*' build/buildozer.spec |grep -Po '((, *)|(^))\K[^, ]*' |grep -v -e '^python3\b' -e 'hostpython3\b' -e '^kivy\b' |tr '\n' ' ')
    python -m pip install $TO_PIP_INSTALL
    ```

* install Kivy for Python 3.6-3.7:

    ```bash
    python -m pip install kivy
    ```

* install Kivy for Python 3.8 (until Kivy 2.0 is out):

    ```bash
    python -m pip install kivy[base] kivy_examples --pre --extra-index-url https://kivy.org/downloads/simple/
    ```

* run:

    ```bash
    python main.py
    ```

To run unit tests and style checks on the project, install `tox` into your virtual
environment and run it.

```bash
(venv) $ pip install tox
(venv) $ tox
```

To format the code automatically using `black`:

```bash
(venv) $ tox -e fmt
```

## Building for Android

See also [Create a package for Android](https://kivy.org/doc/stable/guide/packaging-android.html)

* Download BitBurrow source code:

    ```bash
    cd <your code directory>
    git clone --recursive-submodules https://github.com/bitinerant/bitburrow.git
    ```

* Set up an LXD container for building (can be safely re-run):

    ```bash
    sudo apt install -y ansible lxd
    cd bitburrow/build/
    ansible-playbook bootstrap.yml
    cat tmp/instructions
    ```

* Edit the 2 files as described in the instructions displayed from the above command
* Download and install build tools on container and copy source to container (may take a long time; can be safely re-run):

    ```bash
    ansible-playbook -i tmp/hosts configure.yml
    ```

* Build (first run takes much longer):

    ```bash
    ssh kivy-buildozer 'source .profile && cd bitburrow/build/ && /usr/local/bin/buildozer android clean && /usr/local/bin/buildozer android release'
    ssh kivy-buildozer 'cat bitburrow/build/bin/bitburrow*' >/tmp/bitburrow_android_testing.apk
    adb install -r /tmp/bitburrow_android_testing.apk  # if it fails, manually uninstall old version and retry
    ```

* Make code changes locally: rerun above 2 steps (`configure.yml` and `buildozer android release`); repeat

### Notes

* To clean everything (hopefully this is not necessary): `ssh kivy-buildozer rm -Rf bitburrow .buildozer`
* Buildozer should automatically sign the .apk, but you can manually sign via:

    ```bash
    ssh kivy-buildozer 'source .profile && cd bitburrow/build/ && jarsigner -verbose -keystore $P4A_RELEASE_KEYSTORE -storepass $P4A_RELEASE_KEYSTORE_PASSWD bin/bitburrow*.apk $P4A_RELEASE_KEYALIAS'
    #verify: jarsigner -verify -keystore $P4A_RELEASE_KEYSTORE bin/bitburrow*.apk
    ```

* Align the .apk (optional; [more info](https://github.com/kivy/kivy/wiki/Creating-a-Release-APK)):

    ```bash
    sudo apt install -y zipalign
    zipalign -v 4 bin/bitburrow*.apk bin/bitburrow-final.apk
    ```

* Kivy docs describe how you can build with [Buildozer](https://kivy.org/doc/stable/guide/packaging-android.html#buildozer) ([Buildozer on readthedocs](https://buildozer.readthedocs.io/en/latest/); also [install instructions](https://buildozer.readthedocs.io/en/latest/installation.html); [Buildozer on GitHub](https://github.com/kivy/buildozer); [Buildozer on PyPi](https://pypi.org/project/buildozer/); [Buildozer Docker image](https://hub.docker.com/r/kivy/buildozer)) **or** via [python-for-android](https://kivy.org/doc/stable/guide/packaging-android.html#packaging-with-python-for-android) ([Build a Kivy or SDL2 application](https://python-for-android.readthedocs.io/en/latest/quickstart/#usage)) **or** [Kivy Launcher](https://kivy.org/doc/stable/guide/packaging-android.html#packaging-your-application-for-the-kivy-launcher)
* Running in Kivy Launcher (**untested**; [from Google Play](https://play.google.com/store/apps/details?id=org.kivy.pygame)):

    ```bash
    cd bitburrow/
    # move symlinks elsewhere
    printf "title=BitBurrow\nauthor=bitinerant\norientation=portrait\n" >android.txt
    cd ..
    adb push bitburrow /storage/emulated/0/kivy/
    ```

<!-- Badges -->
[travis-build-status]: https://travis-ci.org/bitinerant/cleargopher
[travis-build-status-svg]: https://travis-ci.org/bitinerant/cleargopher.svg?branch=master
[black-code-style]: https://github.com/ambv/black
[black-code-style-svg]: https://img.shields.io/badge/code%20style-black-000000.svg
