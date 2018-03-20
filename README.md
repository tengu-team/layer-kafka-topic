# Overview

This charm represents a Kafka topic to be created.

## Usage
```
juju deploy kafka
juju deploy ./kafka-topic 
juju add-relation kafka kafka-topic
juju config kafka-topic partitions=25
juju config kafka-topic replication=3
juju config kafka-topic topic-name=data
```
## Caveats
- This charm will try to create the topic once all needed config values are set (name, partitions and replication). If you need a compact topic, set the value before other configs.
- Alterations to the config values will have no effect after the topic has been initially created.

## Authors

This software was created in the [IBCN research group](https://www.ibcn.intec.ugent.be/) of [Ghent University](https://www.ugent.be/en) in Belgium. This software is used in [Tengu](https://tengu.io), a project that aims to make experimenting with data frameworks and tools as easy as possible.

 - Sander Borny <sander.borny@ugent.be>
