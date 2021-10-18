#!/bin/bash
file="./ui/version.py" 
ver=$(echo $(cat "$file") | egrep -o '(\d+\.\d+\.\d+-?\w*)')

echo '--- ZigStar GW Multi tool ---'
echo 'Building v'$ver

pyuic5  ./ui/main.ui -o ./ui/main.py
echo 'main.py OK'
pyuic5 ./ui/about.ui -o ./ui/about.py
echo 'about.py OK'
pyrcc5 ./ui/resources.qrc -o ./resources_rc.py 
echo 'resources.qrc OK' 

create-version-file ./ui/metadata.yml --outfile ./ui/file_version_info.txt --version $ver
echo 'file_version_info.txt OK'

sed "s/[0-9].[0-9].[0-9]/$ver/" osx.spec > osx.spec1
mv osx.spec1 osx.spec
echo 'osx.spec OK'

echo '--------- Finished ----------'