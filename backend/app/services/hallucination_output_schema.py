BACK_TRANSLATION_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "question_answered": {
            "type": "string",
        },
        "operation": {
            "type": "string",
        },
        "metrics": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "dimensions": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "filters": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "grouping": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "ordering": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "limit": {
            "anyOf": [
                {
                    "type": "integer",
                },
                {
                    "type": "null",
                },
            ]
        },
    },
    "required": [
        "question_answered",
        "operation",
        "metrics",
        "dimensions",
        "filters",
        "grouping",
        "ordering",
        "limit",
    ],
    "additionalProperties": False,
}


ALIGNMENT_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "score": {
            "type": "number",
        },
        "verdict": {
            "type": "string",
            "enum": [
                "aligned",
                "partially_aligned",
                "misaligned",
            ],
        },
        "matched_requirements": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "missing_requirements": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "extra_assumptions": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "explanation": {
            "type": "string",
        },
    },
    "required": [
        "score",
        "verdict",
        "matched_requirements",
        "missing_requirements",
        "extra_assumptions",
        "explanation",
    ],
    "additionalProperties": False,
}