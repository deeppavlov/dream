from nltk.tokenize import word_tokenize, RegexpTokenizer


class yesno_question:
    def __init__(self):
        self.tokenizer = RegexpTokenizer(r"\w+")

        fo = open(file="yesno_dicts.txt", mode="r", encoding="utf-8")
        self.adverbs = fo.readline().strip().split(",")
        self.qa_converter = {k: v for k, v in [s.split(":") for s in fo.readline().strip().split(",")]}
        self.yes_types = fo.readline().strip().split(",")
        self.no_types = fo.readline().strip().split(",")

        self.qa_dicts = {}
        for line in fo.readlines():
            if line.startswith("#") or line.strip() == "":
                continue
            items = line.strip().split("|")
            self.qa_dicts[items[0]] = [items[1], items[2], items[3], items[4]]
        fo.close()

    def get_answer_type(self, words):
        """0: yes short answer without adverb
        1: no short answer without adverb
        2: yes short answer with adverb
        3: no short answer with adverb
        4: long answer or unidentify"""
        adverb = ""

        if 0 < len(words) < 4:
            first_word = words[0].replace(".", "").replace("!", "").replace(",", "")

            for i, word in enumerate(words):
                if word in self.adverbs:
                    j = i
                    while j < len(words) and words[j] in self.adverbs:
                        adverb += words[j] + " "
                        j += 1
                    break

            if first_word in self.yes_types:
                if adverb == "":
                    return 0, adverb
                else:
                    return 2, adverb
            elif first_word in self.no_types:
                if adverb == "":
                    return 1, adverb
                else:
                    return 3, adverb
            elif first_word in self.adverbs and len(words) == 1:
                return 2, adverb
            elif first_word == "not" and words[1] in self.adverbs:
                return 2, adverb

        return 4, adverb

    def create_answer(self, key, second_part, answer, answer_type, adverb):
        if second_part[-1] == "?":
            second_part = second_part[:-1]

        if adverb != "":
            for i, word in enumerate(second_part):
                if word in self.adverbs:
                    second_part.pop(i)

        if answer_type < 2:
            return (
                self.qa_dicts[key][answer_type]
                + " "
                + " ".join([self.qa_converter[w] if w in self.qa_converter else w for w in second_part])
                + "."
            )
        else:
            return (
                self.qa_dicts[key][answer_type]
                + " "
                + adverb
                + " ".join([self.qa_converter[w] if w in self.qa_converter else w for w in second_part])
                + "."
            )

    def preprocess_question(self, question):
        question = question.lower().replace(", please,", "").replace(", please", "").replace("please, ", "")
        q_words = word_tokenize(question)
        if q_words[-1] in [".", "?", "!"]:
            q_words.pop(-1)
        return q_words

    def preprocess_answer(self, answer):
        # split and remove punctuation
        a_words = self.tokenizer.tokenize(answer.lower())
        # no not -> yes
        if len(a_words) > 2:
            if a_words[0] == "no" and a_words[1] == "not":
                a_words[0] = "yes"
        return a_words

    def rewrite_yesno_answer(self, question, answer):
        a_words = self.preprocess_answer(answer)
        answer_type, adverb = self.get_answer_type(a_words)
        if answer_type < 4:
            q_words = self.preprocess_question(question)
            if answer_type < 4:
                if len(q_words) > 3:
                    first_part, second_part = q_words[:3], q_words[3:]
                    key = " ".join(first_part).replace("n't", "not")
                    if key in self.qa_dicts:
                        return self.create_answer(key, second_part, answer, answer_type, adverb)
                if len(q_words) > 2:
                    first_part, second_part = q_words[:2], q_words[2:]
                    key = " ".join(first_part).replace("n't", "not")
                    if key in self.qa_dicts:
                        return self.create_answer(key, second_part, answer, answer_type, adverb)

        return ""
