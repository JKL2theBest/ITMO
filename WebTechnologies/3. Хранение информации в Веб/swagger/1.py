from flask import Flask, jsonify

app = Flask(__name__)

# Пример Swagger спецификации (замените на вашу спецификацию)
swagger_spec = {
    "components": {
        "schemas": {
            "Student": {
                "properties": {
                    "course": {"title": "Course", "type": "string"},
                    "group": {"title": "Group", "type": "string"},
                    "isuid": {"title": "Isuid", "type": "integer"},
                    "name": {"title": "Name", "type": "string"},
                },
                "required": ["group", "course", "name", "isuid"],
                "title": "Student",
                "type": "object",
            },
            "ValidationErrorModel": {
                "properties": {
                    "ctx": {
                        "anyOf": [{"type": "object"}, {"type": "null"}],
                        "default": None,  # Исправлено с null на None
                        "description": "an optional object which contains values required to render the error message.",
                        "title": "Error context",
                    },
                    "loc": {
                        "anyOf": [
                            {"items": {"type": "string"}, "type": "array"},
                            {"type": "null"},
                        ],
                        "default": None,  # Исправлено с null на None
                        "description": "the error's location as a list. ",
                        "title": "Location",
                    },
                    "msg": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": None,  # Исправлено с null на None
                        "description": "a computer-readable identifier of the error type.",
                        "title": "Message",
                    },
                    "type_": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": None,  # Исправлено с null на None
                        "description": "a human readable explanation of the error.",
                        "title": "Error Type",
                    },
                },
                "title": "ValidationErrorModel",
                "type": "object",
            },
        },
        "securitySchemes": None,  # Исправлено с null на None
    },
    "info": {"title": "student API", "version": "1.0.0"},
    "openapi": "3.1.0",
    "paths": {
        "/students": {
            "get": {
                "description": "to get all students",
                "operationId": "get_book_students_get",
                "parameters": [
                    {
                        "in": "query",
                        "name": "course",
                        "required": True,
                        "schema": {"title": "Course", "type": "string"},
                    }
                ],
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Student"}
                            }
                        },
                        "description": "OK",
                    },
                    "422": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "items": {
                                        "$ref": "#/components/schemas/ValidationErrorModel"
                                    },
                                    "type": "array",
                                }
                            }
                        },
                        "description": "Unprocessable Entity",
                    },
                },
                "summary": "get all students",
                "tags": ["default"],
            }
        }
    },
}


@app.route("/swagger.json")
def swagger_json():
    return jsonify(swagger_spec)


if __name__ == "__main__":
    # Слушаем порт 11000 на VPN-интерфейсе
    app.run(host="0.0.0.0", port=11000)
