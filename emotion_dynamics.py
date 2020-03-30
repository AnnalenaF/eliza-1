"""This module contains the main functionality of the emotion dynamics of WASABI"""
import random
import time


class EmotionalAgent(object):
    """Simulates an emotional agent always having a certain emotional state

    Attributes:
        __emotion_dynamics: An object of type EmotionDynamics which implements the basic WASABI
            emotion dynamics
        __emotion_converter: An object of type EmotionConverter which is able to interpret the
            values of the emotion dynamics to real emotions"""
    def __init__(self):
        self.__emotion_dynamics = EmotionDynamics()
        self.__emotion_converter = EmotionConverter()
        self.__emotion_dynamics.update()

    def update_emotions(self):
        """Updates current emotional state using emotion dynamics"""
        self.__emotion_dynamics.update()

    def update_emotions_continuously(self):
        """Updates current emotional state every 2 seconds"""
        while True:
            self.update_emotions()
            time.sleep(2)

    def random_emotional_impulse(self):
        """Sends random emotional impulse between -25 and 25 to the emotion dynamics"""
        emoimp = random.randint(0, 50) - 25
        self.__emotion_dynamics.emotional_impulse(emoimp)

    def emotional_impulse(self, impulse):
        """Sends emotional impulse to the emotion dynamics

        Args:
            impulse: A float/integer value which should be between -100 and 100 and should not be
                zero
        """
        self.__emotion_dynamics.emotional_impulse(impulse)

    def get_emotion(self):
        """Returns current emotion"""
        emotion_list = self.__emotion_dynamics.get_emotion_list()
        pad_data = self.__emotion_converter.convert_to_class_type(emotion_list)
        return self.__emotion_converter.get_emotion(pad_data)

    def set_dominance(self, dominance):
        """Sets the dominance value of the emotion dynamics instance

        Args:
            dominance: new dominance value between -1.0 and 1.0"""
        self.__emotion_dynamics.set_dominance(dominance)


class EmotionDynamics(object):
    """Implements the basic WASABI emotion dynamics"""
    def __init__(self):
        self.__mass = 1000
        self.__sxlast = self.__sylast = self.__sxt = self.__syt = 0
        self.__sdom = self.__sdomlast = 100
        self.__vxlast = self.__vylast = self.__vxt = self.__vyt = self.__vdom = self.__vdomlast = 0
        self.__axlast = self.__aylast = self.__axt = self.__ayt = self.__adom = self.__adomlast = 0
        self.__dt = 0.1 #10 Hz!
        self.__z = 0
        self.__x_sign_change = 0
        self.__y_sign_change = 0
        self.__x_sign = self.__y_sign = 0
        self.__x_tens = 50
        self.__y_tens = 10
        self.__xreg = 1
        self.__yreg = 1
        self.__slope = 500 # 500% equals 5!
        self.__boredom = 10 # ???

    def update(self):
        """Updates current emotional state"""
        f_x = -self.__x_tens * self.__sxlast
        f_y = -self.__y_tens * self.__sylast
        self.__axt = f_x / self.__mass
        self.__vxt = self.__axt * self.__dt + self.__vxlast
        self.__sxt = self.__vxt * self.__dt + self.__sxlast
        if (self.__sxt > 0 and self.__sxlast < 0) or (self.__sxt < 0 and self.__sxlast > 0):
            self.__sxt = self.__sxlast = 0
            self.__vxlast = 0
            self.__axlast = 0
        else:
            self.__vxlast = self.__vxt
            self.__axlast = self.__axt
            self.__sxlast = self.__sxt
        self.__ayt = f_y / self.__mass
        self.__vyt = self.__ayt * self.__dt + self.__vylast
        self.__syt = self.__vyt * self.__dt + self.__sylast
        self.__syt += self.__sxt * (self.__slope / 100) / self.__mass
        if (self.__syt > 0 and self.__sylast < 0) or (self.__syt < 0 and self.__sylast > 0):
            self.__syt = self.__sylast = 0
            self.__vylast = 0
            self.__aylast = 0
        else:
            self.__vylast = self.__vyt
            self.__aylast = self.__ayt
            self.__sylast = self.__syt
        if self.__sxt > 100:
            self.__sxt = 100
        if self.__syt > 100:
            self.__syt = 100
        if self.__sxt < -100:
            self.__sxt = -100
        if self.__syt < -100:
            self.__syt = -100

        if (self.__sxt < self.__xreg and self.__syt < self.__yreg and self.__sxt > -self.__xreg and
                self.__syt > -self.__yreg):
            if self.__z > -100:
                self.__z -= self.__boredom / 1000
        else: self.__z = 0

    def emotional_impulse(self, impulse):
        """Processes emotional impulse by translating it to parameters of the emotion dynamics

        Args:
            impulse: emotional impulse value between -100 and 100"""
        self.__axt = self.__axlast = self.__vxt = self.__vxlast = 0
        self.__ayt = self.__aylast = self.__vyt = self.__vylast = 0
        self.__sxlast += impulse
        if self.__sxlast > 100:
            self.__sxlast = 100
        if self.__sxlast < -100:
            self.__sxlast = -100
        self.__sxt += impulse
        if self.__sxt > 100:
            self.__sxt = 100
        if self.__sxt < -100:
            self.__sxt = -100

    def get_emotion_list(self):
        """Returns list of value indicating emotional state"""
        emotion_list = [self.__sxt, self.__syt, self.__z, self.__sdom]
        return emotion_list

    def set_dominance(self, dominance):
        """Sets the dominance attribute of the emotion dynamics to the given value

        Args:
            dominance: new dominance value between -1.0 and 1.0, should not be zero"""
        self.__sdom = dominance


