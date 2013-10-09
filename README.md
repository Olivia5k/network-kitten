Kitten
====

Distributed schema based file transfer.

To put it simple, kitten is a peer-to-peer file transfer protocol. It differs from
other similar projects in that it is completely decentralized, has a schema
based grouping of what it considers to be transferable items, and has a high
focus on usability.

It is currently in a pre-alpha state; *Here be dragons*.

## Getting started ##
* Install [virtualenv](http://www.virtualenv.org/en/latest/)
* Clone this repo, cd into it
* Run the following:

```
virtualenv .
source bin/activate
pip install -r dev.requirements.txt
python setup.py develop
```

* Run the tests to verify that it works: `py.test test/`
