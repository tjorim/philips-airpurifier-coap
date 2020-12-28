python="python3"
pip="pip3"
manifest=./custom_components/philips_airpurifier/manifest.json
aioairctrl=$(grep -Po '(?<=")aioairctrl[^"]+(?=")' $manifest)

if ! command -v $python &> /dev/null
then
    echo "$python could not be found"
    return
fi

$python -m venv .venv
source .venv/bin/activate

if ! command -v $pip &> /dev/null
then
    echo "$pip could not be found"
    return
fi

$pip install $aioairctrl
aioairctrl --help
