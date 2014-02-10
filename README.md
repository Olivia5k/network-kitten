# Kitten

**kitten** is a distributed build scheduler.  Think of it as a build agent to
a build system such as Jenkins, but without a central point. All connected
nodes communicate between each other to perform all the tasks traditionally
performed by the central build server.

It is currently in an experimental pre-alpha state; *Here be dragons*.


## Python 3 comatibility

As of this writing, the [gevent][gevent] library does not support Python 3.
gevent is a crucial part in having concurrency to requests.  I tried making
dynamic imports so that Python 2 loaded greenlet powered zmq and Python 3 did
not, but that proved harder than I thought.

So, until gevent [gets actual Python 3 support][38], kitten will not support
Python 3.  This bothers me a lot since I am an active advocate for Python 3,
but a networking library without concurrency is beyond silly.


[gevent]: https://github.com/surfly/gevent
[38]: https://github.com/surfly/gevent/issues/38
