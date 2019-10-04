from programy.dialog.joiner.joiner import SentenceJoiner
from programy.utils.logging.ylogger import YLogger


class SentenceJoinerDeDuplicator(SentenceJoiner):
    def combine_answers(self, answers, srai):
        # The simplest heuristic is to pull answers through set data structure and deduplicate pure
        # duplicates
        len_before = len(answers)
        answers = list(set(answers))
        len_after = len(answers)
        if len_after != len_before:
            YLogger.warning(self, "Sentence DeDuplicator stripped duplicated answers: %d %d",
                            len_before, len_after)
        final_sentences = []
        for sentence in answers:
            if sentence:

                # Capitalise the start of each sentence
                if sentence[0].isalpha():
                    sentence = sentence[0].upper() + sentence[1:]

                # If it ends with a terminator, keep the terminator, otherwise add a full stop
                if self.ends_with_terminator(sentence):
                    final_sentences.append(sentence)
                else:
                    if srai is False:
                        final_sentences.append(sentence + self._configuration.terminator)
                    else:
                        final_sentences.append(sentence)

        return " ".join([sentence for sentence in final_sentences])
