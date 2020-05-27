#!/bin/bash

echo Downloading MINLPlib:
curl -O http://www.minlplib.org/instancedata.csv
curl -O http://www.minlplib.org/minlplib.solu
curl -O http://www.minlplib.org/minlplib_gms.zip
unzip -u minlplib_gms.zip -d ../
rm minlplib_gms.zip
