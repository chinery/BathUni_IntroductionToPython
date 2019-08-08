import random
import math
import numbers

random.seed(0)


class Test:
    def __init__(self, inputs, expected, hint=""):
        self.__inputs = inputs
        self.__expected = expected
        self.__hint = hint
        self.__output = None
        self.__result = None

    def get_inputs(self):
        return self.__inputs

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
        return "inputs: {}, expected: {}".format(self.get_inputs, self.get_expected)

    def run(self, func):
        self.__output = func(*self.__inputs)
        # testing for equality usually requires horrible type checking
        if self.__output is None or self.__expected is None:
            self.__result = self.__output == self.__expected
        elif isinstance(self.__expected, numbers.Number):
            # noinspection PyTypeChecker
            self.__result = math.isclose(self.__output, self.__expected)
        else:
            self.__result = self.__output == self.__expected
        return self.__result


class TestCaseSpec:
    def __init__(self, inputs, types, hint=""):
        self.__inputs = [t(i) for t, i in zip(types, inputs)]
        self.__hint = hint

    def get_inputs(self):
        return self.__inputs

    def get_hint(self):
        return self.__hint


class TestSpec:
    SEP = ";"
    MODES = {
             "name": 0,
             "inpublic": 1,
             "insecret": 2,
             "inrandom": 3,
             "insecretrandom": 4,
             "code": 5
             }

    def __init__(self, filename):
        self.__inpublic = []
        self.__insecret = []
        self.__inrandom = []
        self.__insecretrandom = []
        self.__code = ""
        with open(filename, "r") as text_file:
            lines = text_file.readlines()
        self.__parse(lines)
        self.__post_process()

    @staticmethod
    def __first_word(text):
        ix = text.find(" ")
        if ix != -1:
            return text[:ix]
        else:
            return text

    @staticmethod
    def __second_word(text):
        ix = text.index(" ")
        end_ix = text.find(" ", ix+1)
        if end_ix != -1:
            return text[ix+1:end_ix]
        else:
            return text[ix+1:]

    def __parse(self, text_lines):
        mode = None
        random_freq = 1
        in_type = None

        for line in text_lines:
            line = line.rstrip()
            if line[0] == "*":
                word = TestSpec.__first_word(line)[1:]
                if word not in TestSpec.MODES.keys():
                    raise RuntimeError("Unsupported *mode")
                mode = TestSpec.MODES[word]

                if word == "inpublic" or word == "insecret":
                    in_type = TestSpec.__second_word(line)
                    in_type = TestSpec.__split_and_strip(in_type)
                    in_type = [eval(x) for x in in_type]
                elif word == "inrandom" or word == "insecretrandom":
                    random_freq = int(TestSpec.__second_word(line))
            elif mode is None:
                raise RuntimeError("Need *mode before data")
            elif mode == 0:
                self.__name = line
            elif mode == 1 or mode == 2:
                line_sp = line.split(" : ")
                inputs = TestSpec.__split_and_strip(line_sp[0])
                if len(line_sp) > 1:
                    test_case_spec = TestCaseSpec(inputs, in_type, line_sp[1])
                else:
                    test_case_spec = TestCaseSpec(inputs, in_type)

                if mode == 1:
                    self.__inpublic.append(test_case_spec)
                else:
                    self.__insecret.append(test_case_spec)
            elif mode == 3:
                self.__inrandom.extend([line for _ in range(random_freq)])
            elif mode == 4:
                self.__insecretrandom.extend([line for _ in range(random_freq)])
            elif mode == 5:
                if self.__code == "":
                    self.__code = line
                else:
                    self.__code += "\n" + line

    @staticmethod
    def __split_and_strip(line):
        return [x.strip() for x in line.split(TestSpec.SEP)]

    def __post_process(self):
        inr = [TestSpec.__split_and_strip(line) for line in self.__inrandom]
        self.__inrandom = [["random." + i for i in line] for line in inr]

        inr = [TestSpec.__split_and_strip(line) for line in self.__insecretrandom]
        self.__insecretrandom = [["random." + i for i in line] for line in inr]

    def generate_tests(self):
        tests = []
        secret_tests = []

        exec(self.__code)
        assert (self.__name in dir())
        solution_function = eval(self.__name)

        for inputs in self.__inpublic:
            answer = solution_function(*inputs.get_inputs())
            tests.append(Test(inputs.get_inputs(), answer, inputs.get_hint()))

        for inputs in self.__insecret:
            answer = solution_function(*inputs.get_inputs())
            secret_tests.append(Test(inputs.get_inputs(), answer, inputs.get_hint()))

        random_inputs = []
        for spec in self.__inrandom:
            inputs = [eval(randomspec) for randomspec in spec]
            while inputs in random_inputs:
                inputs = [eval(randomspec) for randomspec in spec]
            random_inputs.append(inputs)
            answer = solution_function(*inputs)
            tests.append(Test(inputs, answer))

        random_inputs = []
        for spec in self.__insecretrandom:
            inputs = [eval(randomspec) for randomspec in spec]
            while inputs in random_inputs:
                inputs = [eval(randomspec) for randomspec in spec]
            random_inputs.append(inputs)
            answer = solution_function(*inputs)
            secret_tests.append(Test(inputs, answer))

        return tests, secret_tests

    def get_name(self):
        return self.__name


if __name__ == "__main__":
    test_test = Test([1, 2], 3)

    print(test_test.run(lambda x, y: x+y))

    spec = TestSpec("../Chapter 2/questions/add")
    tests, secret_tests = spec.generate_tests()
    print()


