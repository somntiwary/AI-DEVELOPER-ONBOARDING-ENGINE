# pyright: reportMissingImports=false
import os
from functools import lru_cache
from typing import Optional, Tuple, TYPE_CHECKING, Any
import ast

try:
    from tree_sitter import Language, Parser  # type: ignore
except Exception:  # pragma: no cover
    Language = None  # type: ignore
    Parser = None  # type: ignore

if TYPE_CHECKING:
    from tree_sitter import Language as TLanguage, Parser as TParser  # pragma: no cover
else:  # Fallback types for editors/type-checkers when runtime import is unavailable
    TLanguage = Any  # type: ignore
    TParser = Any  # type: ignore


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(BASE_DIR, "build")
os.makedirs(BUILD_DIR, exist_ok=True)

LIB_FILENAME = "my-languages.dll" if os.name == "nt" else "my-languages.so"
LIB_PATH = os.path.join(BUILD_DIR, LIB_FILENAME)


@lru_cache(maxsize=1)
def get_language() -> Optional[TLanguage]:
    if Language is None:
        return None
    if not os.path.exists(LIB_PATH):
        return None
    try:
        # Newer API (>=0.25)
        if hasattr(Language, "load"):
            return Language.load(LIB_PATH)  # type: ignore[attr-defined]
        # Older API (<0.25): constructor with (lib_path, lang_name)
        return Language(LIB_PATH, "python")  # type: ignore[call-arg]
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_parser() -> Optional[TParser]:
    if Parser is None:
        return None
    language = get_language()
    if language is None:
        return None
    try:
        parser = Parser()
        parser.set_language(language)
        return parser
    except Exception:
        return None


def parse_python_file(path: str) -> Tuple[str, Optional[object]]:
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    parser = get_parser()
    if parser is None:
        return code, None
    tree = parser.parse(code.encode("utf-8"))
    return code, tree


def parse_python_ast(path: str) -> Tuple[str, ast.AST]:
    """Parse using Python's built-in ast as a universal fallback."""
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    try:
        node = ast.parse(code)
    except SyntaxError:
        # Best-effort: return empty Module when code has syntax errors
        node = ast.parse("")
    return code, node


def parse_python_file_safe(path: str) -> Tuple[str, object, str]:
    """Resilient parser that prefers Tree-sitter and falls back to Python ast.

    Returns: (code, tree_or_ast, engine), where engine in {"tree_sitter", "python_ast"}
    """
    code, ts_tree = parse_python_file(path)
    if ts_tree is not None:
        return code, ts_tree, "tree_sitter"
    code, py_ast = parse_python_ast(path)
    return code, py_ast, "python_ast"
