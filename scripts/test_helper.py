import random
import math
import numbers
import traceback
import sys
from typing import Iterable
import copy

random.seed(0)
boolrange = (False, True)


class ModifiedInput:
    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "Your code modified the input! This is not allowed." \
               "\n\t        Try creating a copy if you need to modify the object."


class PrettyError:
    def __init__(self, exception, line):
        self.__exception = exception
        self.__line = line

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"An error occurred on the line:" \
               f"\n\t          {self.__line}" \
               f"\n\t        The error was:" \
               f"\n\t          {self.__exception.__class__.__name__}: {self.__exception}"


class Test:
    def __init__(self, inputs, expected, hint=""):
        self.__inputs = inputs
        self.__original_inputs = copy.deepcopy(inputs)
        self.__expected = expected
        self.__hint = hint
        self.__output = None
        self.__result = None

    def get_inputs(self):
        return self.__original_inputs

    def get_expected(self):
        return self.__expected

    def get_hint(self):
        return self.__hint

    def get_output(self):
        return self.__output

    def get_result(self):
        return self.__result

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "inputs: {}, expected: {}".format(self.get_inputs(), self.get_expected())

    def run(self, func):
        try:
            self.__output = func(*self.__inputs)
        except Exception as e:
            # this hideousness extracts the line of code that caused the error
            data = traceback.extract_tb(sys.exc_info()[2])
            line = data[-1][-1]
            self.__output = PrettyError(e, line)
            # for now assume no deliberate errors... might need to change this
            return False

        if self.__inputs != self.__original_inputs:
            self.__output = ModifiedInput()
            return False
        # testing for equality usually requires horrible type checking
        elif self.__output is None or self.__expected is None:
            self.__result = self.__output == self.__expected
        elif isinstance(self.__expected, numbers.Number):
            # allow 'close enough' for floats
            # noinspection PyTypeChecker
            self.__result = math.isclose(self.__output, self.__expected)
        else:
            self.__result = self.__output == self.__expected
        return self.__result


def nth_word(s, n):
    sp = s.split()
    if n < len(sp):
        return sp[n]
    else:
        return ""


class TestCaseSpec:
    def __init__(self, inputs, secret=False, hint=""):
        self.__inputs = inputs
        self.__secret = secret
        self.__hint = hint

    def get_inputs(self):
        return self.__inputs

    def get_hint(self):
        return self.__hint

    def is_secret(self):
        return self.__secret

    def add_tests(self, tests, secret_tests, func):
        answer = func(*self.get_inputs())
        if not self.is_secret():
            tests.append(Test(self.get_inputs(), answer, self.get_hint()))
        else:
            secret_tests.append(Test(self.get_inputs(), answer, self.get_hint()))


class RandomTestCaseSpec(TestCaseSpec):
    def __init__(self, inputs, repeats=1, secret=False, hint=""):
        super().__init__(inputs, secret, hint)
        self.__repeats = repeats

    def add_tests(self, tests, secret_tests, func):
        previous_inputs = [test.get_inputs() for test in tests]
        previous_inputs.extend([test.get_inputs() for test in secret_tests])

        spec = self.get_inputs()
        spec = ["random." + i for i in spec]
        for _ in range(self.__repeats):
            inputs = [eval(randomspec) for randomspec in spec]
            while inputs in previous_inputs:
                inputs = [eval(randomspec) for randomspec in spec]
            answer = func(*inputs)
            if not self.is_secret():
                tests.append(Test(inputs, answer))
            else:
                secret_tests.append(Test(inputs, answer))


class RangeTestCaseSpec(TestCaseSpec):

    # e.g. input [range(0,10), range(0,10)]
    #            [range(0,10)]
    #            [(1,), range(0,10)]
    @staticmethod
    def __get_range_specs(specs):
        if len(specs) == 1:
            return [[spec] for spec in specs[0]]
        else:
            return [[x, *spec] for x in specs[0] for spec in RangeTestCaseSpec.__get_range_specs(specs[1:])]

    @staticmethod
    def __iterableify(obj):
        if isinstance(obj, Iterable):
            return obj
        else:
            return (obj,)

    def add_tests(self, tests, secret_tests, func):
        previous_inputs = [test.get_inputs() for test in tests]
        previous_inputs.extend([test.get_inputs() for test in secret_tests])

        specs = self.get_inputs()
        specs = [self.__iterableify(spec) for spec in specs]
        specs = self.__get_range_specs(specs)

        for inputs in specs:
            if inputs in previous_inputs:
                continue

            answer = func(*inputs)
            if not self.is_secret():
                tests.append(Test(inputs, answer, self.get_hint()))
            else:
                secret_tests.append(Test(inputs, answer, self.get_hint()))


