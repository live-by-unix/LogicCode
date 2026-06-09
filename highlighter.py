from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor


LANGUAGE_KEYWORDS = {
    'python': [
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
        'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
        'try', 'while', 'with', 'yield',
    ],
    'c': [
        'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
        'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
        'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof',
        'static', 'struct', 'switch', 'typedef', 'union', 'unsigned', 'void',
        'volatile', 'while', 'include', 'define', 'ifdef', 'ifndef', 'endif',
    ],
    'cpp': [
        'auto', 'break', 'case', 'catch', 'char', 'class', 'const', 'constexpr',
        'continue', 'default', 'delete', 'do', 'double', 'else', 'enum',
        'explicit', 'export', 'extern', 'float', 'for', 'friend', 'goto', 'if',
        'inline', 'int', 'long', 'mutable', 'namespace', 'new', 'noexcept',
        'operator', 'override', 'private', 'protected', 'public', 'register',
        'return', 'short', 'signed', 'sizeof', 'static', 'static_cast',
        'struct', 'switch', 'template', 'this', 'throw', 'try', 'typedef',
        'typeid', 'typename', 'union', 'unsigned', 'using', 'virtual', 'void',
        'volatile', 'while', 'include', 'define', 'ifdef', 'ifndef', 'endif',
    ],
    'java': [
        'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch',
        'char', 'class', 'const', 'continue', 'default', 'do', 'double',
        'else', 'enum', 'extends', 'final', 'finally', 'float', 'for', 'goto',
        'if', 'implements', 'import', 'instanceof', 'int', 'interface', 'long',
        'native', 'new', 'package', 'private', 'protected', 'public', 'return',
        'short', 'static', 'strictfp', 'super', 'switch', 'synchronized',
        'this', 'throw', 'throws', 'transient', 'try', 'void', 'volatile',
        'while', 'true', 'false', 'null',
    ],
    'csharp': [
        'abstract', 'as', 'base', 'bool', 'break', 'byte', 'case', 'catch',
        'char', 'checked', 'class', 'const', 'continue', 'decimal', 'default',
        'delegate', 'do', 'double', 'else', 'enum', 'event', 'explicit',
        'extern', 'false', 'finally', 'fixed', 'float', 'for', 'foreach',
        'goto', 'if', 'implicit', 'in', 'int', 'interface', 'internal', 'is',
        'lock', 'long', 'namespace', 'new', 'null', 'object', 'operator',
        'out', 'override', 'params', 'private', 'protected', 'public',
        'readonly', 'ref', 'return', 'sbyte', 'sealed', 'short', 'sizeof',
        'stackalloc', 'static', 'string', 'struct', 'switch', 'this', 'throw',
        'true', 'try', 'typeof', 'uint', 'ulong', 'unchecked', 'unsafe',
        'ushort', 'using', 'virtual', 'void', 'volatile', 'while',
    ],
    'fortran': [
        'program', 'end', 'function', 'subroutine', 'module', 'interface',
        'implicit', 'none', 'integer', 'real', 'double', 'precision',
        'complex', 'character', 'logical', 'dimension', 'allocatable',
        'pointer', 'target', 'parameter', 'save', 'intent', 'optional',
        'public', 'private', 'contains', 'use', 'call', 'return',
        'if', 'then', 'else', 'elseif', 'endif', 'do', 'enddo',
        'while', 'select', 'case', 'endselect', 'stop', 'continue',
        'format', 'write', 'read', 'print', 'open', 'close',
        'allocate', 'deallocate', 'nullify', 'cycle', 'exit',
    ],
}

