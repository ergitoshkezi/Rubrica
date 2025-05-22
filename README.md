Open Visual Studio Code, Create a Python environment/Folder of your preference, eg:
   python -m venv Prova 

   
Then enter on the environment created(cd  Prova) and launch this command:
  git clone https://github.com/ergitoshkezi/Rubrica.git
  
  
Install the required libraries list on the file requirements.txt:
  pip install -r requirements.txt
  
  
Execute the Run.py file:
  python Run.py

  
After Run.py is performed, please go on a browser and launch:
  http://localhost:5000



Ho scelto l'attributo Città di caricare i valori tramite un csv, inoltre il diagramma E/R e molto semplice
uno a molti:
Rubrica_Login(1,1) Rubrica(0,N)

La folder structure è la seguente dove, Routes e Models contengono il codice vero e proprio per registrazione login e aggiungere rubriche:

├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── models.py
│   └── templates/
│       ├── login.html
│       ├── index.html
│       └── form.html
├── config.py
└── run.py
