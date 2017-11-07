"""This module implements data tag match."""

import re


class MatchPattern(object):
    """MatchPattern class."""

    def create(self, ptrn):
        """Create object.

        Args:
            ptrn (str): Glob pattern.
        """
        if ptrn == '**':
            return AllMatchPattern()
        else:
            return GlobMatchPattern(ptrn)


class AllMatchPattern(MatchPattern):
    """AllMatchPattern class."""

    def __init__(self, arg):
        """init."""
        super(AllMatchPattern, self).__init__()
        self.arg = arg

    def __repr__(self):
        """Canonical string representation."""
        return "<AllMatchPattern arg '{}'>".format(self.arg)


class GlobMatchPattern(MatchPattern):
    """GlobMatchPattern class."""

    def __init__(self, pat):
        """init.

        Args:
            pat (str): Glob pattern.
        """
        self.pat = pat
        stack = []
        regex = ['']
        escape = False
        dot = False

        i = 0
        while i < len(pat):
            c = pat[i: i + 1]

            if escape:
                regex[-1] += re.escape(c)
                escape = False
                i += 1
                continue
            elif pat[i: i + 2] == "**":
                # recursive any
                if dot:
                    regex[-1] += "(?![^\\.])"
                    dot = False
                if pat[i + 2: i + 3] == ".":
                    regex[-1] += "(?:.*\\.|\\A)"
                    i += 3
                else:
                    regex[-1] += ".*"
                    i += 2
                continue
            elif dot:
                regex[-1] += "\\."
                dot = False

            if c == "\\":
                escape = True
            elif c == ".":
                dot = True
            elif c == "*":
                # any
                regex[-1] += "[^\\.]*"
            elif c == "{":
                # or
                stack.append([])
                regex.append('')
            elif c == "}" and stack:
                stack[-1] += regex.pop()
                regex[-1] += "({})".format('|'.join(stack.pop()))
            elif c == "," and stack:
                stack[-1].append(regex.pop())
                regex.append('')
            elif re.search(r'[a-zA-Z0-9_]', c) is not None:
                regex[-1] += c
            else:
                regex[-1] += "\\#{}".format(c)

            i += 1

        while stack:
            stack[-1] += regex.pop()
            regex[-1] += '|'.join(stack.pop())

        self.regex = re.compile("^" + regex[-1] + "$")

    def match(self, strn):
        """Check matching with pattern.

        Args:
            strn (str): Target string

        Returns:
            (bool): True if string matches.
        """
        return len(self.regex.findall(strn)) > 0

    def __repr__(self):
        """Canonical string representation."""
        return "<GlobMatchPattern pattern '{}'>".format(self.pat)


class OrMatchPattern(MatchPattern):
    """OrMatchPattern class."""

    def __init__(self, patterns):
        """init.

        Args:
            patterns (list): List of MatchPattern.
        """
        super(OrMatchPattern, self).__init__()
        self.patterns = patterns

    def match(self, strn):
        """Check matching for each pattern.

        Args:
            strn (str): Target string.

        Returns:
            (bool): True if any pattern matches.
        """
        for pattern in self.patterns:
            if pattern.match(strn):
                return True

    def __repr__(self):
        """Canonical string representation."""
        pats = [repr(pat) for pat in self.patterns]
        return "<OrMatchPattern {}>".format(', '.join(pats))
