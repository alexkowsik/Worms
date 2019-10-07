import sys
from PyQt5 import QtWidgets as qw
from PyQt5 import QtGui as qg
from PyQt5 import QtCore as qc
import random



class SNAKE(qw.QWidget):

    GSF = qg.QFont('Comic Sans MS', 12)     # GLOBAL_STANDARD_FONT
    SBS = (250, 50)                         # STANDARD_BUTTON_SIZE
    SWS = [800, 600]                        # STANDARD_WINDOW_SIZE

    logo = None
    duct_tape = None

    def __init__(self):
        super(SNAKE, self).__init__()

    def start(self):
        print("initializing snake...")

        self.duct_tape = Controller()
        self.duct_tape.widgetList.append(Home(self.duct_tape))
        self.duct_tape.currently_active = self.duct_tape.widgetList[0]
        self.duct_tape.widgetList.append(Settings(self.duct_tape))
        self.duct_tape.widgetList.append(Highscores(self.duct_tape, True))
        self.duct_tape.widgetList.append(Credits(self.duct_tape))
        self.duct_tape.widgetList.append(FlexTape(self.duct_tape, True))
        self.duct_tape.currently_active = self.duct_tape.widgetList[0]
        self.duct_tape.currently_active.show()

    def setupLayout(self):

        # setup window frame
        self.setWindowTitle("- henlo, I ams smol snek")
        self.setWindowIcon(qg.QIcon("resources/tank_icon.png"))

        # setup window pos and size
        self.resize(self.SWS[0], self.SWS[1])
        self.center()


        # setup background
        background = qw.QLabel(self)
        background.setGeometry(0, 0, self.window().frameGeometry().width(), self.window().frameGeometry().height())
        memeBackground = qg.QPixmap("resources/worms_logo.jpg")
        scaledMeme = memeBackground.scaled(background.size())
        background.setPixmap(scaledMeme)

        # setup logo
        self.logo = qw.QLabel()
        self.logo.resize(self.SBS[0], self.SBS[0])
        solidSnake = qg.QPixmap("resources/tank_icon.png")
        self.logo.setPixmap(solidSnake.scaled(self.logo.size(), qc.Qt.KeepAspectRatio))
        splashtexts = ['handmade!',
                       'contains duct tape',
                       'like and subscribe',
                       'sub2pewds',
                       'it is i, smol snek!',
                       'Ssssss',
                       'gets better every time!',
                       'SOLID',
                       '0% snake oil',
                       'this code is the\nliving reincarnation of\nhis noodly appendange,\nthe flying spaghettimonster',
                       'contains flex tape',
                       'Phil Swift approves',
                       'Oooof!',
                       'may cause autism']
        rand = random.randint(0, len(splashtexts) - 1)
        self.logo.setToolTip(splashtexts[rand])

    def center(self):
        fg = self.frameGeometry()
        centrum = qw.QDesktopWidget().availableGeometry().center()
        fg.moveCenter(centrum)
        self.move(fg.topLeft())

    def build_shadow():  # STANDARD_TEXT_SHADOW
        STS = qw.QGraphicsDropShadowEffect()
        STS.setColor(qc.Qt.black)
        STS.setBlurRadius(1)
        STS.setOffset(1.5, 1.5)
        return STS

    def quitGame(self):
        choice = qw.QMessageBox.question(self, "Quit Game",
                                         "Are you sure?",
                                         qw.QMessageBox.Yes | qw.QMessageBox.No)

        if choice == qw.QMessageBox.Yes:
            print("exiting game...")
            qc.QCoreApplication.instance().quit()
        else:
            pass

    def keyPressEvent(self, event):
        key = event.key()
        if key == qc.Qt.Key_Escape:
            self.duct_tape.tapeToHome()
        else:
            pass


