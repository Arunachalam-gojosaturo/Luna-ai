"""
Parse AI responses to separate explanatory text from code blocks.
"""
import re
from dataclasses import dataclass


@dataclass
class CodeBlock:
    language: str
    code: str
    index: int   # position in original text for ordering


@dataclass
class ParsedResponse:
    full_text: str
    explanation: str        # text only - used for TTS
    code_blocks: list       # list[CodeBlock]
    has_code: bool


def parse_response(text: str) -> ParsedResponse:
    """Split AI response into explanation text and code blocks."""
    code_blocks = []
    idx = 0

    # Match ```lang\ncode``` or ```\ncode```
    pattern = re.compile(r'```(\w*)\n?(.*?)```', re.DOTALL)

    clean_explanation = text

    for m in pattern.finditer(text):
        lang = m.group(1).strip() or "text"
        code = m.group(2).rstrip()
        code_blocks.append(CodeBlock(language=lang, code=code, index=idx))
        idx += 1
        # Remove code block from explanation
        clean_explanation = clean_explanation.replace(m.group(0), f"[Code block {idx}]", 1)

    # Further clean explanation for TTS
    tts_text = pattern.sub("", text)          # remove all code fences
    tts_text = re.sub(r'\[Code block \d+\]', '', tts_text)
    tts_text = re.sub(r'\n{3,}', '\n\n', tts_text)
    tts_text = re.sub(r'`[^`]+`', lambda m: m.group(0).strip('`'), tts_text)  # inline code → plain
    tts_text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', tts_text)              # bold/italic
    tts_text = re.sub(r'#{1,6}\s+', '', tts_text)                              # headers
    tts_text = tts_text.strip()

    # Clean display explanation (keep structure but strip fences)
    display_explanation = pattern.sub('', clean_explanation).strip()

    return ParsedResponse(
        full_text=text,
        explanation=tts_text if tts_text else "Here's the code:",
        code_blocks=code_blocks,
        has_code=len(code_blocks) > 0,
    )


def get_language_label(lang: str) -> str:
    labels = {
        "python": "Python", "py": "Python",
        "javascript": "JavaScript", "js": "JavaScript",
        "typescript": "TypeScript", "ts": "TypeScript",
        "bash": "Bash", "sh": "Shell", "shell": "Shell",
        "html": "HTML", "css": "CSS",
        "json": "JSON", "yaml": "YAML", "yml": "YAML",
        "cpp": "C++", "c": "C", "java": "Java",
        "rust": "Rust", "go": "Go",
        "sql": "SQL", "text": "Text", "": "Code",
    }
    return labels.get(lang.lower(), lang.upper() or "Code")
