import sys
import random
import copy
import re


class RNGFormat:
    random_formats = {
                      "#rsn": [1, 2, 3, 4, 5],  # random small number
                      "#rssn": [2, 3],          # random super small number
                      "#rsen": [2, 4, 6, 8],    # random small even number
                      "#rson": [1, 3, 5],       # random small odd number
                      "#risn": [0, 1, 2, 3],    # random index small number (inc 0)
                      "#rmn": [6, 7, 8, 9],     # random medium number
                      "#rb": [True, False],     # random boolean
                      "#rv": ["dog", "fox", "pig", "egg"],       # random variable name
                      "#rst": ['"wolf"', '"fish"', '"lion"'],    # random string
                      "#rss": ['"toad "', '"bird "', '"duck "']  # random string with space
                     }

    @staticmethod
    def __get_random_thing(random_format):
        return random.choice(RNGFormat.random_formats[random_format])

    @staticmethod
    def format(question):
        if "@" in question:
            rf_copy = copy.deepcopy(RNGFormat.random_formats)
            i = 1
            while "@" in question:
                for random_format in RNGFormat.random_formats.keys():
                    if random_format + "@{}".format(i) in question:
                        random_thing = RNGFormat.__get_random_thing(random_format)
                        question = question.replace(random_format + "@{}".format(i),
                                                    str(random_thing))
                        RNGFormat.random_formats[random_format].remove(random_thing)
                i += 1
            RNGFormat.random_formats = rf_copy

        for random_format in RNGFormat.random_formats.keys():
            while random_format in question:
                question = question.replace(random_format,
                                            str(RNGFormat.__get_random_thing(random_format)),
                                            1)
        return question


class Question:
    def __init__(self, question, answer):
        self.__question = question
        self.__answer = self.__format_answer(question, answer)

    @staticmethod
    def __format_answer(question, answer):
        # ipython returns nice type strings in jupyter cells:
        #     e.g. int, bool, float
        # but regular python returns ugly class strings:
        #     e.g. <type 'int'>
        # so if it's a type question, strip that away

        if "type(" in question and "<" in answer:
            left_index = answer.index("'")
            right_index = answer.rindex("'")
            return answer[left_index+1:right_index]
        return answer

    def get_question(self):
        return self.__question

    def __str__(self):
        return self.__question

    def __repr__(self):
        return "q: {}, a: {}".format(self.__question, self.__answer)

    def is_correct_answer(self, guess):
        guess = guess.replace("'", '"')
        comp_answer = self.__answer

        if "[" in comp_answer or "(" in comp_answer:
            # ignore whitespace in list/tuple answers
            # (but leave it in the official answer in case they ask for the solution)
            guess = guess.replace(" ", "")
            comp_answer = comp_answer.replace(" ", "")

        return comp_answer == guess.replace("'", '"') or guess == "s"

    def get_hint(self, guess):
        if '"' in self.__answer and '"' not in guess and "'" not in guess:
            return "Don't forget to use quote marks around string literals"
        elif guess.lower() == self.__answer.lower():
            return "The answer is case sensitive"
        else:
            return ""

    def get_solution(self):
        return self.__answer

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Question):
            return self.__question == other.__question
        return False

    def __hash__(self):
        return hash(self.__question)


class BVQuestion(Question):
    def get_hint(self, guess):
        solution_length = len(self.get_solution())
        if solution_length != len(guess):
            return f"The number of underscores shows the length of the correct answer ({solution_length})"
        return super().get_hint(guess)


class QuestionFormat:
    def __init__(self, level=1, repeats=1):
        self.__level = level
        self.__repeats = repeats
        self.__question = ""

    def set_question(self, question):
        self.__question = question

    def get_repeats(self):
        return self.__repeats

    def get_level(self):
        return self.__level

    def get_question(self):
        return self.__question

    def generate_question(self):
        raise NotImplementedError("This method is abstract.")


def out_str(s):
    if isinstance(s, str):
        return '"' + s + '"'
    else:
        return str(s)


class QEFormat(QuestionFormat):
    def add_question(self, question):
        super().set_question(question)

    def generate_question(self):
        formatted_question = RNGFormat.format(self.get_question())
        answer = out_str(eval(formatted_question))
        return Question("What is the result of this expression?"
                        "\n{}".format(formatted_question),
                        answer)


class QSEFormat(QuestionFormat):
    def add_question(self, question):
        if self.get_question() == "":
            super().set_question(question)
        else:
            super().set_question(self.get_question() + "\n" + question)

    def generate_question(self):
        formatted_question = RNGFormat.format(self.get_question())
        index = formatted_question.rindex("\n")
        formatted_exec = formatted_question[:index]
        exec(formatted_exec)
        formatted_eval = formatted_question[index+1:]
        answer = out_str(eval(formatted_eval))
        return Question("After the following code is executed:\n"
                        "{}\n"
                        "What is the result of the expression below?\n"
                        "{}".format(formatted_exec, formatted_eval),
                        answer)


