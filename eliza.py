import logging
import random
import re
import threading
import emotion_dynamics

# Fix Python2/Python3 incompatibility
try:
    input = raw_input
except NameError:
    pass

log = logging.getLogger(__name__)


class Key:
    def __init__(self, word, weight, decomps):
        self.word = word
        self.weight = weight
        self.decomps = decomps


class Decomp:
    def __init__(self, parts, save, reasmbs):
        self.parts = parts
        self.save = save
        self.reasmbs = reasmbs
        self.next_reasmb_index = 0


class Eliza:
    def __init__(self):
        self.initials = []
        self.finals = []
        self.quits = []
        self.emotions = []
        self.emotion_triggers = {}
        self.pres = {}
        self.posts = {}
        self.synons = {}
        self.keys = {}
        self.memory = []
        # new "emotional Eliza" using wasabi emotion dynamics
        self.emotional_eliza = emotion_dynamics.EmotionalAgent()
        self.input_emotions = []  # emotions contained in language input

    def load(self, path):
        key = None
        decomp = None
        with open(path) as file:
            for line in file:
                if not line.strip():
                    continue
                tag, content = [part.strip() for part in line.split(':')]
                if tag == 'initial':
                    self.initials.append(content)
                elif tag == 'final':
                    self.finals.append(content)
                elif tag == 'quit':
                    self.quits.append(content)
                elif tag == 'pre':
                    parts = content.split(' ')
                    self.pres[parts[0]] = parts[1:]
                elif tag == 'post':
                    parts = content.split(' ')
                    self.posts[parts[0]] = parts[1:]
                elif tag == 'synon':
                    parts = content.split(' ')
                    self.synons[parts[0]] = parts
                elif tag == 'emotion':  # get set of possible emotions
                    parts = content.split(' ')
                    self.emotions.append(content)
                elif tag == 'emotionTrigger':  # get set of emotional triggers
                    parts = content.split(' ')
                    word = parts[0]
                    impulse = parts[1]
                    emotion_trigger = (word, impulse)
                    self.emotion_triggers[word] = emotion_trigger
                elif tag == 'key':
                    parts = content.split(' ')
                    word = parts[0]
                    weight = int(parts[1]) if len(parts) > 1 else 1
                    key = Key(word, weight, [])
                    self.keys[word] = key
                elif tag == 'decomp':
                    parts = content.split(' ')
                    save = False
                    if parts[0] == '$':
                        save = True
                        parts = parts[1:]
                    decomp = Decomp(parts, save, [])
                    key.decomps.append(decomp)
                elif tag == 'reasmb':
                    parts = content.split(' ')
                    decomp.reasmbs.append(parts)

    def _match_decomp_r(self, parts, words, results):
        if not parts and not words:
            return True
        if not parts or (not words and parts != ['*']):
            return False
        if parts[0] == '*':
            for index in range(len(words), -1, -1):
                results.append(words[:index])
                if self._match_decomp_r(parts[1:], words[index:], results):
                    return True
                results.pop()
            return False
        elif parts[0].startswith('@'):
            root = parts[0][1:]
            if not root in self.synons:
                raise ValueError('Unknown synonym root {}'.format(root))
            if not words[0].lower() in self.synons[root]:
                return False
            results.append([words[0]])
            return self._match_decomp_r(parts[1:], words[1:], results)
        elif parts[0].lower() != words[0].lower():
            return False
        else:
            return self._match_decomp_r(parts[1:], words[1:], results)

    def _match_decomp(self, parts, words):
        results = []
        if self._match_decomp_r(parts, words, results):
            return results
        return None

    def _next_reasmb(self, decomp):
        index = decomp.next_reasmb_index
        result = decomp.reasmbs[index % len(decomp.reasmbs)]
        decomp.next_reasmb_index = index + 1
        return result

    def _reassemble(self, reasmb, results):
        output = []
        output_append = ''

        # In case of a question for Eliza's emotional state, evaluate whether
        # questioned emotion is true or not and response accordingly
        current_emotion = ''
        if '<emotion_response>' in reasmb:
            current_emotion = self.emotion()
            if current_emotion in self.input_emotions:
                output.append('Ja,')
            else:
                output.append('Nein,')

        # when user says sorry, an angry state is improved by a positive impulse
        if '<sorry>' in reasmb:
            current_emotion = self.emotion()
            if current_emotion == 'aergerlich' or current_emotion == 'genervt':
                self.send_impulse(50)

        # send emotional impulse and dominance attached to a reassembly rule
        if '<impulse>' in reasmb:
            impulse = reasmb[len(reasmb) - 1]
            impulse = impulse.replace('[', '')
            impulse = impulse.replace(']', '')
            impulse = impulse.split(',')
            # index 0: impulse value index 1: dominance value
            output_append = self.send_impulse(float(impulse[0]), float(impulse[1]))
        for reword in reasmb:
            if (not reword or reword == '<emotion_response>' or reword == '<impulse>'
                    or reword == '<sorry>' or reword.startswith('<no_') or reword.startswith('[')
                    or reword == '<switch>'):
                continue
            if reword[0] == '(' and reword[-1] == ')':
                index = int(reword[1:-1])
                if index < 1 or index > len(results):
                    raise ValueError('Invalid result index {}'.format(index))
                if index == 1 and current_emotion:
                    # insert current emotion when emotional state is questioned
                    output.append(current_emotion)
                    continue
                else:
                    insert = results[index - 1]
                for punct in [',', '.', ';']:
                    if punct in insert:
                        insert = insert[:insert.index(punct)]
                output.extend(insert)
            elif reword == '<emotion>':  # insert current emotion
                output.append(self.emotion())
            else:
                output.append(reword)
        output.append(output_append)
        return output

    def _sub(self, words, sub):
        output = []
        for word in words:
            word_lower = word.lower()
            if word_lower in sub:
                output.extend(sub[word_lower])
            else:
                output.append(word)
        return output

    def _match_key(self, words, key):
        for decomp in key.decomps:
            results = self._match_decomp(decomp.parts, words)
            if results is None:
                log.debug('Decomp did not match: %s', decomp.parts)
                continue
            log.debug('Decomp matched: %s', decomp.parts)
            log.debug('Decomp results: %s', results)
            results = [self._sub(words, self.posts) for words in results]
            log.debug('Decomp results after posts: %s', results)
            reasmb = self._next_reasmb(decomp)
            log.debug('Using reassembly: %s', reasmb)
            if reasmb[0] == 'goto':
                goto_key = reasmb[1]
                if not goto_key in self.keys:
                    raise ValueError('Invalid goto key {}'.format(goto_key))
                log.debug('Goto key: %s', goto_key)
                return self._match_key(words, self.keys[goto_key])
            output = self._reassemble(reasmb, results)

            if '<no_trigger>' not in reasmb:
                # retrieve emotional triggers
                emotion_triggers = [w.lower() for w in words if w.lower() in self.emotion_triggers]
                log.debug('Emotional Triggers: %s', [(t[0], t[1]) for t in emotion_triggers])

                # accumulate and send emotional impulses
                impulse = 0
                for trigger in emotion_triggers:
                    new_impulse = float(self.emotion_triggers[trigger][1])

                    # if trigger is negated, switch its effect
                    index_trigger = words.index(self.emotion_triggers[trigger][0])
                    if words[index_trigger - 1] == 'nicht' or '<switch>' in reasmb:
                        new_impulse *= -1

                    if ('<no_pos_trigger>' in reasmb and new_impulse > 0):
                        # no positive impulses permitted
                        continue
                    elif '<no_neg_trigger>' in reasmb and new_impulse < 0:
                        # no negative impulses permitted
                        continue

                    impulse += new_impulse
                if impulse:
                    output.append(self.send_impulse(impulse))

           # FOR TESTING: always tell current emotional state
           # else:
           #     output.append('Ich bin gerade ' + self.emotion())

            if decomp.save:
                self.memory.append(output)
                log.debug('Saved to memory: %s', output)
                continue
            return output
        return None

    def respond(self, text):
        if text.lower() in self.quits:
            return None

        text = re.sub(r'\s*\.+\s*', ' . ', text)
        text = re.sub(r'\s*,+\s*', ' , ', text)
        text = re.sub(r'\s*;+\s*', ' ; ', text)
        log.debug('After punctuation cleanup: %s', text)

        words = [w for w in text.split(' ') if w]
        log.debug('Input: %s', words)

        words = self._sub(words, self.pres)
        log.debug('After pre-substitution: %s', words)

        # retrieve emotions from input
        self.input_emotions = [w.lower() for w in words if w.lower() in self.emotions]
        log.debug('Emotions: %s', self.input_emotions)

        keys = [self.keys[w.lower()] for w in words if w.lower() in self.keys]
        if self.input_emotions:  # add key 'emotion' to key list in case an emotion was mentioned
            word = 'emotion'
            keys.append(self.keys[word])
        keys = sorted(keys, key=lambda k: -k.weight)
        log.debug('Sorted keys: %s', [(k.word, k.weight) for k in keys])

        output = None

        for key in keys:
            output = self._match_key(words, key)
            if output:
                log.debug('Output from key: %s', output)
                break
        if not output:
            if self.memory:
                index = random.randrange(len(self.memory))
                output = self.memory.pop(index)
                log.debug('Output from memory: %s', output)
            else:
                output = self._next_reasmb(self.keys['xnone'].decomps[0])
                log.debug('Output from xnone: %s', output)

        return ' '.join(output)

    def initial(self):
        return random.choice(self.initials)

    def final(self):
        return random.choice(self.finals)

    def emotion(self):
        return self.emotional_eliza.get_emotion()  # retrieve emotion from emotion dynamics
       # return random.choice(self.emotions)  # random emotion for task 2

    def send_impulse(self, impulse, dominance=100):
        output = ''
        emotion_before_impulse = self.emotion()
        self.emotional_eliza.emotional_impulse(impulse)
        self.emotional_eliza.set_dominance(dominance)
        self.emotional_eliza.update_emotions()
        emotion_after_impulse = self.emotion()
        # tell user emotional state after impulse
        if emotion_after_impulse != emotion_before_impulse:  # emotion changed after impulse
            if emotion_after_impulse == 'aengstlich':
                output = 'Das beunruhigt mich'
            elif emotion_after_impulse == 'froehlich':
                output = 'Das freut mich'
            else:
                output = 'Das stimmt mich ' + self.emotion()
        else:  # emotion has not changed
            if emotion_before_impulse == 'aengstlich':
                output = 'Ich bin immer noch beunruhigt'
            elif emotion_after_impulse == 'froehlich':
                output: 'Ich bin immer noch erfreut'
            else:
                output = 'Ich bin immer noch ' + emotion_before_impulse
        return output

    def run(self):
        print(self.initial())

        while True:
            sent = input('> ')

            output = self.respond(sent)
            if output is None:
                break

            print(output)

        print(self.final())


def main():
    eliza = Eliza()

    # start thread continuously updating Eliza's emotions
    thread = threading.Thread(target=eliza.emotional_eliza.update_emotions_continuously)
    thread.daemon = True
    thread.start()

    eliza.load('doctor_de.txt')
    eliza.run()

if __name__ == '__main__':
    logging.basicConfig()
    main()