BUILTIN_TYPES = {
    'python': ['int', 'float', 'str', 'list', 'dict', 'tuple', 'set', 'bool',
               'bytes', 'bytearray', 'range', 'map', 'filter', 'type', 'object',
               'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
               'StopIteration', 'RuntimeError', 'OSError', 'FileNotFoundError',
               'print', 'len', 'range', 'enumerate', 'zip', 'sorted', 'reversed',
               'open', 'input', 'isinstance', 'hasattr', 'getattr', 'setattr',
               'abs', 'all', 'any', 'bin', 'chr', 'dir', 'divmod', 'eval',
               'exec', 'format', 'globals', 'hex', 'id', 'iter', 'locals',
               'max', 'min', 'next', 'oct', 'ord', 'pow', 'repr', 'round',
               'str', 'sum', 'super', 'vars', 'classmethod', 'staticmethod',
               'property', '__init__', '__str__', '__repr__', '__call__',
               '__getitem__', '__setitem__', '__len__', '__iter__',
               '__next__', '__enter__', '__exit__',
               ],
    'c': ['size_t', 'FILE', 'NULL', 'printf', 'scanf', 'fprintf', 'fscanf',
          'malloc', 'calloc', 'realloc', 'free', 'fopen', 'fclose', 'fread',
          'fwrite', 'fseek', 'ftell', 'rewind', 'fgets', 'fputs', 'fgetc',
          'fputc', 'sprintf', 'sscanf', 'strlen', 'strcpy', 'strcmp',
          'strcat', 'strchr', 'strstr', 'memcpy', 'memmove', 'memset',
          'memcmp', 'atoi', 'atof', 'atol', 'exit', 'rand', 'srand',
          'sqrt', 'pow', 'sin', 'cos', 'tan', 'abs', 'ceil', 'floor',
          ],
    'cpp': ['std', 'cout', 'cin', 'cerr', 'clog', 'endl', 'string',
            'vector', 'map', 'set', 'list', 'deque', 'queue', 'stack',
            'pair', 'tuple', 'array', 'shared_ptr', 'unique_ptr',
            'make_shared', 'make_unique', 'iterator', 'begin', 'end',
            'find', 'sort', 'reverse', 'count', 'size', 'empty',
            'push_back', 'pop_back', 'front', 'back', 'insert', 'erase',
            'new', 'delete', 'nullptr', 'true', 'false', 'bool',
            'dynamic_cast', 'static_cast', 'reinterpret_cast', 'const_cast',
            'printf', 'scanf', 'malloc', 'free', 'NULL', 'size_t',
            ],
    'java': ['String', 'Integer', 'Double', 'Float', 'Boolean', 'Long',
             'Short', 'Byte', 'Character', 'Object', 'Class', 'System',
             'Math', 'Arrays', 'List', 'ArrayList', 'Map', 'HashMap',
             'Set', 'HashSet', 'Queue', 'LinkedList', 'Stack',
             'Iterator', 'Comparator', 'Collections', 'Exception',
             'RuntimeException', 'IOException', 'NullPointerException',
             'ArrayIndexOutOfBoundsException', 'Thread', 'Runnable',
             'Serializable', 'Comparable', 'Override', 'Deprecated',
             'SuppressWarnings', 'out', 'in', 'println', 'print',
             ],
    'csharp': ['string', 'int', 'double', 'float', 'bool', 'char', 'byte',
               'long', 'short', 'uint', 'ulong', 'decimal', 'object',
               'var', 'dynamic', 'null', 'true', 'false', 'void',
               'Console', 'WriteLine', 'Write', 'ReadLine', 'Read',
               'String', 'Int32', 'Int64', 'Double', 'Single',
               'Boolean', 'Byte', 'Char', 'Decimal',
               'List', 'Dictionary', 'HashSet', 'Queue', 'Stack',
               'IEnumerable', 'IEnumerator', 'IDisposable',
               'Exception', 'ArgumentException', 'ArgumentNullException',
               'InvalidOperationException', 'IOException',
               'Task', 'async', 'await', 'var', 'nameof',
               ],
    'fortran': ['.true.', '.false.', '.eq.', '.ne.', '.lt.', '.le.',
                '.gt.', '.ge.', '.and.', '.or.', '.not.', '.eqv.',
                '.neqv.', 'kind', 'selected_int_kind', 'selected_real_kind',
                'precision', 'epsilon', 'huge', 'tiny',
                ],
}


def _make_format(color, bold=False, italic=False):
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(color))
    if bold:
        fmt.setFontWeight(QFont.Weight.Bold)
    if italic:
        fmt.setFontItalic(True)
    return fmt


