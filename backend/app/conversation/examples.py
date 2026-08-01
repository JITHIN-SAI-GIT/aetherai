"""
Few-shot style examples injected into persona context hints.
These are formatting hints, not actual prompts — no LLM call is made.
"""

STYLE_EXAMPLES: dict = {
    "coding": (
        "Respond with a clear explanation followed by a clean code block. "
        "Use syntax highlighting with the correct language tag. "
        "Explain each significant part briefly after the code."
    ),
    "math": (
        "Show working step-by-step. Use LaTeX notation where helpful. "
        "State the final answer clearly on its own line."
    ),
    "creative": (
        "Write in a flowing, engaging style. Avoid bullet points. "
        "Use vivid language and maintain a consistent tone throughout."
    ),
    "research": (
        "Organise by headings. Cite key facts. Use bullet points sparingly. "
        "Conclude with a concise summary paragraph."
    ),
    "explanation": (
        "Start with the core concept in one sentence. Build up with examples. "
        "Use analogies where helpful. End with a brief summary."
    ),
    "translation": (
        "Provide the translated text first, then a brief note on "
        "any idiomatic differences if relevant."
    ),
    "business": (
        "Use professional, concise language. Lead with the key point. "
        "Use bullet points for lists of items. Avoid jargon."
    ),
    "general": (
        "Be clear, friendly, and direct. Match the user's level of formality."
    ),
}
