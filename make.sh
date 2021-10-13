#!/bin/bash
file="./ui/version.py" 
name=$(cat "$file")     
echo '--- ZigStar GW Multi tool ---'
echo 'Building v'${name:11:5} 
pyuic5 ./ui/main.ui -o ./ui/main.py
echo 'main.py OK'
pyuic5 ./ui/about.ui -o ./ui/about.py
echo 'about.py OK'
pyrcc5 -o ./resources_rc.py ./ui/resources.qrc
echo 'resources.qrc OK' 

create-version-file ./ui/metadata.yml --outfile ./ui/file_version_info.txt --version ${name:11:5} 
echo 'file_version_info.txt OK'