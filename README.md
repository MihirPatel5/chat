# create environment 
python -m venv env

# active env
source env/bin/activate

# install dependencies
pip install -r requirements.txt

# run project
cd djnagochat/
python manage.py runeserver
