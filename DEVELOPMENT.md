# Chorus
This is a Peru package. To set up the workspace:
```
mkdir Chorus
brazil ws create --root Chorus --name Chorus --vs Chorus/development-peru
cd Chorus
brazil ws use --p Chorus
```

We use Peru for package management. Install the required packages for peru build:
```
pip install hatch
pip install -U mypy
```

Then run
```
brazil-build
```
to create the executable. If above command fails with error, try
```
brazil-wire-ctl clean-workspace && brazil-wire-ctl restart && brazil ws --clean && brazil-build clean && brazil-build
```
Note the current version hasn't split up unit tests and integrational tests properly. So you need AWS credential for API calls to pass pytest.

After build successfully, the executable under
```
.venv/bin/python3.12
```
shall come with the Chorus package installed (i.e. you can `import chorus`).

## Hetrogenous Agent
Install the needed dependencies with:
1. langchain : ```pip install ".[langchain]"```