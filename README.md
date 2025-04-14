# Name of the team: RuntimeTerror

How to run project:

First of all, change subgraph name in `run.py` to the one you want to use.
Our pipeline steps are logged in `logs` dir.
Final results will be displayed in console.

HYPOTHESIS ARE IN THE RunTimeTerror.json !!!!

Then, install dependencies:
Windows:

```
py -m venv venv
./venv/Scripts/activate
pip install -r requirements.txt
py ./run.py
```

Posix:

```
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
python3 ./run.py
```

Put your api keys into .env file:

```
OPENAI_API_KEY=example_key
GEMINI_API_KEY=example_key
FIRECRAWL_API_KEY=example_key
PUBMED_API_KEY=example_key
```


Our custom stuff is in `src/stuff` dir.
