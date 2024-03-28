# Elastic Install on Jetstream


Installation:

Instructions from [DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-elasticsearch-on-ubuntu-20-04).

```bash
$ curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
$ echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list
$ sudo apt update
$ sudo apt install elasticsearch
```

During the last step you just hit return if you see a pink screen with options.


# Attaching a volume

Just do this from Jetstream2. I attached the elastic-test instance to the elastic-data volume, which is available on the instance at `/media/volume/elastic-data`.


# Configuration and basic security

To be written


