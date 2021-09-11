import re
from programy.dialog.joiner.joiner import SentenceJoiner
from programy.utils.logging.ylogger import YLogger


class SentenceJoinerDeDuplicator(SentenceJoiner):
    def combine_answers(self, answers, srai):
        # The simplest heuristic is to pull answers through set data structure and deduplicate pure
        # duplicates
        len_before = len(answers)

        new_answers = []
        for i in range(len(answers)):
            if not (answers[i] in new_answers):
                new_answers.append(answers[i])
        answers = new_answers

        len_after = len(answers)
        if len_after != len_before:
            YLogger.warning(self, "Sentence DeDuplicator stripped duplicated answers: %d %d", len_before, len_after)
        final_sentences = []
        # TODO it would be better to reference to config's bot.default_response setting for
        # the IDK response, but
        # 1) it is not clear what is the best practice to reference variables from YAML.
        # 2) config consumed by SentenceJoinerDeDuplicator has no acces to BotConfiguration where
        # IDK is specified
        IDK_SENTENCE = "Sorry, I don't have an answer for that!"

        # reversed `answers` to join answers in correct order
        for sentence in answers:
            if sentence and sentence.lower() != IDK_SENTENCE.lower():
                # Sometimes sentence can be already merged list of answers which may contain
                # duplicated IDKs. So we make cleaning here.
                if IDK_SENTENCE.lower() in sentence.lower():
                    sentence, _ = re.subn(IDK_SENTENCE, "", sentence, flags=re.IGNORECASE)
                    sentence = sentence.strip()
                    if not sentence:
                        # if sentence is empty after IDK removal
                        continue

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
                # return just the first answer that satisfies the criteria of allowed answer (not IDK).
                # break

        if len(final_sentences) == 0:
            # if we here means all answers are IDKs, choose the only one:
            final_sentences = [IDK_SENTENCE]
        for i, sent in enumerate(final_sentences):
            if "newborn socialbot" in sent:
                final_sentences = [sent]
        if len(final_sentences) > 1:
            final_sentences = [final_sentences[-1]]
        return " ".join([sentence for sentence in final_sentences])
