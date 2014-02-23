# Kitten

**kitten** is a lightweight distributed clustering scheduler with a focus on
extendability via plugins. It was first imagined as a distributed build system,
but the networking part took over and the build system will later be
implemented as a plugin.

It is currently in an experimental alpha state; *dragons be reside here*.


## Python 3 compatibility

As of this writing, the [gevent][gevent] library does not support Python 3.
gevent is a crucial part in having concurrency to requests.  I tried making
dynamic imports so that Python 2 loaded greenlet powered zmq and Python 3 did
not, but that proved harder than I thought.

So, until gevent [gets actual Python 3 support][38], kitten will not support
Python 3.  This bothers me a lot since I am an active advocate for Python 3,
but a networking library without concurrency is beyond silly.


[gevent]: https://github.com/surfly/gevent
[38]: https://github.com/surfly/gevent/issues/38
