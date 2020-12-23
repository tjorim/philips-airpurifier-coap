python3 -m venv .venv
source .venv/bin/activate
pip3 install pycryptodomex
pip3 install aiocoap==0.4b3
alias aioairctrl="PYTHONPATH=$PWD/custom_components python3 -m philips_airpurifier.aioairctrl.cli"
