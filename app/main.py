import json

import bottle
from bottle import Bottle

from app.auth import register_auth_routes
from app.database import SessionLocal, init_db
from app.docs import register_docs_routes
from app.routes.tickets import register_ticket_routes

app = Bottle()

init_db()

register_auth_routes(app)
register_ticket_routes(app)
register_docs_routes(app)


@app.get("/health")
def health():
    bottle.response.content_type = "application/json"
    return json.dumps({"status": "ok"})


@app.hook("after_request")
def enable_cors():
    bottle.response.headers["Access-Control-Allow-Origin"] = "*"
    bottle.response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    bottle.response.headers["Access-Control-Allow-Headers"] = (
        "Origin, Accept, Content-Type, X-API-Key, X-Admin-Key"
    )


@app.hook("after_request")
def remove_session(*args, **kwargs):
    SessionLocal.remove()


@app.route("/<:re:.*>", method="OPTIONS")
def cors_options(**kwargs):
    return ""


@app.error(400)
def error_400(error):
    bottle.response.content_type = "application/json"
    return json.dumps({"error": "Bad Request", "message": str(error.body)})


@app.error(401)
def error_401(error):
    bottle.response.content_type = "application/json"
    return json.dumps({"error": "Unauthorized", "message": str(error.body)})


@app.error(403)
def error_403(error):
    bottle.response.content_type = "application/json"
    return json.dumps({"error": "Forbidden", "message": str(error.body)})


@app.error(404)
def error_404(error):
    bottle.response.content_type = "application/json"
    return json.dumps({"error": "Not Found", "message": str(error.body)})


@app.error(422)
def error_422(error):
    bottle.response.content_type = "application/json"
    return json.dumps({"error": "Unprocessable Entity", "message": str(error.body)})


@app.error(500)
def error_500(error):
    bottle.response.content_type = "application/json"
    return json.dumps({"error": "Internal Server Error", "message": str(error.body)})


if __name__ == "__main__":
    from app.config import config

    bottle.run(app=app, host="0.0.0.0", port=config.PORT)