class Home(SNAKE):

    nameSetBySettings = False
    name_list = [' ', ' ', ' ', ' ', ' ']
    score_list = [0, 0, 0, 0, 0]
    playerindex = 0
    # highscore variables here since flextape, game and highscores will be reinstaciated

    def __init__(self, controller):
        self.duct_tape = controller
        print("initializing home ...")
        super(Home, self).__init__()
        self.setupLayout()
        self.setupHome()

    def setupHome(self):
        buttonList = []

        settingsBTN = qw.QPushButton("Settings", self)
        buttonList.append(settingsBTN)
        settingsBTN.clicked.connect(self.duct_tape.tapeToSettings)

        playBTN = qw.QPushButton("PLAY", self)
        buttonList.append(playBTN)
        playBTN.clicked.connect(self.duct_tape.tapeToGame)

        highscoreBTN = qw.QPushButton("Highscores", self)
        buttonList.append(highscoreBTN)
        highscoreBTN.clicked.connect(self.duct_tape.tapeToHighscores)

        creditsBTN = qw.QPushButton("Credits", self)
        buttonList.append(creditsBTN)
        creditsBTN.clicked.connect(self.duct_tape.tapeToCredits)

        quitBTN = qw.QPushButton("quit", self)
        buttonList.append(quitBTN)
        quitBTN.clicked.connect(self.quitGame)
        quitBTN.setToolTip('nono, stay pls!')

        easteregg = qw.QLabel(self)
        easteregg.setGeometry(500, 500, 100, 100)
        easteregg.setToolTip('E4STEREGG')
        # img = qg.QImage(self.width(), self.height(), qg.QImage.Format_RGBA8888)
        # img.fill(qc.Qt.white)
        # easteregg.setPixmap(qg.QPixmap.fromImage(img))

        for btn in buttonList:
            if btn != playBTN:
                btn.setFixedSize(self.SBS[0], self.SBS[1])
                btn.setFont(self.GSF)
            else:
                btn.setFixedSize(250, 100)
                btn.setFont(qg.QFont('Comic Sans MS', 20))
                btn.setToolTip('play with classic settings')

        vLayout = qw.QVBoxLayout()
        vLayout.addWidget(self.logo)
        vLayout.addStretch()
        vLayout.addWidget(settingsBTN)
        vLayout.addWidget(playBTN)
        vLayout.addWidget(highscoreBTN)
        vLayout.addWidget(creditsBTN)
        vLayout.addStretch()
        vLayout.addWidget(quitBTN)

        hLayout = qw.QHBoxLayout()
        hLayout.addStretch()
        hLayout.addLayout(vLayout)
        hLayout.addStretch()

        self.setLayout(hLayout)

    def keyPressEvent(self, event):
        key = event.key()
        if key == qc.Qt.Key_Escape:
            self.quitGame()
        else:
            pass



