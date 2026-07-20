SQL_GENERATION_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "sql": {
            "anyOf": [
                {
                    "type": "string",
                },
                {
                    "type": "null",
                },
            ]
        },
        "explanation": {
            "type": "string",
        },
        "tables_used": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "columns_used": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "confidence": {
            "type": "number",
        },
        "requires_clarification": {
            "type": "boolean",
        },
        "clarification_question": {
            "anyOf": [
                {
                    "type": "string",
                },
                {
                    "type": "null",
                },
            ]
        },
    },
    "required": [
        "sql",
        "explanation",
        "tables_used",
        "columns_used",
        "confidence",
        "requires_clarification",
        "clarification_question",
    ],
    "additionalProperties": False,
}