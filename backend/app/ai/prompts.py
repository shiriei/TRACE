"""TRACE AI System Prompts and Structured Output Schemas."""
from typing import Any, Dict, List

TRACE_SYSTEM_PROMPT = """You are TRACE's local observation interpreter.

TRACE helps people notice and remember the world around them.

Your job is to interpret a user's observation and classify it into exactly one of five TRACE categories:
- Nature: Living, growing, changing, or naturally occurring things (plants, moss, birds, insects, natural patterns).
- Sound: Acoustic discoveries noticed primarily through hearing (bird calls, echoes, water, machinery, rhythms).
- Structure: Human-made objects, architecture, engineered elements, or road patterns (walls, bridges, drains, pipes, buildings).
- Mystery: Strange, unexplained, unexpected, or out-of-place clues worth investigating.
- Personal: Emotionally or autobiographically meaningful moments, memories, or objects.

Rules:
1. Do not invent observations that the user did not provide.
2. Create a concise human-friendly title (3 to 8 words).
3. Write a short summary (1 or 2 concise sentences describing what was noticed).
4. Extract 2 to 5 specific, useful lowercase tags.
5. Identify the dominant sensory type: "visual", "auditory", "environmental", "textual", "personal", or "mixed".
6. Assign a confidence score from 0.0 to 1.0 reflecting how clearly the observation maps to the category.
7. Return ONLY a valid JSON object matching the requested schema. Do not write greetings, markdown fluff, or generic chatbot replies.
"""

# OpenAI-compatible Structured Outputs JSON Schema for LM Studio
TRACE_AI_JSON_SCHEMA: Dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "trace_ai_result",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["Nature", "Sound", "Structure", "Mystery", "Personal"],
                    "description": "One of the five canonical TRACE categories.",
                },
                "title": {
                    "type": "string",
                    "description": "Short human-friendly title.",
                },
                "summary": {
                    "type": "string",
                    "description": "One or two concise sentences describing what was noticed.",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Small list of useful tags.",
                },
                "sensory_type": {
                    "type": "string",
                    "enum": ["visual", "auditory", "environmental", "textual", "personal", "mixed"],
                    "description": "Dominant sensory modality.",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence score between 0.0 and 1.0.",
                },
            },
            "required": ["category", "title", "summary", "tags", "sensory_type", "confidence"],
            "additionalProperties": False,
        },
    },
}


def build_interpretation_messages(observation: str) -> List[Dict[str, str]]:
    """Construct messages payload for chat completion."""
    return [
        {"role": "system", "content": TRACE_SYSTEM_PROMPT},
        {"role": "user", "content": f"Observation to interpret: {observation}"},
    ]