class BVFormat(QuestionFormat):
    def add_question(self, question):
        if self.get_question() == "":
            super().set_question(question)
        else:
            super().set_question(self.get_question() + "\n" + question)

    def generate_question(self):
        formatted_question = RNGFormat.format(self.get_question())
        last_new_line_index = formatted_question.rindex("\n")
        formatted_exec = formatted_question[:last_new_line_index]
        formatted_eval = formatted_question[last_new_line_index + 1:]

        code_to_exec = formatted_exec.replace("$", "")
        code_to_eval = formatted_eval.replace("$", "")
        exec(code_to_exec)
        eval_answer = out_str(eval(code_to_eval))

        dollar_index = formatted_question.index("$")
        re_match = re.search(r'[\s:]', formatted_question[dollar_index:])
        if re_match is not None:
            next_space = re_match.start() + dollar_index
        else:
            next_space = len(formatted_question)

        answer = formatted_question[dollar_index+1:next_space]
        formatted_question = formatted_question.replace("$" + answer, "_" * len(answer))

        return BVQuestion("The result of running the following code is {}.\n"
                          "What should fill in the blank?\n"
                          "{}".format(eval_answer, formatted_question),
                          answer)


class FormatDeck:
    def __init__(self, formats):
        self.__formats = formats
        self.__renew()

    def __renew(self):
        self.__deck = copy.deepcopy(self.__formats)
        random.shuffle(self.__deck)

    def draw(self):
        if len(self.__deck) == 0:
            self.__renew()
        return self.__deck.pop()


def extract_parameter(line, option):
    line = line.strip()
    index_start = line.index(option) + len(option)
    if " " in line[index_start:]:
        index_end = line.index(" ", index_start)
    else:
        index_end = len(line)
    return line[index_start:index_end]


def get_question_formats(lines):
    question_format = 0
    question_format_bag = []
    QTYPES = {"QE", "QS", "BV"}

    for line in lines:
        if line[:2] == "//":
            pass
        elif line == "\n" and question_format != 0:
            question_format_bag.append(question_format)
            question_format = 0
        elif line == "\n":
            continue
        elif line == "-\n":
            question_format.add_question("")
        elif line[:2] in QTYPES:
            if "-l" in line:
                level = int(extract_parameter(line, "-l"))
            else:
                level = 1

            if "-r" in line:
                repeats = int(extract_parameter(line, "-r"))
            else:
                repeats = 1

            if line[:2] == "QE":
                question_format = QEFormat(level, repeats)
            elif line[:2] == "QS":
                question_format = QSEFormat(level, repeats)
            elif line[:2] == "BV":
                question_format = BVFormat(level, repeats)
        else:
            question_format.add_question(line.rstrip())

    if question_format != 0:
        question_format_bag.append(question_format)

    return question_format_bag


def get_tiered_questions(formats):
    formats.sort(key=lambda qf: qf.get_level())
    max_level = max(formats, key=lambda qf: qf.get_level()).get_level()

    questions = []
    for level in range(1, max_level + 1):
        level_formats = list(filter(lambda qf: qf.get_level() == level, formats))

        repeats = level_formats[0].get_repeats()
        level_questions = get_questions(level_formats, repeats)
        questions.extend(level_questions)

    return questions


def get_questions(formats, number=10):
    questions = []
    deck = FormatDeck(formats)
    for _ in range(number):
        question_format = deck.draw()
        random_question = question_format.generate_question()

        i = 0
        while random_question in questions and i < 5:
            question_format = deck.draw()
            random_question = question_format.generate_question()
            i += 1

        questions.append(random_question)

    return questions


def load_formats_from_file(filename):
    with open(filename, "r") as text_file:
        lines = text_file.readlines()
    return get_question_formats(lines)


def run(file):
    question_formats = load_formats_from_file(file)
    questions = get_tiered_questions(question_formats)

    while True:
        for question_number, question in enumerate(questions):
            print("Question {} of {}".format(question_number+1, len(questions)))
            unsolved = True
            attempt = 1
            while unsolved:
                print(question.get_question())

                guess = input(">>>")
                guess = guess.strip()
                if question.is_correct_answer(guess):
                    print("Correct!\n")
                    unsolved = False
                elif guess == "quit":
                    return
                elif attempt >= 4 and guess == "I give up":
                    print("The solution is:")
                    print("\t" + question.get_solution())
                    print("Work out why this is the case before continuing!")
                    print("Please type 'I understand' (without quotes) to continue.")
                    busywork = input(">>>")
                    while busywork != "I understand":
                        busywork = input(">>>")
                    unsolved = False
                elif question.get_hint(guess) != "":
                    print(question.get_hint(guess) + "\n")
                else:
                    print("Try again...\n")

                attempt += 1
                if attempt >= 4 and unsolved:
                    print("** Type 'I give up' (without quotes) to see the solution **")

        print("All questions answered correctly! Great job.")
        response = ""
        while response.lower() not in ["yes", "no", "y", "n"]:
            print("Would you like to try more questions like these? (Y/N)")
            response = input(">>>")

        if response.lower() in ["yes", "y"]:
            questions = get_questions(question_formats)
        else:
            break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("Need to provide question file as argument.")
    if len(sys.argv) > 2:
        # assume multiple arguments means spaces in the path
        filename = " ".join(sys.argv[1:])
    else:
        filename = sys.argv[1]

    try:
        run(filename)
    except KeyboardInterrupt:
        pass
