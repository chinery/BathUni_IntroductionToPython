from test_helper import Test, TestSpec
import sys
import textwrap


def generic_hints(output):
    if output is None:
        return "Make sure you are always returning something from your function."
    elif isinstance(output, IndexError):
        return "There was an IndexError. Check your indexing. " \
               "e.g. trying to access a character of an empty string will cause this error."
    elif isinstance(output, Exception):
        return "There was some kind of error. The actual section above should include more information."
    else:
        return ""


def format_var(var):
    if isinstance(var, str):
        return "'" + var + "'"
    else:
        return var


def format_test_output(test):
    output = "\n\tinputs: {}\n\texpected: {}" \
             "\n\tactual: {}".format(str(test.get_inputs())[1:-1],
                                     format_var(test.get_expected()),
                                     format_var(test.get_output()))
    if test.get_result():
        # PASS
        return output + "\n\tresult: PASS"
    else:
        # FAIL
        if test.get_hint() != "":
            hint = test.get_hint()
        elif generic_hints(test.get_output()) != "":
            hint = generic_hints(test.get_output())
        else:
            return output + "\n\tresult: FAIL"

        hint = textwrap.indent(textwrap.fill(hint, 60), "\t" + " "*len("hint: ")).lstrip()
        return output + "\n\tresult: FAIL\n\thint: " + hint


def run_tests(fn, tests, full_results=True):
    successes = 0
    total = len(tests)
    for i, test in enumerate(tests):
        result = test.run(fn)
        if full_results:
            print(f"Test {i+1}/{total}: {format_test_output(test)}")
        elif result:
            print(f"Test {i+1}/{total}: PASS")
        else:
            print(f"Test {i+1}/{total}: FAIL")

        if result:
            successes += 1
        else:
            return False
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("Need to provide test spec file as argument.")
    if len(sys.argv) > 2:
        # assume multiple arguments means spaces in the path
        filename = " ".join(sys.argv[1:])
    else:
        filename = sys.argv[1]

    test_spec = TestSpec(filename)

    tests, secret_tests = test_spec.generate_tests()
    assert(test_spec.get_name() in dir())
    test_fn = eval(test_spec.get_name())

    print(f"Running tests on function {test_spec.get_name()}\n")
    success = run_tests(test_fn, tests)
    print()

    if not success:
        print("Try editing your code and re-running the cell.")
    else:
        print(f"Running {len(secret_tests)} secret tests...\n")
        success = run_tests(test_fn, secret_tests, False)
        print()
        if success:
            print("All tests passed! Great job!")
        else:
            print(textwrap.fill("One or more secret tests failed. Make sure you are not"
                                " being too specific in your code. The tests that failed will"
                                " be similar to the previous tests shown here."))
