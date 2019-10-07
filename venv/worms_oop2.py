import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np
import random
from math import pi
import time
import skfmm
import matplotlib.pyplot as plt


WIDTH = 1200
HEIGHT = 600

# this version uses consitent angle measurements (degrees):
#     180
#      |
# 90  -+-  270
#      |
#      0
# this version uses player objects and parametric functions for scalability
# this version uses a main game loop for easy rendering


class Worms:
    def __init__(self):

        self.display = QLabel()
        self.display.setMouseTracking(True)
        self.display.mouseMoveEvent = self.mouse_move_event
        self.display.mousePressEvent = self.mouse_press_event  # Klick wechselt Spieler

        self.W = np.linspace(0.001, 0.05, 20)  # W war vorgegeben
        self.curve = self.create_curve()

        # self.timer = QTimer()
        # self.timer.timeout.connect(self.animation)

        self.mousePos = None
        self.player1Pos = QPoint(200, self.curve[200])
        self.player2Pos = QPoint(1000, self.curve[1000])
        self.currentPlayer = Player(0)
        self.currentPlayer.setPlayerPos(tuple([200, self.curve[200]]))
        self.entitylist = []
        self.entitylist.append(self.currentPlayer)

        self.worldImg = self.create_world_image()  # das Bild, das immer erhalten und bemalt wird
        self.worldImgFrozen = self.worldImg.copy()  # s. unten
        self.mappainter = QPainter(self.worldImg)
        self.mappainter.setRenderHint(QPainter.Antialiasing)

        # self.charsImg = self.create_chars_image()
        # self.canonImg1 = self.create_canon_image(1)
        # self.canonImg2 = self.create_canon_image(2)

        # self.bulletImg = self.create_bullet_image()
        # self.bulletPos = self.player1Pos

        # self.make_crater(500, 50)  # demo: x = 500, radius = 50
        # self.draw_chars_img()
        # self.redraw_canons(self.player1Pos.x(), self.player1Pos.y())

        # self.travel_rate = 3  # makes bullet travel every xth frame when rate is 1/x
        # self.frame_count = self.travel_rate

        # img = self.worldImgFrozen.copy()  # die frozen Kopie, damit die Kanonenpositionen erhalten bleiben
        # self.display.setPixmap(QPixmap.fromImage(self.worldImg))
        # self.display.show()
        # self.display.setPixmap(QPixmap.fromImage(self.worldImg))
        # self.display.show()
        self.draw(self.entitylist)

    def draw(self, entitielist):
        debug = False

        a = 0

        background = QPixmap.fromImage(self.worldImgFrozen.copy())
        mainpainter = QPainter(background)
        mainpainter.setRenderHint(QPainter.Antialiasing)
        mainpainter.setCompositionMode(QPainter.CompositionMode_SourceOver)



        # while True:

        a += 1
        print('processing...['+str(a)+']')

        time.sleep(1/60)

        # for entity in entitielist:

        qpoint = QPoint(self.currentPlayer.pos[0]-31, self.currentPlayer.pos[1]-15)
        # tempimage = self.currentPlayer.draw()
        # mainpainter.drawImage(qpoint, tempimage)
        test = QPixmap('resources/tank.png').scaled(72, 30, Qt.KeepAspectRatio)
        mainpainter.drawPixmap(qpoint, test)

        if debug:
            mainpainter.setBrush(Qt.red)
            mainpainter.drawText(self.currentPlayer.pos[0], self.currentPlayer.pos[1], '+')

        mainpainter.translate(self.currentPlayer.pos[0]+4, self.currentPlayer.pos[1]-10)
        mainpainter.rotate(self.currentPlayer.aimAngel)

        color = QColor("#788E2D")
        mainpainter.setPen(color)
        mainpainter.setBrush(color)
        mainpainter.drawRect(0, 0, 4, 30)

        self.display.setPixmap(background)
        self.display.show()

        mainpainter.end()


    def create_curve(self):
        random1 = [random.uniform(0, 2 * pi) for _ in range(len(self.W))]
        random2 = [random.uniform(-1, 1) for _ in range(len(self.W))]
        return [self.get_curve_fx(i, random1, random2) for i in range(WIDTH)]

    # liefert für x den Wert f(x) der Kurve für die Landschaft
    def get_curve_fx(self, x, r1, r2):
        fx = 0
        for i in range(len(self.W)):
            fx += 1 / np.sqrt(self.W[i]) * np.sin(self.W[i] * x + r1[i]) * r2[i]
        return fx * 3 + 350  # willkürliche Skalierung (Ausprobieren)

    def create_world_image(self):
        land = self.create_bool_landscape()

        # färbt den Boden entsprechend der Distanz zur Oberfläche
        map_dist = skfmm.distance(land)
        map_dist = map_dist / np.max(map_dist) * 4  # willkürlicher Faktor (alternativ 0.6 draufaddieren)
        world = plt.cm.copper_r(map_dist)
        # world = np.zeros([HEIGHT, WIDTH, 4])
        world[:, :, 3] = land
        world = np.asarray(world * 255, np.uint8)  # Werte der colormap zwischen 0 und 1, also mit 255 skalieren
        return QImage(world, WIDTH, HEIGHT, QImage.Format_RGBA8888)

    # setzt jeden Pixel auf True wenn er dem Land angehört und sonst auf False
    def create_bool_landscape(self):
        land = np.zeros([HEIGHT, WIDTH], dtype=np.bool)

        # prüfe für jeden Pixel, ob er unter dem Funktionswert an der x-Stelle liegt
        for i in range(WIDTH):
            for j in range(HEIGHT):
                if j > self.curve[i]:
                    land[j, i] = True
                else:
                    land[j, i] = False
        return land

    # returns angle consistent with Qpainter.rotate(a), so that 1 points at 2
    @staticmethod
    def getAngle(pos1, pos2):
        x_1 = pos1[0]
        y_1 = pos1[1]
        x_2 = pos2[0]
        y_2 = pos2[1]

        g = x_2 - x_1 if x_1 <= x_2 else x_1 - x_2
        a = y_2 - y_1 if y_1 <= y_2 else y_1 - y_2

        angle = np.arctan(g/a)*180/pi

        if(x_1 <= x_2):
            if(y_1 <= y_2):
                angle = 360 - angle
            else:
                angle += 180
        elif(y_1 > y_2):
                angle = 180 - angle

        return np.floor(angle)

    def mouse_press_event(self, event):
        qpos = event.pos()
        self.mousePos = tuple([qpos.x(), qpos.y()])
        # self.set_takeoff_angle()
        # self.display.setMouseTracking(False)
        # self.timer.start(1)
        print(self.getAngle(self.currentPlayer.pos, self.mousePos))

    def mouse_move_event(self, event):
        mousePos = event.pos()
        self.currentPlayer.setPlayeraim(tuple([mousePos.x(), mousePos.y()]))
        self.draw(self.entitylist)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # self.timer.stop()
            self.bulletPos = self.player2Pos if self.currentPlayer == 1 else self.player1Pos
            self.currentPlayer = 2 if self.currentPlayer == 1 else 1
            self.display.setMouseTracking(True)
            # self.redraw_canons(0, 0)


