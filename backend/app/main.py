from fastapi import FastAPI

app = FastAPI(
    title="SafeQuery AI",
    description=(
        "Secure natural-language-to-SQL analytics platform with "
        "guardrails and hallucination detection."
    ),
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return the current health status of the API."""
    return {
        "status": "healthy",
        "project": "SafeQuery AI",
    }