class Settings(SNAKE):

    # ------------Pics und Graphic effects------------------
    gamesize_dropdown = None
    zoom_dropdown = None
    speedup_dropdown = None
    initspeed_dropdown = None
    border_checkbox = None
    player_name = None

    def __init__(self, controller):
        self.duct_tape = controller
        print("initializing settings...")
        super(Settings, self).__init__()
        self.setupLayout()

        # ------------create widgets---------------

        # 1st row: enter name
        player_name_lbl = qw.QLabel("<font color = white>enter your name here!</font>")

        # input line
        self.player_name = qw.QLineEdit()
        self.player_name.setMaxLength(16)
        self.player_name.setPlaceholderText("name")
        self.player_name.setMaximumWidth(180)

        # 2nd row:
        gamesize_lbl = qw.QLabel()
        gamesize_lbl.setText("<font color='white'>choose your game size!</font>")

        self.gamesize_dropdown = qw.QComboBox()
        self.gamesize_dropdown.addItems(['10x10', '12x12', '16x16', '20x20', '32x32', '50x50', '64x64', '80x80', '90x90', '100x100', '128x128'])
        self.gamesize_dropdown.setCurrentIndex(4)

        # 3rd row:
        # zoom_lbl = qw.QLabel()
        # zoom_lbl.setText("<font color='white'>select zoom factor!</font>")
        #
        # self.zoom_dropdown = qw.QComboBox()
        # self.zoom_dropdown.addItems(['auto', '4 px', '8 px', '16 px', '32 px', '64 px'])
        # cancelled mid-development

        # 4th row:
        initspeed_lbl = qw.QLabel()
        initspeed_lbl.setText("<font color='white'>set initial speed!</font>")

        self.initspeed_dropdown = qw.QComboBox()
        self.initspeed_dropdown.addItems(['0,5x', '1x', '1.5x', '2x', '2.5x', '3x'])
        self.initspeed_dropdown.setCurrentIndex(1)

        # 5th row:
        speedup_lbl = qw.QLabel()
        speedup_lbl.setText("<font color='white'>set speedup!</font>")

        self.speedup_dropdown = qw.QComboBox()
        self.speedup_dropdown.addItems(['none (lame)', 'python runtime speed', 'trabbi', 'slow', 'medium', 'between medium and fast', 'gotta go fast', 'european extreme'])
        self.speedup_dropdown.setCurrentIndex(3)

        # 6th row:
        border_lbl = qw.QLabel()
        border_lbl.setText("<font color='white'>border?</font>")

        self.border_checkbox = qw.QCheckBox()
        self.border_checkbox.setChecked(False)

        # back button
        back_button = qw.QPushButton()
        back_button.setText("back")
        back_button.clicked.connect(self.saveNameHome)
        back_button.setFixedSize(SNAKE.SBS[0], SNAKE.SBS[1])

        # play button
        play_button = qw.QPushButton('PLAY!')
        play_button.setFixedSize(SNAKE.SBS[0], SNAKE.SBS[1])
        play_button.clicked.connect(self.saveNameGame)

        # ------------ Layouts udn Widgets einfügen-----------------
        # erstelle eine vbox mit 2 reihen. 1. reihe ist der header und 2. reihe das grid linksbündig
        grid = qw.QGridLayout()
        vbox = qw.QVBoxLayout()
        hbox = qw.QHBoxLayout()
        hbox2 = qw.QHBoxLayout()

        # Grundstruktur

        vbox.addLayout(hbox)
        vbox.addStretch()

        # 1. Reihe mit header
        hbox.addStretch()
        hbox.addWidget(self.logo)
        hbox.addStretch()

        # 2.reihe mit dem grid und nem Stretch
        vbox.addLayout(hbox2)
        hbox2.addStretch()
        hbox2.addLayout(grid)
        hbox2.addStretch()
        vbox.addStretch()

        # befülle das grid.
        konfigList = [player_name_lbl, self.player_name, gamesize_lbl, self.gamesize_dropdown,
                      initspeed_lbl, self.initspeed_dropdown,
                      speedup_lbl, self.speedup_dropdown, border_lbl,
                      self.border_checkbox, back_button, play_button]

        shadowlist = []
        for i in konfigList:
            if not isinstance(i, qw.QCheckBox):
                i.setFont(SNAKE.GSF)
                if not isinstance(i, qw.QComboBox):
                    temp = SNAKE.build_shadow()
                    shadowlist.append(temp)
                    i.setGraphicsEffect(temp)

        # befülle das grid.
        for i in range(len(konfigList)):
            grid.addWidget(konfigList[i], i // 2, i % 2)

        self.setLayout(vbox)

    def saveNameHome(self):
        if len(self.player_name.text()) > 0:
            self.duct_tape.widgetList[0].name_list[self.duct_tape.widgetList[0].playerindex] = self.player_name.text()
            self.duct_tape.widgetList[0].nameSetBySettings = True
        self.duct_tape.tapeToHome()

    def saveNameGame(self):
        if len(self.player_name.text()) > 0:
            self.duct_tape.widgetList[0].name_list[self.duct_tape.widgetList[0].playerindex] = self.player_name.text()
            self.duct_tape.widgetList[0].nameSetBySettings = True
        self.duct_tape.tapeToGame()

    def keyPressEvent(self, event):
        key = event.key()
        if key == qc.Qt.Key_Return:
            self.saveNameGame()
        elif key == qc.Qt.Key_Escape:
            self.saveNameHome()
        else:
            pass


class Game:


    def __init__(self, controller):
        print('hatching smol snek...')
        self.duct_tape = controller

        self.display = qw.QLabel()
        self.display.setFixedSize(800, 800)
        self.display.keyPressEvent = self.keyPressEvent
        self.display.setWindowTitle("- henlo, I ams smol snek")
        self.display.setWindowIcon(qg.QIcon("resources/tak_icon.png"))
        fg = self.display.frameGeometry()
        centrum = qw.QDesktopWidget().availableGeometry().center()
        fg.moveCenter(centrum)
        self.display.move(fg.topLeft())


        self.width = self.display.frameGeometry().width()
        self.height = self.width
        self.display.show()
        print("ok")




    def keyPressEvent(self, event):
        key = event.key()
        if key == qc.Qt.Key_Up and self.direction != 3:
            self.lastKey = 1
        elif key == qc.Qt.Key_Right and self.direction != 4:
            self.lastKey = 2
        elif key == qc.Qt.Key_Down and self.direction != 1:
            self.lastKey = 3
        elif key == qc.Qt.Key_Left and self.direction != 2:
            self.lastKey = 4
        elif key == qc.Qt.Key_Escape:
            self.exitGame(False)
        else:
            pass
            # super().keyPressEvent(event)

    def exitGame(self, ended):
        if not ended:
            self.timer.stop()
            choice = qw.QMessageBox.question(self.display, "Exit Game",
                                             "Exit running Game?",
                                             qw.QMessageBox.Yes | qw.QMessageBox.No)

            if choice == qw.QMessageBox.Yes:
                self.duct_tape.tapeGameToHome(self)
            else:
                self.timer.start()
        else:
            print("flextaping...")
            if self.duct_tape.widgetList[0].playerindex <= 5:
                self.duct_tape.widgetList[0].score_list[self.duct_tape.widgetList[0].playerindex] = "<font color = white>" + str(self.points) + "</font>"
            self.duct_tape.flextape(self)


class Highscores(SNAKE):

    namelist = []
    scorelist = []

    def __init__(self, controller, first):
        self.duct_tape = controller
        if first:
            print("initializing highscores ...")
        super(Highscores, self).__init__()
        self.setupLayout()
        self.setupHighscores()

    def setupHighscores(self):

        head = qw.QLabel('<font color=white>HIGHSCORES:</font>')
        head.setFont(qg.QFont('Comic Sans MS', 20))
        temp = SNAKE.build_shadow()
        head.setGraphicsEffect(temp)

        shadowlist = []
        for i in range(5):
            currentname = self.duct_tape.widgetList[0].name_list[i]
            temp1 = qw.QLabel()
            temp2 = SNAKE.build_shadow()
            shadowlist.append(temp2)
            self.namelist.append(temp1)
            self.namelist[i].setGraphicsEffect(shadowlist[i])
            self.namelist[i].setFont(SNAKE.GSF)
            if currentname != ' ':                    #check if name is still dummy
                self.namelist[i].setText(currentname)
                if len(currentname)-25 > 10:          #check if name without color syntax is longer than 12
                    self.namelist[i].setFont(qg.QFont('Comic Sans MS', 8))


        for i in range(5):
            temp1 = qw.QLabel()
            temp2 = SNAKE.build_shadow()
            shadowlist.append(temp2)
            self.scorelist.append(temp1)
            self.scorelist[i].setGraphicsEffect(shadowlist[i+5])
            self.scorelist[i].setFont(SNAKE.GSF)
            if self.duct_tape.widgetList[0].name_list[i] != ' ':                    # check if name is still dummy
                self.scorelist[i].setText(self.duct_tape.widgetList[0].score_list[i])
                if len(self.duct_tape.widgetList[0].score_list[i])-25 > 12:
                    self.scorelist[i].setFont(qg.QFont('Comic Sans MS', 8))

        returnBTN = qw.QPushButton("back", self)
        returnBTN.clicked.connect(self.duct_tape.tapeToHome)
        returnBTN.setFixedSize(self.SBS[0], self.SBS[1])
        returnBTN.setFont(self.GSF)

        h2Layout = qw.QHBoxLayout()
        h2Layout.addWidget(self.namelist[0])
        h2Layout.addWidget(self.scorelist[0])

        h3Layout = qw.QHBoxLayout()
        h3Layout.addWidget(self.namelist[1])
        h3Layout.addWidget(self.scorelist[1])

        h4Layout = qw.QHBoxLayout()
        h4Layout.addWidget(self.namelist[2])
        h4Layout.addWidget(self.scorelist[2])

        h5Layout = qw.QHBoxLayout()
        h5Layout.addWidget(self.namelist[3])
        h5Layout.addWidget(self.scorelist[3])

        h6Layout = qw.QHBoxLayout()
        h6Layout.addWidget(self.namelist[4])
        h6Layout.addWidget(self.scorelist[4])

        vLayout = qw.QVBoxLayout()
        vLayout.addWidget(self.logo)
        vLayout.addStretch()
        vLayout.addWidget(head)
        vLayout.addStretch()
        vLayout.addLayout(h2Layout)
        vLayout.addLayout(h3Layout)
        vLayout.addLayout(h4Layout)
        vLayout.addLayout(h5Layout)
        vLayout.addLayout(h6Layout)
        vLayout.addStretch()
        vLayout.addWidget(returnBTN)

        hLayout = qw.QHBoxLayout()
        hLayout.addStretch()
        hLayout.addLayout(vLayout)
        hLayout.addStretch()

        self.setLayout(hLayout)

    def keyPressEvent(self, event):
        key = event.key()
        if (key == qc.Qt.Key_Escape) | (key == qc.Qt.Key_Return):
            self.duct_tape.tapeToHome()
        else:
            pass



class Credits(SNAKE):

    def __init__(self, controller):
        self.duct_tape = controller
        print("initializing credits ...")
        super(Credits, self).__init__()
        self.setupLayout()
        self.setupCredits()

    def setupCredits(self):

        widgetlist = []

        AK = qw.QLabel('<font color=white>Alex Kowsik</font>')
        widgetlist.append(AK)
        DK = qw.QLabel('<font color=white>Daniel Klima</font>')
        widgetlist.append(DK)
        PF = qw.QLabel('<font color=white>Philipp Freundlieb</font>')
        widgetlist.append(PF)
        snek = qw.QLabel('<font color=white>...and smol snek</font>')
        widgetlist.append(snek)
        ah = qw.QLabel('<font color=white>as himself</font>')
        widgetlist.append(ah)

        returnBTN = qw.QPushButton("back", self)
        returnBTN.clicked.connect(self.duct_tape.tapeToHome)
        returnBTN.setFixedSize(self.SBS[0], self.SBS[1])
        returnBTN.setFont(self.GSF)

        vLayout = qw.QVBoxLayout()
        vLayout.addWidget(self.logo)
        vLayout.addStretch()
        for lable in widgetlist:
            if (lable == snek) | (lable == ah):
                if lable == snek:
                    vLayout.addStretch()
                    lable.setFont(qg.QFont('Comic Sans MS', 14))
                else:
                    lable.setFont(qg.QFont('Comic Sans MS', 11))
            else:
                lable.setFont(qg.QFont('Comic Sans MS', 18))
            temp = SNAKE.build_shadow()
            lable.setGraphicsEffect(temp)
            vLayout.addWidget(lable)
        vLayout.addStretch()
        vLayout.addWidget(returnBTN)

        hLayout = qw.QHBoxLayout()
        hLayout.addStretch()
        hLayout.addLayout(vLayout)
        hLayout.addStretch()

        self.setLayout(hLayout)


class FlexTape(SNAKE):

    game = None
    player_text = None
    playerName = None

    def __init__(self, controller, first):
        self.duct_tape = controller
        print('summoning' + (' ' if first else ' more ') + 'flextape')
        super(FlexTape, self).__init__()
        self.setupLayout()
        self.setupFlexTape()

    def setupFlexTape(self,):

        gameOverLBL = qw.QLabel('<font color=white>GAME OVER</font>')
        gameOverLBL.setFont(qg.QFont('Comic Sans MS', 20))
        temp1 = SNAKE.build_shadow()
        gameOverLBL.setGraphicsEffect(temp1)

        saveLBL = qw.QLabel('<font color=white>save game:</font>')
        saveLBL.setFont(qg.QFont('Comic Sans MS', 16))
        temp2 = SNAKE.build_shadow()
        saveLBL.setGraphicsEffect(temp2)

        self.player_text = qw.QLineEdit()
        self.player_text.setMaxLength(20)
        if self.duct_tape.widgetList[0].nameSetBySettings:
            self.player_text.setText(self.duct_tape.widgetList[0].name_list[self.duct_tape.widgetList[0].playerindex])
        else:
            self.player_text.setPlaceholderText("name")
        self.player_text.setMaximumWidth(180)

        saveBTN = qw.QPushButton("save game", self)
        saveBTN.clicked.connect(self.saveGame)
        saveBTN.setFixedSize(self.SBS[0], self.SBS[1])
        saveBTN.setFont(self.GSF)

        homeBTN = qw.QPushButton("home", self)
        homeBTN.clicked.connect(self.dontSave)
        homeBTN.setFixedSize(self.SBS[0], self.SBS[1])
        homeBTN.setFont(self.GSF)

        endBTN = qw.QPushButton("quit", self)
        endBTN.clicked.connect(self.quitGame)
        endBTN.setFixedSize(self.SBS[0], self.SBS[1])
        endBTN.setFont(self.GSF)

        v2Layout = qw.QVBoxLayout()
        v2Layout.addWidget(gameOverLBL)
        v2Layout.addStretch()
        v2Layout.addWidget(saveLBL)
        v2Layout.addWidget(self.player_text)

        h2Layout = qw.QHBoxLayout()
        h2Layout.addStretch()
        h2Layout.addLayout(v2Layout)
        h2Layout.addStretch()

        vLayout = qw.QVBoxLayout()
        vLayout.addWidget(self.logo)
        vLayout.addStretch()
        vLayout.addLayout(h2Layout)
        vLayout.addWidget(saveBTN)
        vLayout.addWidget(homeBTN)
        vLayout.addWidget(endBTN)

        hLayout = qw.QHBoxLayout()
        hLayout.addStretch()
        hLayout.addLayout(vLayout)
        hLayout.addStretch()

        hLayout.setSizeConstraint(qw.QLayout.SetFixedSize)
        self.setFixedSize(250, 450)     # hardcoded, because minimumSize() of hLayout returns 150 for height :(
        self.center()

        self.setLayout(hLayout)

    def dontSave(self):
        choice = qw.QMessageBox.question(self, "going Home",
                                         "End Game without saving?",
                                         qw.QMessageBox.Yes | qw.QMessageBox.No)

        if choice == qw.QMessageBox.Yes:
            self.duct_tape.widgetList[0].nameSetBySettings = False  # reset Flag for next player
            self.duct_tape.flexToHome()
            self.game.display.close()
        else:
            pass

    def nameValid(self):
        self.playerName = self.player_text.text()
        if self.duct_tape.widgetList[0].nameSetBySettings:
            if ((self.playerName != self.duct_tape.widgetList[0].name_list[self.duct_tape.widgetList[0].playerindex]) &
                ((len(self.playerName) < 1) | (self.playerName == ' '))):   # if player changed settings name and new name is invalid
                self.player_text.setPlaceholderText('invalid name')
                return False
            else:       # player did not change settings name or changed it to valid name
                return True
        else:   # no name entered in settings
            if (len(self.playerName) > 1) & (not self.playerName == ' '):
                return True
            else:
                self.player_text.setPlaceholderText('invalid name')
                return False

    def saveGame(self):
        if self.nameValid():
            self.duct_tape.widgetList[0].nameSetBySettings = False  # reset Flag for next player
            if self.duct_tape.widgetList[0].playerindex <= 5:
                self.duct_tape.widgetList[0].name_list[self.duct_tape.widgetList[0].playerindex] = "<font color = white>" + self.playerName + "</font>"
                print(self.playerName + '`s score was added to highscores')
                if self.duct_tape.widgetList[0].playerindex != 5:
                    self.duct_tape.widgetList[0].playerindex += 1
            self.game.display.close()
            self.duct_tape.flexToHighscores()

    def keyPressEvent(self, event):
        key = event.key()
        if key == qc.Qt.Key_Return:
            self.saveGame()
        elif key == qc.Qt.Key_Escape:
            self.dontSave()
        else:
            pass


class Controller:

    widgetList = []
    currently_active = None

    def __init__(self):
        print('summoning duct tape')
    # everything needed is done in SNAKE.start() to prevent recursive __init__ calls

    def tapeToHome(self):
        temp = self.currently_active
        self.currently_active = self.widgetList[0]
        self.currently_active.show()
        temp.close()

    def tapeToSettings(self):
        temp = self.currently_active
        self.currently_active = self.widgetList[1]
        self.currently_active.show()
        temp.hide()

    def tapeToGame(self):
        temp = self.currently_active
        temp.hide()
        Game(self)
        self.widgetList[4] = FlexTape(self, False)

    def tapeToHighscores(self):
        temp = self.currently_active
        self.currently_active = self.widgetList[2]
        self.currently_active.show()
        temp.close()

    def tapeToCredits(self):
        temp = self.currently_active
        self.currently_active = self.widgetList[3]
        self.currently_active.show()
        temp.hide()

    def tapeGameToHome(self, gameInstance):
        self.currently_active = self.widgetList[0]
        self.currently_active.show()
        gameInstance.display.close()

    def flextape(self, gameInstance):
        self.currently_active = self.widgetList[4]
        self.currently_active.game = gameInstance
        self.currently_active.show()

    def flexToHome(self):
        temp = self.currently_active
        self.currently_active = self.widgetList[0]
        self.currently_active.show()
        temp.close()

    def flexToHighscores(self):
        self.widgetList[2] = Highscores(self, False)
        temp = self.currently_active
        self.currently_active = self.widgetList[2]
        self.currently_active.show()
        temp.close()


def run():
    app = qw.QApplication(sys.argv)
    window = SNAKE()
    window.start()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()