class Player:

    def __init__(self, index):

        self.id = index
        self.name = ''
        self.color = Qt.black
        self.pos = (0, 0)
        self.aimAngel = 180

    def setPlayerName(self, name):
        self.name = name

    def setPlayeraim(self, targetPos):
        self.aimAngel = Worms.getAngle(self.pos, targetPos)

    def setPlayerPos(self, destination):
        self.pos = destination

    def draw(self):

        layer = np.zeros([36, 15, 4])
        layer[:, :, 3] = 0  # macht Ebene transparent
        img = QImage(layer, 72, 72, QImage.Format_RGBA8888)
        painter = QPainter(img)
        # painter.setRenderHint(QPainter.Antialiasing)

        # sprite laden
        sprite = QPixmap('resources/tank.png').scaled(72, 30, Qt.KeepAspectRatio)
        painter.drawPixmap(0, 42, sprite)

        # canon = np.zeros([7, 60, 4])  # das canon image ist nur 7px*60px groß
        # canon[:, :, 3] = 0
        # img2 = QImage(canon, 7, 60, QImage.Format_RGBA8888)
        # canonpainter = QPainter(img2)
        # color = QColor("#788E2DFF")
        # canonpainter.setPen(color)
        # canonpainter.setBrush(color)
        # canonpainter.drawRect(0, 0, 7, 30)
        # canonpainter.rotate(self.aimAngel)
        #
        # painter.drawImage(0, 0, img2)
        #
        # canonpainter.end()
        painter.end()

        return img






app = QApplication(sys.argv)
# app.setOverrideCursor(Qt.BlankCursor)  # lässt Mauszeiger verschwinden
Worms()
sys.exit(app.exec_())

