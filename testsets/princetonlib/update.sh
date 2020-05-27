#!/bin/bash

echo Downloading PrincetonLib:
curl -O http://www.gamsworld.org/performance/princetonlib/princeton.zip
unzip -u princeton.zip -d tmp
rm princeton.zip

mkdir -p gms
for f in tmp/gams/*/*.gms
do
   filename="$(basename -- $f)"
   echo "copy: " $filename
   cp $f gms/$filename
done
rm -rf tmp
