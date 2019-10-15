import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np
import random
from math import pi
import time
#import skfmm
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
        self.display.keyPressEvent = self.keyPressEvent

        self.W = np.linspace(0.001, 0.05, 20)  # W war vorgegeben
        self.curve = self.create_curve()

        self.mousePos = None

        self.gravity_pull = 9.81    #can by any positive real number
        self.playerlist = []


        self.entitylist = self.playerlist       # TODO: separate entities from players and draw players on mousemove only


        self.playercount = 4        # TODO: take input from menu
        self.createPlayers(self.playercount)

        self.bullet = Bullet()
        self.entitylist.append(self.bullet)



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
        self.timer = QTimer()
        self.timer.timeout.connect(self.draw)

        self.timer.start()

        self.draw()


    def update_pos(self):
        self.pull = 0
        for obj in self.entitylist:
            self.pull += self.gravity_pull * obj.mass

        # updated location of bullet
        shot = QPoint(self.bulletPos.x() + self.shot_vector.x(),
                      self.bulletPos.y() - self.shot_vector.y())

        if self.pull >= 1:
            self.shot_vector -= QPoint(0, np.floor(self.pull))  # applying pull. direction changes
            self.pull = self.pull % 1  # resetting pull

        # only travel when frame_count % travel_rate = 0
        # pauses pull and bullet travel, but not pull and bullet simulation
        if self.frame_count == self.travel_rate:
            self.frame_count = -1
            self.bulletPos = shot

        self.frame_count += 1


    def createPlayers(self, quantity):          # quantity must not be higher than 4 !
        if quantity >= 5:
            print('TOO MANY PLAYERS')
        else:
            for i in range(0, quantity):
                if i == 0:
                    self.currentPlayer = Player(0)
                    self.playerlist.append(self.currentPlayer)
                else:
                    self.playerlist.append(Player(i))
                x_pos = int(i*WIDTH/quantity)+int(WIDTH/(quantity*2))
                self.playerlist[-1].setPlayerPos(tuple([x_pos, self.curve[x_pos]]))
                print('created player '+str(i))

    def draw(self,):
        debug = False

        background = QPixmap.fromImage(self.worldImgFrozen.copy())
        mainpainter = QPainter(background)
        mainpainter.setRenderHint(QPainter.Antialiasing)
        mainpainter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # while True:

        for entity in self.entitylist:
            tempimage = entity.draw()
            temppos = entity.getPOR()
            mainpainter.drawImage(temppos[0], temppos[1], tempimage)
            if debug:
                mainpainter.setPen(Qt.red)
                mainpainter.setBrush(Qt.red)
                mainpainter.drawEllipse(entity.pos[0]-3, entity.pos[1]-3, 5, 5)

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

    # def get_curve_length(self):
    #
    #     total = 0
    #     current_y = self.curve[0]
    #     previous_y = 0
    #     for x in range(5, WIDTH, 5):
    #         previous_y = current_y
    #         current_y = self.curve[x]
    #         total += np.sqrt(25 + (current_y - previous_y)**2)
    #
    #     return total


    def create_world_image(self):
        land = self.create_bool_landscape()

        # färbt den Boden entsprechend der Distanz zur Oberfläche
        # map_dist = skfmm.distance(land)
        # map_dist = map_dist / np.max(map_dist) * 4  # willkürlicher Faktor (alternativ 0.6 draufaddieren)
        # world = plt.cm.copper_r(map_dist)
        world = np.zeros([HEIGHT, WIDTH, 4])
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

    def shoot(self):
        print('boom')
        time.sleep(2)

    def mouse_press_event(self, event):
        qpos = event.pos()
        self.mousePos = tuple([qpos.x(), qpos.y()])
        self.display.setMouseTracking(False)
        print(self.getAngle(self.currentPlayer.pos, self.mousePos))
        self.shoot()    # running this command adds delay!
        self.currentPlayer = self.playerlist[(self.currentPlayer.getID()+1) % self.playercount]
        self.display.setMouseTracking(True)


    def mouse_move_event(self, event):
        mousePos = event.pos()
        self.currentPlayer.setPlayeraim(tuple([mousePos.x(), mousePos.y()]))
        self.draw()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.timer.stop()
            # self.currentPlayer = playerlist.next()
            self.display.setMouseTracking(True)
            # self.redraw_canons(0, 0)


