from test_helper import Test, TestSpec
import sys
import textwrap


def format_expected(expected):
    if isinstance(expected, str):
        return "'" + expected + "'"
    else:
        return expected


def format_input(inp):
    return inp


def format_inputs(inputs):
    return str([format_input(inp) for inp in inputs])[1:-1]


def format_test(test, name):
    return f"{name}({format_inputs(test.get_inputs())}) -> {format_expected(test.get_expected())}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("Need to provide test spec file as argument.")
    if len(sys.argv) > 2:
        # assume multiple arguments means spaces in the path
        filename = " ".join(sys.argv[1:])
    else:
        filename = sys.argv[1]

    test_spec = TestSpec(filename)

    tests, _ = test_spec.generate_tests()

    print(f"Example tests for function {test_spec.get_name()}\n")
    tot = min(5, len(tests))
    for i in range(tot):
        print(f"Test {i + 1}/{tot}: {format_test(tests[i], test_spec.get_name())}")
