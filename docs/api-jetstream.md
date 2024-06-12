# The API on Jetstream

There are two ways to make this run on an instance: (1) run the API directly on the instance and (2) run the API in a Docker container (recommended). In both cases you first need to get the API code:

```bash
$ git clone https://github.com/lapps-askme/askme-light/
$ cd askme-light/code
```

## Running directly on the instance

The basic instance comes with Python version 3.10.12. Some modules are already installed, see [jetstream-freeze.txt](jetstream-freeze.txt), but most of what we need is not included. Install the requirements for the API as per usual, using a virtual environment.

```bash
$ python3 -m venv /home/ubuntu/venv/askme-light
$ source /home/ubuntu/venv/askme-light/bin/activate
$ pip install -r requirements.txt
```

Edit the config.py file and set ELASTIC_HOST to the Jetstream internal address of the Elasticsearch instance (from early April 2024):

```python
ELASTIC_HOST = '10.0.142.31'
```

Start FastAPI with the internal IP address (from early April 2024) of the instance where this runs as the host.

```bash
$ uvicorn api:app --reload --host 10.0.142.4
```

And then you can access it from the world with the public IP address of the API instance:

```bash
$ curl 149.165.171.219:8000/api
{"description":"AskMe API","help":"Ping the /api/help endpoint for help"}
```

## Using Docker

First edit the config file as above and set ELASTIC_HOST:

```python
ELASTIC_HOST = '10.0.142.31'
```

Then edit the Dockerfile for the API in `docker/Dockerfile-api` and change the last line:

```docker
CMD ["uvicorn", "api:app", "--host", "0.0.0.0"]
```

Editing the Dockerfile will be made obsolete soon by changing the file in the repository.

Then build the image in two steps

```bash
$ docker build -t askme-base -f docker/Dockerfile-base .
$ docker build -t askme-api -f docker/Dockerfile-api .
```

Finally start the container:

```bash
$ docker run --restart always -d -p 8000:8000 askme-api
```

The --restart option should insure that the container is restarted, including when the instance reboots, see [https://docs.docker.com/config/containers/start-containers-automatically/](https://docs.docker.com/config/containers/start-containers-automatically/) for details. The API is now available on the public IP address of the instance.