class Player:

    def __init__(self, index):

        self.id = index
        self.name = ''
        self.color = Qt.black
        self.pos = (0, 0)
        self.aimAngel = 180
        self.size = (72, 30)

    def getPOR(self):
        return tuple([self.pos[0]-self.size[0]//2, self.pos[1]-55])

    def getID(self):
        return self.id

    def setPlayerName(self, name):
        self.name = name

    def setPlayeraim(self, targetPos):
        self.aimAngel = Worms.getAngle(self.pos, targetPos)

    def setPlayerPos(self, destination):
        self.pos = destination

    def draw(self):
        debug = False

        layer = np.zeros([self.size[0], 2*self.size[1], 4])
        layer[:, :, 3] = 0  # macht Ebene transparent
        img = QImage(layer, self.size[0], 2*self.size[1], QImage.Format_RGBA8888)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # draw cannon
        angle = self.aimAngel

        if debug:
            painter.setPen(Qt.red)
            painter.setBrush(QColor('#00000000'))
            painter.drawRect(0, 0, self.size[0], 2*self.size[1])
            spirte = QPixmap('resources/tank_debug.png').scaled(self.size[0], self.size[1], Qt.KeepAspectRatio)
            painter.drawPixmap(0, 25, spirte)

            painter.translate(35, 30)
            painter.rotate(angle)

            color = Qt.red
            painter.setPen(color)
            painter.setBrush(color)
            painter.drawRect(0, 0, 4, 30)

            painter.rotate(-angle)
            painter.translate(-35, -30)
        else:
            spirte = QPixmap('resources/tank.png').scaled(self.size[0], self.size[1], Qt.KeepAspectRatio)
            painter.drawPixmap(0, 25, spirte)

            painter.translate(35, 30)
            painter.rotate(angle)

            color = QColor("#788E2D")
            painter.setPen(color)
            painter.setBrush(color)
            painter.drawRect(0, 0, 4, 30)

        painter.end()

        return img

class Bullet:

    def __init__(self):

        self.color = Qt.gray
        self.pos = QPoint(0,0)
        self.size = (4, 10)
        self.velocity = (0, 0)
        self.mass = 10

    def getPOR(self):
        return tuple([self.pos[0]-self.size[0]//2, self.pos[1]-self.size[1]])

    def getFlightAngle(self):
        return 180

    def setvelocity(self, velocity):
        self.velocity = velocity

    def draw(self):
        debug = False

        layer = np.zeros([self.size[0], self.size[1], 4])
        layer[:, :, 3] = 0  # macht Ebene transparent
        img = QImage(layer, self.size[0], self.size[1], QImage.Format_RGBA8888)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # draw cannon
        angle = self.aimAngel

        if debug:
            painter.setPen(Qt.red)
            painter.setBrush(QColor('#00000000'))
            painter.drawRect(0, 0, self.size[0], 2*self.size[1])
            spirte = QPixmap('resources/tank_debug.png').scaled(self.size[0], self.size[1], Qt.KeepAspectRatio)
            painter.drawPixmap(0, 25, spirte)

            painter.translate(35, 30)
            painter.rotate(angle)

            color = Qt.red
            painter.setPen(color)
            painter.setBrush(color)
            painter.drawRect(0, 0, 4, 30)

            painter.rotate(-angle)
            painter.translate(-35, -30)
        else:
            spirte = QPixmap('resources/tank.png').scaled(self.size[0], self.size[1], Qt.KeepAspectRatio)
            painter.drawPixmap(0, 25, spirte)

            painter.translate(35, 30)
            painter.rotate(angle)

            color = QColor("#788E2D")
            painter.setPen(color)
            painter.setBrush(color)
            painter.drawRect(0, 0, 4, 30)

        painter.end()

        return img






app = QApplication(sys.argv)
# app.setOverrideCursor(Qt.BlankCursor)  # lässt Mauszeiger verschwinden
Worms()
sys.exit(app.exec_())

