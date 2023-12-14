import ast

from functools import reduce
from typing import Any, Callable, Dict


def compile_expression(expression: str) -> Callable[[Dict[str, Any]], bool]:
    """Compiles an expression and returns a function to yield its value given
    an environment.

    :param expression: The expression to evaluate.

    :return: a callable that yields a boolean
    """
    def inner(env):
        def cmp(a, op, b):
            match op:
                case ast.Eq(): return a == b
                case ast.Gt(): return a > b
                case ast.GtE(): return a >= b
                case ast.Lt(): return a < b
                case ast.LtE(): return a <= b
                case _: raise ValueError('{} {} {}'.format(
                    a, type(op).__name__, b))

        def val(node):
            match node:
                case ast.BoolOp(op, values):
                    match op:
                        case ast.And(): return reduce(
                            lambda acc, v: acc and v,
                            (val(v) for v in values),
                            True)
                        case ast.Or(): return reduce(
                            lambda acc, v: acc or v,
                            (val(v) for v in values),
                            False)
                case ast.Compare(left, ops, comparators): return reduce(
                    lambda acc, i: cmp(acc, *i),
                    zip(ops, (val(c) for c in comparators)),
                    val(left))
                case ast.Constant(value):
                    return value
                case ast.Name(n):
                    try:
                        return env[n]
                    except KeyError:
                        raise ValueError(
                            'in "{}": unknown value "{}"'.format(
                                expression, n))
                case _: raise ValueError(
                    'in "{}": unknown expression "{}"'.format(
                        expression, ast.unparse(node)))

        return val(at.body)

    try:
        at = ast.parse(expression, mode='eval')
        return inner
    except SyntaxError:
        raise ValueError('syntax error: {}'.format(expression))
