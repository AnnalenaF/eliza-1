import random

class EmotionalAgent:
    def __init__(self):
        self.emotionsActive = 0
        self.myEmotionDynamics = EmotionDynamics()
        self.myEmotionConverter = EmotionConverter()
        self.myEmotionDynamics.update()

    def update_emotions(self):
        self.myEmotionDynamics.update()
        self.myEmotionConverter.get_emotion(self.myEmotionConverter.convert_to_class_type(self.myEmotionDynamics.get_emotion_list()))

    def update_emotions_continuously(self):
        while True: #update emotional state every 2 seconds
            self.update_emotions()
            sleep(2)


    def random_emotional_impulse(self):
        emoimp = random.randint(0, 50) - 25
        self.myEmotionDynamics.emotional_impulse(emoimp)      

    def emotional_impulse(self, impulse):
        self.myEmotionDynamics.emotional_impulse(impulse)

    def get_emotion(self):
        return self.myEmotionConverter.s

class EmotionDynamics:
    def __init__(self):
        self.mass = 1000
        self.sxlast = self.sylast = self.sxt = self.syt = 0
        self.sdom = self.sdomlast = 100
        self.vxlast = self.vylast = self.vxt = self.vyt = self.vdom = self.vdomlast = 0
        self.axlast = self.aylast = self.axt = self.ayt = self.adom = self.adomlast = 0
        self.dt = 0.1 #10 Hz!
        self.z = 0
        self.xSignChange = 0
        self.ySignChange = 0
        self.xSign = self.ySign = 0
        self.xTens = 50
        self.yTens = 10
        self.xReg = 1
        self.yReg = 1
        self.slope = 500 # 500% equals 5!
        self.boredom = 10 # ???
    
    def update(self):
        self.Fx = -self.xTens * self.sxlast
        self.Fy = -self.yTens * self.sylast
        self.axt = self.Fx / self.mass
        self.vxt = self.axt * self.dt + self.vxlast
        self.sxt = self.vxt * self.dt + self.sxlast
        if ((self.sxt > 0 and self.sxlast < 0) or (self.sxt < 0 and self.sxlast > 0)):
            self.sxt = self.sxlast = 0
            self.vxlast = 0
            self.axlast = 0
        else:
            self.vxlast = self.vxt
            self.axlast = self.axt
            self.sxlast = self.sxt
        self.ayt = self.Fy / self.mass
        self.vyt = self.ayt * self.dt + self.vylast
        self.syt = self.vyt * self.dt + self.sylast
        self.syt += self.sxt * (self.slope / 100) / self.mass
        if ((self.syt > 0 and self.sylast < 0) or (self.syt < 0 and self.sylast > 0)):
            self.syt = self.sylast = 0
            self.vylast = 0
            self.aylast = 0
        else:
            self.vylast = self.vyt
            self.aylast = self.ayt
            self.sylast = self.syt

        if (self.sxt > 100): self.sxt = 100
        if (self.syt > 100): self.syt = 100
        if (self.sxt < -100): self.sxt = -100
        if (self.syt < -100): self.syt = -100

        if (self.sxt < self.xReg and self.syt < self.yReg and self.sxt > -self.xReg and self.syt > -self.yReg):
            if (self.z > -100): self.z -= self.boredom / 1000
        else: self.z = 0
        #print "(x $sxt) (y $syt) (z $z)". 
    
    def get_dt(self):
        return self.dt

    def emotional_impulse(self, impulse):
        self.axt = self.axlast = self.vxt = self.vxlast = self.ayt = self.aylast = self.vyt = self.vylast = 0
        self.sxlast += impulse
        if self.sxlast > 100: 
            self.sxlast = 100	
        if self.sxlast < -100: 
            self.sxlast = -100
        self.sxt += impulse
        if self.sxt > 100: 
            self.sxt = 100
        if self.sxt < -100: 
            self.sxt = -100

    def get_emotion_list(self):
        emotionList = [self.sxt, self.syt, self.z, self.sdom]
        return emotionList

    def set_dominance(self, dominance):
        self.sdom = dominance

class EmotionConverter:
    def __init__(self):
        self.outerRadius = 0.8
        self.innerRadius = 0.4
        self.emoIndex = -1
        self.s = "entspannt"
        self.actualStringConvertElement = [ "entspannt", (0, 0, 1.0) ]
        self.stringConvertList = list() # <(category, [P,A,D]), ..>
        tempList = [ "wuetend", (-0.8, 0.8, 1.0) ] 
        self.stringConvertList.append(tempList) 
        tempList = [ "aengstlich", (-0.8, 0.8, -1.0) ]
        self.stringConvertList.append(tempList) 
        tempList = [ "genervt", (-0.5, 0.0, 1.0) ]
        self.stringConvertList.append(tempList) 
        tempList = [ "traurig", (-0.5, 0.0, 1.0) ]
        self.stringConvertList.append(tempList) 
        tempList = [ "froehlich", (0.5, 0.0, 1.0) ]
        self.stringConvertList.append(tempList) 
        tempList = [ "froehlich", (0.5, 0.0, -1.0) ]
        self.stringConvertList.append(tempList) 
        tempList = [ "froehlich", (0.8, 0.8, 1.0) ]
        self.stringConvertList.append(tempList) 
        tempList = [ "froehlich", (0.8, 0.8, -1.0) ]
        self.stringConvertList.append(tempList) 
        tempList = [ "entspannt", (0.0, 0.0, 1.0) ]
      #  self.stringConvertList.append(tempList) 
      #  tempList = [ "entspannt", (0.0, 0.0, -1.0) ]
        self.stringConvertList.append(tempList) 
        tempList = [ "traurig", (0.0, 0.0, -1.0) ]
        self.stringConvertList.append(tempList) 
        tempList = [ "ueberrascht", (0.1, 0.8, 1.0) ]
        self.stringConvertList.append(tempList) 
        tempList = [ "erschrocken", (0.1, 0.8, -1.0) ]
        self.stringConvertList.append(tempList) 
        tempList = [ "gelangweilt", (-0.5, 0.0, 1.0) ]
        self.stringConvertList.append(tempList) 
        tempList = [ "deprimiert", (-0.5, 0.0, 1.0) ] 
        self.stringConvertList.append(tempList) 
        tempList = [ "neutral", (0.0, 0.0, 0.0) ]
        self.stringConvertList.append(tempList) 

    def convert_to_class_type(self, list):
        v = (0.0, 0.0, 0.0)
        if len(list) == 4:
            emoX = list[0]
            moodY = list[1]
            boredomZ = list[2]
            dominance = list[3]
            
            v = {}
            x = ((emoX + moodY) / 200)
            y = ( abs(emoX / 100) - abs(boredomZ / 100))
            z = dominance / 100
            v["x"] = x
            v["y"] = y
            v["z"] = z
        return v

    def get_emotion(self, paddata):
        self.s = "neutral"
        self.actualStringConvertElement = {"neutral",(0, 0, 0)}
        emoDistance = 10.0
        for listElement in self.stringConvertList:
            x = abs(paddata["x"] - (listElement[1][0]))
            y = abs(paddata["y"] - (listElement[1][1]))
            z = abs(paddata["z"] - (listElement[1][2]))
            tempDistance = x + y + z
            
            if (tempDistance < emoDistance and tempDistance < self.outerRadius):
                self.actualStringConvertElement = listElement
                self.s = listElement[0]
                emoDistance = tempDistance
        return self.s