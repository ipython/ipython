INKSCAPE=/Applications/Inkscape.app/Contents/Resources/bin/inkscape

${INKSCAPE} -z -C --file=ipynb_icon_16x16.svg  --export-png=ipynb_icon_16x16_uncrush.png
${INKSCAPE} -z -C --file=ipynb_icon_24x24.svg  --export-png=ipynb_icon_24x24_uncrush.png
${INKSCAPE} -z -C --file=ipynb_icon_32x32.svg  --export-png=ipynb_icon_32x32_uncrush.png
${INKSCAPE} -z -C --file=ipynb_icon_512x512.svg  --export-png=ipynb_icon_64x64_uncrush.png -w 64 -h 64
${INKSCAPE} -z -C --file=ipynb_icon_512x512.svg  --export-png=ipynb_icon_128x128_uncrush.png -w 128 -h 128
${INKSCAPE} -z -C --file=ipynb_icon_512x512.svg  --export-png=ipynb_icon_256x256_uncrush.png -w 256 -h 256
${INKSCAPE} -z -C --file=ipynb_icon_512x512.svg  --export-png=ipynb_icon_512x512_uncrush.png -w 512 -h 512


for file in `ls *_uncrush.png`; do
    pngcrush -brute  -l 9 -reduce -rem alla -rem text -rem time -rem gAMA -rem cHRM -rem iCCP -rem sRGB $file `basename $file _uncrush.png`.png
    rm $file
done
