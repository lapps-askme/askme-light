# ElasticSearch Security Notes

Take the config file in `/usr/share/elasticsearch/config/elasticsearch.yml` (the last two lines were added by the Dockerfile):

```
cluster.name: "docker-cluster"
network.host: 0.0.0.0
path.data: /data
discovery.type: single-node
```

No security is set up here and in ElasticSearch 7 security is not turned on out-of-the-box, and when checking the security settings you will see that security is indeed not enabled:

```
$ curl -X GET -u username:password "http://localhost:9200/_xpack?pretty"
...
    "security" : {
      "available" : true,
      "enabled" : false
    },
...
```


For minimal security the following should be added to the config file:

```
xpack.security.enabled: true
```

After you have rebuild the image and started a new container you cannot connect anymore:

```
$ docker build -t elastic:secure -f Dockerfile-elastic-secure .
$ docker run -d --rm -p 9200:9200 \
    -v /Users/Shared/data/elasticsearch/data/:/data \
    --user elasticsearch elastic:secure
$ curl localhost:9200/_cat/indices
```

```json
{
  "error": {
    "root_cause": [
      {
        "type": "security_exception",
        "reason": "missing authentication credentials for REST request [/_cat/indices]",
        "header": {"WWW-Authenticate": "Basic realm=\"security\" charset=\"UTF-8\""}
      }
    ],
    "type": "security_exception",
    "reason": "missing authentication credentials for REST request [/_cat/indices]",
    "header": {"WWW-Authenticate": "Basic realm=\"security\" charset=\"UTF-8\""}
  },
  "status": 401
}
```

You can docker-exec into the container and set up the passwords of build-in users:

```
$ docker exec -it <container-name> bash
elasticsearch@365510585b92:~$ bin/elasticsearch-setup-passwords auto
```

Randomly generated passwords, including for the elastic user, will be printed to the terminal. Make note of them and save them, otherwise you cannot work as the elastic user if needed.

Under the hood this uses a bootstrapped password for the elastic user, you should only use this once at initial setup and when you run the command again it will fail, see [setup-passwords.html](https://www.elastic.co/guide/en/elasticsearch/reference/7.17/setup-passwords.html) in the reference of version 7.17. Also note that you need to run this after ElasticSearch was started for the first time, since it needs access to a keystore which is not generated until ElasticSearch is first started.

Now you can connect:

```
$ curl -u elastic:<password> localhost:9200/_cat/indices
green  open .geoip_databases fhDJzpC5RlKXsnCKulERRA 1 0   39 0  37.8mb  37.8mb
green  open .security-7      HJSbKR9CTGCVswvQlvAoVg 1 0    7 0  25.1kb  25.1kb
yellow open xdd              XfRpnoc9S5ukusYHE1R7lQ 1 1 2999 1 135.8mb 135.8mb
```

Note the extra index.

Use *elasticsearch-users* to add a new user:

```
bin/elasticsearch-users useradd askme -p pw-askme -r viewer
```

This user is not authorized to see the list of indices, but it is allowed to see the contents of indices that do not start with a dot, which for now is enough for the AskMe interface.

```
curl -u askme:pw-askme localhost:9200/xdd/_search
```

See [https://www.elastic.co/guide/en/elasticsearch/reference/7.17/users-command.html](https://www.elastic.co/guide/en/elasticsearch/reference/7.17/users-command.html) for details. You can also use it to reset passwords or add roles. Sometimes you see mentions of  *elasticsearch-reset-password*, but that is version 8 only.

In Dockerfile-elastic-secure there is a line that creates an askme user. But note that built-in users have no passwords set up, that needs to be done by hand in case you want to delete indices or do something else that requires more than viewer priviliges.

See [https://www.elastic.co/guide/en/elasticsearch/reference/current/built-in-roles.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/built-in-roles.html) for a list of built-in roles.

Also see:

- [https://www.elastic.co/guide/en/elasticsearch/reference/7.16/configuring-stack-security.html](https://www.elastic.co/guide/en/elasticsearch/reference/7.16/configuring-stack-security.html)
- [https://www.elastic.co/guide/en/elasticsearch/reference/7.16/security-minimal-setup.html](https://www.elastic.co/guide/en/elasticsearch/reference/7.16/security-minimal-setup.html)
- [https://www.elastic.co/guide/en/elasticsearch/reference/current/security-privileges.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/security-privileges.html)
- [https://www.elastic.co/guide/en/elasticsearch/reference/current/document-level-security.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/document-level-security.html)
- [https://www.elastic.co/guide/en/elasticsearch/reference/current/field-and-document-access-control.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/field-and-document-access-control.html)