class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, is_dark=True):
        super().__init__(parent)
        self.is_dark = is_dark
        self._language = 'python'
        self._rules = []
        self._build_rules()

    def set_theme(self, is_dark):
        if self.is_dark != is_dark:
            self.is_dark = is_dark
            self._build_rules()
            self.rehighlight()

    def set_language(self, language):
        if self._language != language:
            self._language = language
            self._build_rules()
            self.rehighlight()

    @property
    def _colors(self):
        if self.is_dark:
            return {
                'keyword': '#569cd6',
                'string': '#ce9178',
                'comment': '#6a9955',
                'number': '#b5cea8',
                'function': '#dcdcaa',
                'type': '#4ec9b0',
                'decorator': '#c586c0',
            }
        else:
            return {
                'keyword': '#0000ff',
                'string': '#a31515',
                'comment': '#008000',
                'number': '#098658',
                'function': '#795e26',
                'type': '#267f99',
                'decorator': '#af00db',
            }

    def _build_rules(self):
        self._rules = []
        c = self._colors

        lang = self._language

        keywords = LANGUAGE_KEYWORDS.get(lang, [])
        builtins = BUILTIN_TYPES.get(lang, [])

        kw_fmt = _make_format(c['keyword'], bold=True)
        for kw in keywords:
            pattern = QRegularExpression(
                rf'\b{kw}\b'
            )
            self._rules.append((pattern, kw_fmt))

        type_fmt = _make_format(c['type'], bold=True)
        for bt in builtins:
            pattern = QRegularExpression(rf'\b{bt}\b')
            self._rules.append((pattern, type_fmt))

        fn_fmt = _make_format(c['function'])
        self._rules.append((
            QRegularExpression(r'\b[A-Za-z_]\w*(?=\s*\()'),
            fn_fmt
        ))

        decorator_fmt = _make_format(c['decorator'])
        self._rules.append((
            QRegularExpression(r'@\w+'),
            decorator_fmt
        ))

        str_fmt = _make_format(c['string'])
        self._rules.append((
            QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'),
            str_fmt
        ))
        self._rules.append((
            QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"),
            str_fmt
        ))
        self._rules.append((
            QRegularExpression(r'f"[^"\\]*(\\.[^"\\]*)*"'),
            str_fmt
        ))
        self._rules.append((
            QRegularExpression(r"f'[^'\\]*(\\.[^'\\]*)*'"),
            str_fmt
        ))
        self._rules.append((
            QRegularExpression(r'[rbRB][bB]?"[^"\\]*(\\.[^"\\]*)*"'),
            str_fmt
        ))
        self._rules.append((
            QRegularExpression(r"[rbRB][bB]?'[^'\\]*(\\.[^'\\]*)*'"),
            str_fmt
        ))

        num_fmt = _make_format(c['number'])
        self._rules.append((
            QRegularExpression(r'\b[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?[fFL]?\b'),
            num_fmt
        ))
        self._rules.append((
            QRegularExpression(r'\b[0-9]+[eE][+-]?[0-9]+[fFL]?\b'),
            num_fmt
        ))
        self._rules.append((
            QRegularExpression(r'\b0[xX][0-9a-fA-F]+\b'),
            num_fmt
        ))

        if lang == 'fortran':
            self._rules.append((
                QRegularExpression(r'\b[0-9]+(\.[0-9]*)?[dD][+-]?[0-9]+\b'),
                num_fmt
            ))

        if lang != 'fortran':
            self._rules.append((
                QRegularExpression(r'\b[0-9]+[uUlL]*\b'),
                num_fmt
            ))
        else:
            self._rules.append((
                QRegularExpression(r'\b[0-9]+(_[0-9]+)*\b'),
                num_fmt
            ))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, fmt)

        self._highlight_comments(text)

    def _highlight_comments(self, text):
        c = self._colors
        cmt_fmt = _make_format(c['comment'], italic=True)

        lang = self._language

        if lang == 'python':
            idx = text.find('#')
            if idx >= 0:
                self.setFormat(idx, len(text) - idx, cmt_fmt)
            td = text.find('"""')
            if td >= 0:
                self.setFormat(td, len(text) - td, cmt_fmt)

        elif lang == 'fortran':
            if text and text.strip():
                first = text.strip()[0]
                if first in ('!', 'c', 'C', '*'):
                    self.setFormat(0, len(text), cmt_fmt)

        else:
            idx = text.find('//')
            if idx >= 0:
                self.setFormat(idx, len(text) - idx, cmt_fmt)
