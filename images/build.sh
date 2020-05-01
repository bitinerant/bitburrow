#!/bin/bash


## source/router-28994.svg from https://pixabay.com/vectors/router-network-equipment-28994/
# remove text from top of device
cat source/router-28994.svg |perl -pe 's|>netopia<|> <|' >temp1.svg
# convert to PNG (`convert` does a poor job at this)
inkscape --without-gui --export-height=256 --export-area-drawing temp1.svg --export-png=temp2.png
# clean up
rm temp1.svg
mv temp2.png modem-device.png


## source/arrow-35388.svg from https://pixabay.com/vectors/arrow-pointing-up-sign-symbol-35388/
# flip so it points down
cat source/arrow-35388.svg |perl -pe 's|matrix\(0,-1,1,0,0,16\)|matrix(0,1,1,0,0,0)|' >temp1.svg
# convert to PNG
inkscape --without-gui --export-height=256 temp1.svg --export-png=temp2.png
# add boder to shrink icon when displayed
convert temp2.png -bordercolor none -border 200 temp3.png
# clean up
rm temp1.svg temp2.png
mv temp3.png down-arrow.png


## source/browser-98386.svg from https://pixabay.com/vectors/browser-internet-www-global-98386/
# alternate option https://pixabay.com/illustrations/network-connections-communication-3537400/
# convert to PNG
inkscape --without-gui --export-height=256 source/browser-98386.svg --export-png=temp1.png
mv temp1.png internet.png


## source/wi-fi-2119225.svg from https://pixabay.com/vectors/wi-fi-wifi-symbol-wireless-2119225/
# alternate option https://pixabay.com/illustrations/wifi-wifi-signal-internet-network-1290667/
# convert to PNG
inkscape --without-gui --export-height=160 --export-area-drawing source/wi-fi-2119225.svg --export-png=temp2.png
# add boder to shrink icon when displayed
convert temp2.png -bordercolor none -border 200 temp3.png
# clean up
rm temp2.png
mv temp3.png wifi.png


## source/android-1293981.svg from https://pixabay.com/vectors/android-devices-laptop-mobile-1293981/
# alternate option https://pixabay.com/vectors/cross-device-cross-platform-desktop-1297696/
# cyan to black; fill on laptop white rather than transparent
cat source/android-1293981.svg |perl -pe 's|"#0cc"|"#000"|g; s|fill="none"|fill="#fff"|g;' > temp1.svg
# convert to PNG
inkscape --without-gui --export-height=256 temp1.svg --export-png=temp2.png
# clean up
rm temp1.svg
mv temp2.png wifi-devices.png


## source/router-157597.svg from https://pixabay.com/vectors/router-wireless-network-connection-157597
inkscape --without-gui --export-height=256 source/router-157597.svg --export-png=temp2.png
mv temp2.png generic-router.png


## source/cable-27193.svg from https://pixabay.com/vectors/cable-connection-wired-plugged-27193/
inkscape --without-gui --export-height=256 source/cable-27193.svg --export-png=temp2.png
mv temp2.png ethernet.png