class EmotionConverter(object):
    """Is able to interpret the values of the emotion dynamics to real emotions"""
    def __init__(self):
        self.__outer_radius = 0.8
        self.__inner_radius = 0.4
        self.__s = 'entspannt'
        self.__actual_string_convert_element = ['entspannt', (0.0, 0.0, 1.0)]
        self.__string_convert_list = list() # <(category, [P,A,D]), ..>
        temp_list = ['aergerlich', (-0.8, 0.8, 1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['aengstlich', (-0.8, 0.8, -1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['genervt', (-0.5, 0.0, 1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['traurig', (-0.5, 0.0, -1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['froehlich', (0.5, 0.0, 1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['froehlich', (0.5, 0.0, -1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['froehlich', (0.8, 0.8, 1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['froehlich', (0.8, 0.8, -1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['entspannt', (0.0, 0.0, 1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['entspannt', (0.0, 0.0, -1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['ueberrascht', (0.1, 0.8, 1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['erschrocken', (0.1, 0.8, -1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['gelangweilt', (0, -0.8, 1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['deprimiert', (0, -0.8, -1.0)]
        self.__string_convert_list.append(temp_list)
        temp_list = ['neutral', (0.0, 0.0, 0.0)]
        self.__string_convert_list.append(temp_list)

    def convert_to_class_type(self, foreign_data):
        """Converts values for emotion, mood, boredom and dominance to PAD Data

        Args:
            foreign_data: list containing 4 int values: emotion, mood, boredom, dominance"""
        vector = (0.0, 0.0, 0.0)
        if len(foreign_data) == 4:
            emo_x = foreign_data[0]
            mood_y = foreign_data[1]
            boredom_z = foreign_data[2]
            dominance = foreign_data[3]
            vector = {}
            val_x = ((emo_x + mood_y) / 200)
            val_y = (abs(emo_x / 100) - abs(boredom_z / 100))
            val_z = dominance / 100
            vector['x'] = val_x
            vector['y'] = val_y
            vector['z'] = val_z
        return vector

    def get_emotion(self, paddata):
        """Determines and returns current emotional state as string

        Args:
            paddata: PAD Data vector with x, y, z values"""
        self.__s = 'neutral'
        self.__actual_string_convert_element = {'neutral', (0, 0, 0)}
        emo_distance = 10.0
        for list_element in self.__string_convert_list:
            dist_x = abs(paddata['x'] - list_element[1][0])
            dist_y = abs(paddata['y'] - list_element[1][1])
            dist_z = abs(paddata['z'] - list_element[1][2])
            temp_distance = dist_x + dist_y + dist_z
            if temp_distance < emo_distance and temp_distance < self.__outer_radius:
                self.__actual_string_convert_element = list_element
                self.__s = list_element[0]
                emo_distance = temp_distance
        return self.__s