class InputSpec:
    """
        An inputspec is used when reading a block of lines (TestCaseSpecs)
    """
    def __init__(self, secret=False):
        self.__secret = secret

    def is_secret(self):
        return self.__secret

    def format(self, line):
        raise NotImplementedError("This is an abstract method")


class PlainInputSpec(InputSpec):
    """
        Will look like this:
        *in plain int;int
        5;5
        -1;-1 : Don't forget negative numbers
    """
    def __init__(self, line, secret=False):
        super().__init__(secret)
        in_type = nth_word(line, 2)
        in_type = TestSpec.split_and_strip(in_type)
        self.__types = [eval(x) for x in in_type]

    def format(self, line):
        line_sp = line.split(" : ")
        inputs = TestSpec.split_and_strip(line_sp[0])
        inputs = [t(i) for t, i in zip(self.__types, inputs)]
        if len(line_sp) > 1:
            return TestCaseSpec(inputs, secret=self.is_secret(), hint=line_sp[1])
        else:
            return TestCaseSpec(inputs, secret=self.is_secret())


class RandomInputSpec(InputSpec):
    """
        Supports any method in random
        Will look like this:
        *in random 5
        randrange(-10,10);randrange(-10,10)
        uniform(-10,10);uniform(-10,10)
    """
    def __init__(self, line, secret=False):
        super().__init__(secret)
        self.__random_freq = int(nth_word(line, 2))

    def format(self, line):
        inputs = TestSpec.split_and_strip(line)
        return RandomTestCaseSpec(inputs, self.__random_freq, self.is_secret())


class RangeInputSpec(InputSpec):
    """
        Supports any iterators, and will generate all possibilities
        Special:
            boolrange
        will be converted to
            (False, True)

        Will look like this:
        *in range
        range(0,10);range(5,10)
        boolrange;boolrange
    """
    def format(self, line):
        inputs = TestSpec.split_and_strip(line)
        inputs = [eval(x) for x in inputs]
        return RangeTestCaseSpec(inputs, self.is_secret())


class TestSpec:
    SEP = ";"
    MODES = {"name", "in", "code"}

    def __init__(self, filename):
        self.__inspecs = []
        self.__code = ""
        with open(filename, "r") as text_file:
            lines = text_file.readlines()
        self.__parse(lines)

    def __parse(self, text_lines):
        mode = None
        in_spec = None

        for line in text_lines:
            line = line.rstrip()
            escape = False
            if len(line) > 1:
                if line[0:2] == "//":
                    continue
                if line[0:2] == r"\*":
                    escape = True
                    line = line[1:]

            if len(line) > 0 and line[0] == "*" and not escape:
                word = nth_word(line, 0)[1:]
                if word not in TestSpec.MODES:
                    raise RuntimeError("Unsupported *mode")
                mode = word

                if word == "in":
                    if nth_word(line, 1) == "plain":
                        in_spec = PlainInputSpec(line, False)
                    elif nth_word(line, 1) == "secret_plain":
                        in_spec = PlainInputSpec(line, True)
                    elif nth_word(line, 1) == "random":
                        in_spec = RandomInputSpec(line, False)
                    elif nth_word(line, 1) == "secret_random":
                        in_spec = RandomInputSpec(line, True)
                    elif nth_word(line, 1) == "range":
                        in_spec = RangeInputSpec(False)
                    elif nth_word(line, 1) == "secret_range":
                        in_spec = RangeInputSpec(True)
                    else:
                        raise RuntimeError("Didn't recognise input format")

            elif mode is None:
                raise RuntimeError("Need *mode before data")
            elif mode == "name":
                self.__name = line
            elif mode == "in":
                self.__inspecs.append(in_spec.format(line))
            elif mode == "code":
                if self.__code == "":
                    self.__code = line
                else:
                    self.__code += "\n" + line

    @staticmethod
    def split_and_strip(line):
        return [x.strip() for x in line.split(TestSpec.SEP)]

    def generate_tests(self):
        tests = []
        secret_tests = []

        exec(self.__code, locals(), locals())
        assert(self.__name in dir())
        solution_function = eval(self.__name)

        for input_spec in self.__inspecs:
            input_spec.add_tests(tests, secret_tests, solution_function)

        return tests, secret_tests

    def get_name(self):
        return self.__name


def run():
    test_test = Test([1, 2], 3)

    print(test_test.run(lambda x, y: x + y))

    # spec = TestSpec("../Chapter 2/questions/add")
    spec = TestSpec("../Chapter 2/questions/2.5/reverse")
    tests, secret_tests = spec.generate_tests()
    print()


if __name__ == "__main__":
    run()


