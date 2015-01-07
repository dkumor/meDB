meDB
======

A database for holding IoT data, as well as automatic analysis engine and action dispatch.


The Basics
-------------------

The database wraps zookeeper, kafka and MongoDB. You will need to download the jar files for zookeeper and kafka from the kafka website.
Currently, only kafka 0.81 is supported, since python-kafka doesn't work with 0.82.

Download kafka 0.81 from [here](http://kafka.apache.org/downloads.html).

Create ```bin/jar``` in the root of this repository, and put all jar files from kafka (```/libs```) inside it.

You will also need:

- Java
- mongoDB
- LUKS

Lastly, the following python2 libraries are needed:

- python2-pymongo
- python2-kafka
- python2-subprocess32

Finally, edit the ```setup.cfg``` file to suit your needs, and run the database by calling:

```bash
sudo python connector.py -c setup.cfg
```

```runconnector``` is a quick bash script that does just that.

Those commands run the 'connector' server. It is the core of meDB. Currently, it is also the only thing that really is fully functioning.

How it Works
-------------------------

Currently, only the connector server is finished, so that's what is going to be explained.

There are three independent servers running here. Zookeeper, Kafka, and MongoDB. Unfortunately, Zookeeper and Kafka don't yet support SSL, and as such the connector server and all things which connect directly to it must be entirely contained on one computer. IoT and quantified self objects don't connect to the connector server directly, but to a special data-server (not yet written) which checks for credentials. Thus the one computer limitation is only for the algorithms which have "admin" priviledges to all databases.

The connector server is entirely contained inside a LUKS file container. This is an encrypted file system, very much like a TrueCrypt file container. LUKS requires mount priviledges on the host computer, so the connector server requires sudo access. Permissions are immediately dropped to the 'connector' user after decrypting the database.

The individual databases each have their own directories in the encrypted container, which include automatically generated configuration files and folders for databases themselves.


Why this way?
--------------------

Kafka is made for taking in a firehose of data - it can handle thousands of asynchronous datapoints per second. Many of these datapoints (such as video/microphone feeds) cannot be saved in a database due to size constraints. The goal is therefore to only "memorize" inputs explicitly marked as "saved", and use Machine Learning to create models of the live stream of all other inputs, such that a general sparse and compressed representation can be saved, and certain general events can be recognized (ie, rather than memorizing pixels of a video feed, memorizing only that there is a person in the room). Kafka has a fixed size database, which is cleared of data older than a specified time, and all Machine Learning models, as well as datapoints marked as "save", and automatically compressed representations are held in MongoDB. Zookeeper is used as a general synchronization between the multiple independent applications (and allows expansion to multiple machines once SSL is available for Zookeeper and Kafka)

TODO
---------------------

- Create specific users for the database, such that each item can only write its own inputs
- Enforce registration of inputs (ie, if a temp sensor registers as a float, enforce that it is a float!)
- Data-gathering server. This is the server to which sensors actually connect over SSL. They give their usernames and user keys, as well as the data they would like to write... OR, they connect as inputs, and wait for inputs (example is lamp waiting for ON/OFF command)
- Kafka-MongoDB interface. The program which will write "saved" inputs from kafka to mongoDB in chunks.
- The Machine Learning!!! This is the fun part. It includes textual analysis (NLP) for text inputs, such as journal entries or visited websites, as well as statistical ML for numerical inputs.
