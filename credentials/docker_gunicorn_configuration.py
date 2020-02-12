timeout = 300
bind = "127.0.0.1:8150"
workers = 2
worker_class = "gevent"


def pre_request(worker, req):
    worker.log.info("%s %s" % (req.method, req.path))
