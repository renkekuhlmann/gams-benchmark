#!/bin/bash

function contains {
  local list="$1"
  local item="$2"
  if [[ $list =~ (^|[[:space:]])"$item"($|[[:space:]]) ]] ; then
    # yes, list include item
    result=0
  else
    result=1
  fi
  return $result
}

if [[ -n "$1" ]]; then
   testset=$1
else
   echo "No testset specified!"
   exit 1
fi

if [[ -n "$2" ]]; then
   format=$2
else
   echo "No format specified!"
   exit 1
fi

skip=
if [ $format == "pyomo" ]; then
   echo "$format" > convert.opt
else
   echo "Unknown format!"
   exit 1
fi

mkdir -p $testset/py
for f in $testset/gms/*.gms
do
   filename=$(basename -- "$f")
   filename="${filename%.*}"
   printf "%s... " $filename
   if `contains "$skip" "$filename"`; then
      printf "skip\n"
      continue
   fi

   gams $f lo=0 solver=convert optfile=1 || exit 1
   mv gams.py $testset/py/$filename.py
   rm *.lst

   printf "ok\n"
done

rm convert.opt
