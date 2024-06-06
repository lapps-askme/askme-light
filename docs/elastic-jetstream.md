# Elasticsearch and Jetstream

[ <a href="#setup">setup</a>
| <a href="#config">configuration and security</a>
| <a href="#data">data loading</a>
]

Notes on how to use Elastic on our AskMe Jetstream instances.

<a name="setup"></a>

## Setup

We start with a basic recent Ubuntu instance. For the test instance we used the m3.medium flavor, which has 8 CPUs 30 GB of RAM. For our production server we want a few levels up.


### Installation

Instructions from [DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-elasticsearch-on-ubuntu-20-04).

```bash
$ curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
$ echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list
$ sudo apt update
$ sudo apt install elasticsearch
```

During the last step you just hit return if you see a pink screen with options.

Default Elasticsearch directories locations:

| path                           | description          |
| -------------------------------| ---------------------|
| /etc/elasticsearch/            | configuration files  |
| /usr/share/elasticsearch/bin/  | ES binaries          |
| /var/lib/elasticsearch/        | databases            |
| /var/log/elasticsearch         | log files            |


### Attaching a volume

Just do this from Jetstream2. I attached the elastic-test instance to the elastic-data volume, which is available on the instance at `/media/volume/elastic-data`.


### Starting and stopping

Use systemctl to start and stop Elasticsearch:

```bash
$ sudo systemctl start elasticsearch
$ sudo systemctl stop elasticsearch
```

To start it up every time your server boots:

```bash
$ sudo systemctl enable elasticsearch
```



<a name="config"></a>

## Configuration and basic security


### Using the mounted volume

Stop Elastic search and edit the configuration file to change the path to the data.

```yml
#path.data: /var/lib/elasticsearch
path.data: /media/volume/elastic-data
```

You also need to make sure that the database files are owned by the elasticsearch user:

```bash
$ sudo chown -R elasticsearch:elasticsearch /media/volume/elastic-data/nodes
```

Now you can start elasticsearch again. And probably upload the data again.

```
$ curl http://localhost:9200/xdd/_doc/_bulk -H "Content-Type: application/json" -o /dev/null -X POST --data-binary @random-ela-biomedical-0100.json
```


### Setting up minimal security

Let's first do some other basic configuration, like giving the cluster a name, making the host explicit and setting this up as a single node cluster.

```yaml
cluster.name: "docker-cluster"
network.host: 0.0.0.0
discovery.type: single-node
```

Again, we have stopped and started Elasticsearch around making these changes. There is still no security enable since Elasticsearch version 7 has it disabled by default.

```bash
$ curl -X GET "http://localhost:9200/_xpack?pretty"
```

```json
{
	...
    "security" : {
      "available" : true,
      "enabled" : false
    },
    ...
}
```

To set up security we once again first stop Elasticsearch and add the following to the configuration file:

```yaml
xpack.security.enabled: true
```

```bash
$ sudo systemctl start elasticsearch
$ sudo /usr/share/elasticsearch/bin/elasticsearch-setup-passwords auto
```

First you start the database again and then you run a one-time password setup script to generate passwords. Make note of those passwords since the cannot be reset. Current passwords on the instance are saved in `/etc/elasticsearch`.

After this you cannot simply list the indices again, you need a password:

```bash
$ curl -u elastic:<passwd> localhost:9200/_cat/indices
```
```
green  open .geoip_databases lNNrIkUSTjmFOnUopXYLgQ 1 0  34 43 34.6mb 34.6mb
green  open .security-7      wbNKsAXUT5ihTlkfen09-A 1 0   7  0 25.7kb 25.7kb
yellow open read_me          A9RDN5kwR--YLaKfihab4g 1 1   1  0  4.4kb  4.4kb
yellow open xdd              pXsBXfvyTnqQ0yehghE1ag 1 1 699  1 25.3mb 25.3mb
```

Use *elasticsearch-users* to add a new user:

```
$ sudo /usr/share/elasticsearch/bin/elasticsearch-users useradd askme -p pw-askme -r viewer
```

This user is not authorized to see the list of indices, but it is allowed to see the contents of indices that do not start with a dot, which for now is enough for the AskMe interface.

```
curl -u askme:pw-askme localhost:9200/xdd/_search
```

### Outside visibility

Recall that we used "0.0.0.0" as the network host address. This means that the instance is listening on all addresses. Everybody now has access (as long as they have the passwords). At the time of this writing we had two test instances for AskMe:

<table>
<tr>
	<th>instance</th>
	<th>internal IP</th>
	<th>public IP</th>
</tr>
<tr>
	<td>Elastic test</td>
	<td>10.0.142.31</td>
	<td>149.165.171.238</td>
</tr>
<tr>
	<td>marc-test</td>
	<td>10.0.142.173</td>
	<td>149.165.175.231</td>
</tr>
</table>

I can now log into marc-test and use the internal IP address:

```bash
$ ssh marc-test
ubuntu@marc-test:~$ curl -u askme:pw-askme 10.0.142.31:9200/xdd/_count?pretty
{"count":699,"_shards":{"total":1,"successful":1,"skipped":0,"failed":0}}
```

Or use the public address from the outside (which will also work from the local network.

```bash
$ curl -u askme:pw-askme 149.165.171.238:9200/xdd/_count
{"count":699,"_shards":{"total":1,"successful":1,"skipped":0,"failed":0}}
```

The same can actually be achieved by setting the network host as follows:

```yaml
network.host: 10.0.142.31
```

This makes the elastic service avaible at 10.0.142.31 from the internal network, but also at 149.165.171.238 from both the internal network and the outside. I am not sure why that works.

What did not work is

```yml
network.host: 149.165.171.238
```

Which gives an error after restarting:

```
exouser@elastic-test:~/elastic/data$ sudo systemctl start elasticsearch
Job for elasticsearch.service failed because the control process exited with error code.
See "systemctl status elasticsearch.service" and "journalctl -xeu elasticsearch.service" for details.
```


<a name="data"></a>

## Data handling

We have an as of yet unsolved issue with uploading data on a secured instance. So what we do now is stop the instance, disable security and restart.

```yaml
# network.host: 10.0.142.31
# xpack.security.enabled: true
```

We use upload files that contain at most 1000 documents, which keeps us within the 100MB file limit. With security disabled we can upload as follows.

```bash
curl http://localhost:9200/xdd/_doc/_bulk -H "Content-Type: application/json" -X POST --data-binary @elastic-biomedical-001.json > logs/log-biomedical-001.json
curl http://localhost:9200/xdd/_doc/_bulk -H "Content-Type: application/json" -X POST --data-binary @elastic-biomedical-002.json > logs/log-biomedical-002.json
```

A full list of commands is stored on the "Elastic test" instance at `/home/exouser/elastic/data`.
