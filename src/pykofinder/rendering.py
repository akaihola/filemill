from markdown_it import MarkdownIt
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.lexers.special import TextLexer

from pykofinder.styles import PYGMENTS_FORMATTER


def highlighter(code: str, lang: str, _attrs: str) -> str:
    try:
        lexer = get_lexer_by_name(lang) if lang else guess_lexer(code)
    except Exception:
        lexer = TextLexer()
    return highlight(code, lexer, PYGMENTS_FORMATTER)


md = MarkdownIt("commonmark", {"highlight": highlighter}).enable(
    ["table", "strikethrough"]
)

try:
    from mdit_py_plugins.front_matter import front_matter_plugin

    front_matter_plugin(md)
except ImportError:
    pass

try:
    from mdit_py_plugins.footnote import footnote_plugin

    footnote_plugin(md)
except ImportError:
    pass

try:
    from mdit_py_plugins.tasklists import tasklists_plugin

    tasklists_plugin(md)
except ImportError:
    pass

try:
    from mdit_py_plugins.anchors import anchors_plugin

    anchors_plugin(md)
except ImportError:
    pass

try:
    from mdit_py_plugins.deflist import deflist_plugin

    deflist_plugin(md)
except ImportError:
    pass

try:
    from mdit_py_plugins.dollarmath import dollarmath_plugin

    dollarmath_plugin(md)
except ImportError:
    pass

try:
    from mdit_py_plugins.admon import admon_plugin

    admon_plugin(md)
except ImportError:
    pass
