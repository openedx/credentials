"""
gunicorn configuration file: http://docs.gunicorn.org/en/develop/configure.html
Ansible managed
"""

timeout = 300
bind = "127.0.0.1:8150"
pythonpath = "/edx/app/credentials/credentials"
workers = 2
worker_class = "gevent"

limit_request_field_size = 16384


def pre_request(worker, req):
    worker.log.info("%s %s" % (req.method, req.path))
