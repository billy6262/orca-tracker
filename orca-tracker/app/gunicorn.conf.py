import multiprocessing

# Bind and concurrency
bind = "0.0.0.0:8000"
workers = (multiprocessing.cpu_count() * 2) + 1
threads = 2
worker_class = "gthread"
timeout = 120

# Logging to stdout/stderr (Docker-friendly)
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Safe preload
preload_app = True