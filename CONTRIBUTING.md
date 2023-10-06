# Contributing to Danswer
Hey there! We are so excited that you're interested in Danswer.

As an open source project in a rapidly changing space, we welcome all contributions.


## 💃 Guidelines
### Contribution Opportunities
The [GitHub issues](https://github.com/danswer-ai/danswer/issues) page is a great place to start for contribution ideas.

Issues that have been explicitly approved by the maintainers (aligned with the direction of the project)
will be marked with the `approved by maintainers` label.
Issues marked `good first issue` are an especially great place to start.

**Connectors** to other tools are another great place to contribute. For details on how, refer to this
[README.md](https://github.com/danswer-ai/danswer/blob/main/backend/danswer/connectors/README.md).

If you have a new/different contribution in mind, we'd love to hear about it!
Your input is vital to making sure that Danswer moves in the right direction.
Before starting on implementation, please raise a GitHub issue.

And always feel free to message us (Chris Weaver / Yuhong Sun) on Slack / Discord directly about anything at all. 


### Contributing Code
To contribute to this project, please follow the
["fork and pull request"](https://docs.github.com/en/get-started/quickstart/contributing-to-projects) workflow.
When opening a pull request, mention related issues and feel free to tag relevant maintainers.

Before creating a pull request please make sure that the new changes conform to the formatting and linting requirements.
See the [Formatting and Linting](#-formatting-and-linting) section for how to run these checks locally.


### Getting Help 🙋
Our goal is to make contributing as easy as possible. If you run into any issues please don't hesitate to reach out.
That way we can help future contributors and users can avoid the same issue.

We also have support channels and generally interesting discussions on our
[Slack](https://join.slack.com/t/danswer/shared_invite/zt-1u3h3ke3b-VGh1idW19R8oiNRiKBYv2w)
and 
[Discord](https://discord.gg/TDJ59cGV2X).

We would love to see you there!


## Get Started 🚀
Danswer being a fully functional app, relies on several external pieces of software, specifically:
- Postgres (Relational DB)
- [Vespa](https://vespa.ai/) (Vector DB/Search Engine)

This guide provides instructions to set up the Danswer specific services outside of Docker because it's easier for
development purposes but also feel free to just use the containers and update with local changes by providing the
`--build` flag.


### Local Set Up
We've tested primarily with Python versions >= 3.11 but the code should work with Python >= 3.9.

This guide skips a few optional features for simplicity, reach out if you need any of these:
- User Authentication feature
- File Connector background job


#### Installing Requirements
Currently, we use pip and recommend creating a virtual environment.

For convenience here's a command for it:
```bash
python -m venv .venv
source .venv/bin/activate
```
_For Windows activate via:_
```bash
.venv\Scripts\activate
```

Install the required python dependencies:
```bash
pip install -r danswer/backend/requirements/default.txt
pip install -r danswer/backend/requirements/dev.txt
```

Install [Node.js and npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) for the frontend.
Once the above is done, navigate to `danswer/web` run:
```bash
npm i
```

Install Playwright (required by the Web Connector), with the python venv active, run:
```bash
playwright install
```


#### Dependent Docker Containers
First navigate to `danswer/deployment/docker_compose`, then start up the containers with:

Postgres:
```bash
docker compose -f docker-compose.dev.yml -p danswer-stack up -d relational_db
```

Vespa:
```bash
docker compose -f docker-compose.dev.yml -p danswer-stack up -d index
```


#### Running Danswer

Setup a folder to store config. Navigate to `danswer/backend` and run:
```bash
mkdir dynamic_config_storage
```

To start the frontend, navigate to `danswer/web` and run:
```bash
AUTH_TYPE=disabled npm run dev
```
_for Windows, run:_
```bash
(SET "AUTH_TYPE=disabled" && npm run dev)
```


The first time running Danswer, you will need to run the DB migrations for Postgres.
Navigate to `danswer/backend` and with the venv active, run:
```bash
alembic upgrade head
```

Additionally, we have to package the Vespa schema deployment:
Nagivate to `danswer/backend/danswer/datastores/vespa/app_config` and run:
```bash
zip -r ../vespa-app.zip .
```
- Note: If you don't have the `zip` utility, you will need to install it prior to running the above

To run the backend API server, navigate back to `danswer/backend` and run:
```bash
AUTH_TYPE=disabled \
DYNAMIC_CONFIG_DIR_PATH=./dynamic_config_storage \
VESPA_DEPLOYMENT_ZIP=./danswer/datastores/vespa/vespa-app.zip \
uvicorn danswer.main:app --reload --port 8080
```
_For Windows (for compatibility with both PowerShell and Command Prompt):_
```bash
powershell -Command "
    $env:AUTH_TYPE='disabled'
    $env:DYNAMIC_CONFIG_DIR_PATH='./dynamic_config_storage'
    $env:VESPA_DEPLOYMENT_ZIP='./danswer/datastores/vespa/vespa-app.zip'
    uvicorn danswer.main:app --reload --port 8080 
"
```

To run the background job to check for connector updates and index documents, navigate to `danswer/backend` and run:
```bash
PYTHONPATH=. DYNAMIC_CONFIG_DIR_PATH=./dynamic_config_storage python danswer/background/update.py
```
_For Windows:_
```bash
powershell -Command " $env:PYTHONPATH='.'; $env:DYNAMIC_CONFIG_DIR_PATH='./dynamic_config_storage'; python danswer/background/update.py "
```

To run the background job to check for periodically check for document set updates, navigate to `danswer/backend` and run:
```bash
PYTHONPATH=. DYNAMIC_CONFIG_DIR_PATH=./dynamic_config_storage python danswer/background/document_set_sync_script.py
```
_For Windows:_
```bash
powershell -Command " $env:PYTHONPATH='.'; $env:DYNAMIC_CONFIG_DIR_PATH='./dynamic_config_storage'; python danswer/background/document_set_sync_script.py "
```

To run Celery, which handles deletion of connectors + syncing of document sets, navigate to `danswer/backend` and run:
```bash
PYTHONPATH=. DYNAMIC_CONFIG_DIR_PATH=./dynamic_config_storage celery -A  danswer.background.celery worker --loglevel=info --concurrency=1
```
_For Windows:_
```bash
powershell -Command " $env:PYTHONPATH='.'; $env:DYNAMIC_CONFIG_DIR_PATH='./dynamic_config_storage'; celery -A  danswer.background.celery worker --loglevel=info --concurrency=1 "
```

Note: if you need finer logging, add the additional environment variable `LOG_LEVEL=DEBUG` to the relevant services.

### Formatting and Linting
#### Backend
For the backend, you'll need to setup pre-commit hooks (black / reorder-python-imports).
First, install pre-commit (if you don't have it already) following the instructions
[here](https://pre-commit.com/#installation).
Then, from the `danswer/backend` directory, run:
```bash
pre-commit install
```

Additionally, we use `mypy` for static type checking.
Danswer is fully type-annotated, and we would like to keep it that way! 
Right now, there is no automated type checking at the moment (coming soon), but we ask you to manually run it before
creating a pull requests with `python -m mypy .` from the `danswer/backend` directory.


#### Web
We use `prettier` for formatting. The desired version (2.8.8) will be installed via a `npm i` from the `danswer/web` directory. 
To run the formatter, use `npx prettier --write .` from the `danswer/web` directory.
Like `mypy`, we have no automated formatting yet (coming soon), but we request that, for now,
you run this manually before creating a pull request.


### Release Process
Danswer follows the semver versioning standard.
A set of Docker containers will be pushed automatically to DockerHub with every tag.
You can see the containers [here](https://hub.docker.com/search?q=danswer%2F).

As pre-1.0 software, even patch releases may contain breaking or non-backwards-compatible changes.
