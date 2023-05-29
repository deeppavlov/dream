from flask import request, Response
from prometheus_client import generate_latest, Counter, Histogram, Gauge, CONTENT_TYPE_LATEST
import time

REQUEST_COUNT = Counter(
    "http_request_count",
    "App Request Count",
    [
        "method",
        "endpoint",
        "code",
    ],
)

REQUEST_LATENCY = Histogram("http_request_latency_seconds", "Request latency", ["endpoint"])

REQUEST_IN_PROGRESS = Gauge(
    "http_request_in_progress",
    "Requests in progress",
    [
        "endpoint",
    ],
)


def do_not_track(func):
    func._do_not_track = True
    return func


def setup_metrics(app):
    # readiness endpoint
    @app.route("/ready", methods=["GET"])
    @do_not_track
    def ready():
        return Response("OK")

    # liveness endpoint
    @app.route("/health", methods=["GET"])
    @do_not_track
    def health():
        return Response("OK")

    # metrics endpoint
    @app.route("/metrics", methods=["GET"])
    @do_not_track
    def metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    def ignore_endpoint():
        view_func = app.view_functions.get(request.endpoint)
        return hasattr(view_func, "_do_not_track")

    def before_request():
        if ignore_endpoint():
            return
        request.start_time = time.time()
        REQUEST_IN_PROGRESS.labels(request.path).inc()

    def after_request(response):
        if ignore_endpoint():
            return response
        resp_time = time.time() - request.start_time
        REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.path).observe(resp_time)
        REQUEST_IN_PROGRESS.labels(request.path).dec()
        return response

    app.before_request(before_request)
    app.after_request(after_request)
