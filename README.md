# NICE
Project for the Virgo DetChar Activities, here there are the setup instructions for local installation! 

## Installation

NICE provides an user-friendly configuration of the environment needed for its usage. You should be able to execute what follows:

1. Clone repository from this GitHub repository;

2. Go to the parent directory of the project:
```bash
cd ../
```
3. Create a Python3 environment called `venv-django-py3`. This should be done with `pip` installing functionalities included:
```bash
python3 -m venv venv-django-py3
```
4. Activate the empty environment:
```bash
source venv-django-py3/bin/activate
```
5. Check if the default packages are installed and up-to dated. Check also the versions Python3 version with `python` command:
```bash
python --version
pip list
```
6. Go to the main directory of the project and install the requirements package from the `requirements.txt` file, which has been created with `pip freeze > requirements.txt`:
```bash
pip install -r requirements.txt
```
7. Setup the environment variables using the provided bash file:
```bash
source setup_vmutils.sh
```

Remember to activate the environment and the variables every time you open the terminal!

