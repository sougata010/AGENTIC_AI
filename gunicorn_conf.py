import multiprocessing

# Gunicorn configuration file
# See: https://docs.gunicorn.org/en/stable/configure.html

# Worker Options
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 4 # Fixed for stability in smaller containers
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging Options
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Binding Options
bind = "0.0.0.0:8000"

# Process Naming
proc_name = "agentic_ai"

# Restart workers periodically to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50
