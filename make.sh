#!/bin/bash

function prebuild {
spaser
echo 'Pre-building v'$ver

pyuic5  ./ui/main.ui -o ./ui/main.py
echo 'ALL | main.py                 OK'
pyuic5 ./ui/about.ui -o ./ui/about.py
echo 'ALL | about.py                OK'

while true; do
    read -p "Rebuild resources.qrc ? (y/n) " yn
    case $yn in
        [Yy]* ) pyrcc5 ./ui/resources.qrc -o ./resources_rc.py ; echo 'ALL | resources.qrc           OK' ; break;;
        [Nn]* ) break;;
        * ) echo "Please answer yes or no.";;
    esac
done

create-version-file ./ui/metadata.yml --outfile ./ui/file_version_info.txt --version $ver
echo 'WIN | file_version_info.txt   OK'

sed "s/[0-9].[0-9].[0-9]/$ver/" osx.spec > osx.spec1
mv osx.spec1 osx.spec
echo 'OSX | osx.spec                OK'

echo 'Pre-build finished'
spaser
}

function version {
    IFS='.' read -r -a array <<< "$ver"
    X=${array[0]}
    Y=${array[1]}
    Z=${array[2]}



    Z=$(($Z + 1))

    if [ "$Z" -gt "9" ]; then
        Z=0
        Y=$(($Y + 1))
    fi
    if [ "$Y" -gt "9" ]; then
        Y=0
        X=$(($X + 1))
    fi
    if [ "$X" -gt "9" ]; then
        echo "Version > 9.9.9"
        exit;
    fi


    ver="${X}.${Y}.${Z}"

    echo "$ver"

    sed "s/[0-9].[0-9].[0-9]/$ver/" ui/version.py > ui/version.py_temp
    mv ui/version.py_temp ui/version.py
}

function spaser {
    echo ""
    echo "----------------------------"
    echo ""
}

function commit {
    spaser
    echo -e "v$ver\n\n$(cat commit)" > commit_temp
    cat commit_temp
    spaser
    git commit -a --file=commit_temp
    rm commit_temp
    git status
    spaser
}

function tag {
    spaser
    tag='v'$ver
    echo 'git tag ' $tag
    git tag $tag
    spaser
}

function push {
    spaser
    echo 'git push'  
    git push
    git push origin --tags
    spaser
}

file="./ui/version.py" 
ver=$(echo $(cat "$file") | egrep -o '(\d+\.\d+\.\d+-?\w*)')

echo 'Push script for ZigStar GW MT v'$ver
spaser
while true; do
    read -p "Increase version? (y/n) " yn
    case $yn in
        [Yy]* ) version; break;;
        [Nn]* ) break;;
        * ) echo "Please answer yes or no.";;
    esac
done
prebuild

git status
spaser

while true; do
    read -p "Make commit? (y/n) " yn
    case $yn in
        [Yy]* ) commit; break;;
        [Nn]* ) spaser; echo 'Finished'; exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

while true; do
    read -p "Put tag? (y/n) " yn
    case $yn in
        [Yy]* ) tag; break;;
        [Nn]* ) break;;
        * ) echo "Please answer yes or no.";;
    esac
done

while true; do
    read -p "Push origin? (y/n) " yn
    case $yn in
        [Yy]* ) push; break;;
        [Nn]* ) break;;
        * ) echo "Please answer yes or no.";;
    esac
done

echo 'Finished'