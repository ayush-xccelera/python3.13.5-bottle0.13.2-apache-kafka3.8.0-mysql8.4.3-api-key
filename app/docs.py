import json

import bottle

OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Support Ticket API",
        "description": "Bottle backend for managing support tickets, authenticated via API key.",
        "version": "0.1.0",
    },
    "servers": [{"url": "/api/v1"}],
    "components": {
        "securitySchemes": {
            "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
            "AdminKeyAuth": {"type": "apiKey", "in": "header", "name": "X-Admin-Key"},
        },
        "schemas": {
            "Ticket": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string", "nullable": True},
                    "status": {
                        "type": "string",
                        "enum": ["OPEN", "IN_PROGRESS", "RESOLVED"],
                    },
                    "client_id": {"type": "integer"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"},
                },
            },
            "TicketCreate": {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
            "TicketStatusUpdate": {
                "type": "object",
                "required": ["status"],
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["OPEN", "IN_PROGRESS", "RESOLVED"],
                    }
                },
            },
        },
    },
    "paths": {
        "/tickets": {
            "post": {
                "summary": "Create a ticket",
                "security": [{"ApiKeyAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TicketCreate"}
                        }
                    },
                },
                "responses": {
                    "201": {
                        "description": "Ticket created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Ticket"}
                            }
                        },
                    },
                    "401": {"description": "Missing or invalid API key"},
                    "422": {"description": "Validation error"},
                },
            },
            "get": {
                "summary": "List tickets",
                "security": [{"ApiKeyAuth": []}],
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0}},
                ],
                "responses": {
                    "200": {"description": "Paginated list of tickets"},
                    "401": {"description": "Missing or invalid API key"},
                },
            },
        },
        "/tickets/{id}": {
            "get": {
                "summary": "Retrieve a ticket",
                "security": [{"ApiKeyAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "200": {
                        "description": "Ticket found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Ticket"}
                            }
                        },
                    },
                    "401": {"description": "Missing or invalid API key"},
                    "404": {"description": "Ticket not found"},
                },
            },
            "put": {
                "summary": "Update a ticket",
                "security": [{"ApiKeyAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TicketCreate"}
                        }
                    },
                },
                "responses": {
                    "200": {"description": "Ticket updated"},
                    "401": {"description": "Missing or invalid API key"},
                    "404": {"description": "Ticket not found"},
                    "422": {"description": "Validation error"},
                },
            },
            "delete": {
                "summary": "Delete a ticket",
                "security": [{"ApiKeyAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "204": {"description": "Ticket deleted"},
                    "401": {"description": "Missing or invalid API key"},
                    "404": {"description": "Ticket not found"},
                },
            },
        },
        "/tickets/{id}/status": {
            "patch": {
                "summary": "Change ticket status",
                "security": [{"ApiKeyAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TicketStatusUpdate"}
                        }
                    },
                },
                "responses": {
                    "200": {"description": "Status updated"},
                    "401": {"description": "Missing or invalid API key"},
                    "404": {"description": "Ticket not found"},
                    "422": {"description": "Invalid status or transition"},
                },
            }
        },
        "/api-keys": {
            "post": {
                "summary": "Create an API key (admin only)",
                "security": [{"AdminKeyAuth": []}],
                "responses": {"201": {"description": "API key created"}},
            },
            "get": {
                "summary": "List API keys (admin only)",
                "security": [{"AdminKeyAuth": []}],
                "responses": {"200": {"description": "Paginated list of API keys"}},
            },
        },
        "/api-keys/{id}": {
            "delete": {
                "summary": "Revoke an API key (admin only)",
                "security": [{"AdminKeyAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"description": "API key revoked"}},
            }
        },
    },
}

SWAGGER_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Support Ticket API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {
            SwaggerUIBundle({
                url: "/api/v1/schema",
                dom_id: "#swagger-ui"
            });
        };
    </script>
</body>
</html>
"""


def register_docs_routes(app):
    @app.get("/api/v1/schema")
    def schema():
        bottle.response.content_type = "application/json"
        return json.dumps(OPENAPI_SPEC)

    @app.get("/api/v1/openapi.json")
    def openapi_json():
        bottle.response.content_type = "application/json"
        return json.dumps(OPENAPI_SPEC)

    @app.get("/api/v1/docs")
    def docs():
        bottle.response.content_type = "text/html"
        return SWAGGER_HTML
