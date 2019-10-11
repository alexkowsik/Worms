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
SCALING = 1.5*(WIDTH/1920)/(HEIGHT/1080)
METER = 10*SCALING
DEBUG = True
SCI_KIT = True

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
        self.test = 0

        self.display = QLabel()
        self.display.setFixedSize(WIDTH, HEIGHT)
        self.display.setMouseTracking(True)
        self.display.mouseMoveEvent = self.mouse_move_event
        self.display.mousePressEvent = self.mouse_press_event  # Klick wechselt Spieler
        self.display.keyPressEvent = self.key_press_event

        self.W = np.linspace(0.001, 0.05, 20)  # W war vorgegeben
        self.curve = self.create_curve()

        self.mousePos = None

        self.entitylist = []    # Bullet(s) have to be added to the entitylist before the players, because rendering
        self.testbullet = Bullet()
        self.entitylist.append(self.testbullet)

        self.playerlist = []
        self.playercount = 4        # TODO: take input from menu
        self.create_players(self.playercount)
        self.currentPlayer = self.playerlist[0]
        self.entitylist += self.playerlist  # TODO: separate entities from players and draw players on mousemove only

        self.testbullet.set_pos(self.currentPlayer.get_cannon_pos())


        self.worldImg = self.create_world_image()  # das Bild, das immer erhalten und bemalt wird
        self.worldImgFrozen = self.worldImg.copy()  # s. unten
        self.mappainter = QPainter(self.worldImg)
        self.mappainter.setRenderHint(QPainter.Antialiasing)

        self.timer = QTimer()
        self.timer.setInterval(16)      # 16ms for ~60Hz refresh rate
        self.timer.timeout.connect(self.update_pos)
        self.timer.timeout.connect(self.draw)

        self.timer.start()

    def create_players(self, quantity):          # quantity must not be higher than 4 !
        if quantity >= 5:
            print('TOO MANY PLAYERS')
        else:
            for i in range(0, quantity):
                self.playerlist.append(Player(i))
                x_pos = int(i*WIDTH/quantity)+int(WIDTH/(quantity*2))
                self.playerlist[-1].set_player_pos(tuple([x_pos, self.curve[x_pos]]))
                if DEBUG:
                    print('created player '+str(i))

    def draw(self,):        # draws all entities in self.entitylist omto the prerendered background once

        background = QPixmap.fromImage(self.worldImgFrozen.copy())
        mainpainter = QPainter(background)
        mainpainter.setRenderHint(QPainter.Antialiasing)
        mainpainter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        for entity in self.entitylist:
            tempimage = entity.draw()
            temppos = entity.get_POR()
            mainpainter.drawImage(temppos[0], temppos[1], tempimage)
            if DEBUG:
                mainpainter.setPen(Qt.red)
                mainpainter.drawLine(entity.pos[0]-3, entity.pos[1]-3, entity.pos[0]+3, entity.pos[1]+3)
                mainpainter.drawLine(entity.pos[0]+3, entity.pos[1]-3, entity.pos[0]-3, entity.pos[1]+3)
                # mainpainter.drawEllipse(entity.pos[0]-3, entity.pos[1]-3, 6, 6)

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
        return fx * 3 + 350   # willkürliche Skalierung (Ausprobieren)
        # TODO: hier ein minimum von der kurve für den offset benutzen

    # deprecated
    def get_curve_length(self):

        total = 0
        current_y = self.curve[0]
        for x in range(5, WIDTH, 5):
            previous_y = current_y
            current_y = self.curve[x]
            total += np.sqrt(25 + (current_y - previous_y)**2)

        return total

    def create_world_image(self):
        land = self.create_bool_landscape()

        # färbt den Boden entsprechend der Distanz zur Oberfläche
        if SCI_KIT:
            map_dist = skfmm.distance(land)
            map_dist = map_dist / np.max(map_dist) * 4  # willkürlicher Faktor (alternativ 0.6 draufaddieren)
            world = plt.cm.copper_r(map_dist)
        else:
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

    # returns angle consistent with Qpainter.rotate(angle), so that 1 points at 2
    @staticmethod
    def get_angle(pos1, pos2):
        x_1 = pos1[0]
        y_1 = pos1[1]
        x_2 = pos2[0]
        y_2 = pos2[1]

        g = x_2 - x_1 if x_1 <= x_2 else x_1 - x_2
        a = y_2 - y_1 if y_1 <= y_2 else y_1 - y_2
        if a == 0:
            a = 1

        angle = np.arctan(g/a)*180/pi

        if x_1 <= x_2:
            if y_1 <= y_2:
                angle = 360 - angle
            else:
                angle += 180
        elif y_1 > y_2:
            angle = 180 - angle

        return angle

    def update_pos(self):
        for entity in self.entitylist:
            if entity.is_flying:
                entity.update()
        self.test += 1
        # if DEBUG:
        #     print('update pos ['+str(self.test)+']')

    def shoot(self):
        self.testbullet.set_flight_angle(self.currentPlayer.aim_angle)
        self.testbullet.set_speed(6.5*METER)   #TODO: figure out nice speed, possibly power meter?
        self.testbullet.is_flying = True
        if DEBUG:
            print('boom')

    def mouse_press_event(self, event):
        qpos = event.pos()
        self.mousePos = tuple([qpos.x(), qpos.y()])
        self.display.setMouseTracking(False)
        if DEBUG:
            angle = self.get_angle(self.currentPlayer.pos, self.mousePos)
            print(angle)
        self.shoot()
        self.currentPlayer = self.playerlist[(self.currentPlayer.get_ID() + 1) % self.playercount]
        self.display.setMouseTracking(True)

    def mouse_move_event(self, event):
        mousePos = event.pos()
        self.currentPlayer.set_player_aim(tuple([mousePos.x(), mousePos.y()]))
        if not self.testbullet.is_flying:
            self.testbullet.set_pos(self.currentPlayer.get_cannon_pos())
            self.testbullet.set_flight_angle(self.currentPlayer.aim_angle)
        self.draw()

    def key_press_event(self, event):
        if event.key() == Qt.Key_Escape:
            self.timer.stop()
            # self.currentPlayer = playerlist.next()
            self.display.setMouseTracking(True)


class Player:

    def __init__(self, index):

        self.id = index
        self.name = ''
        self.color = Qt.black
        self.pos = (0, 0)    # pos is where the middle of the tank tracks touch the ground. use getPOR() for positioning tank on map
        self.aim_angle = 180
        self.size = (int(36*SCALING), int(15*SCALING))      # png is 36 x 15
        self.cannon_offset = int(self.size[1]*0.3)
        self.is_flying = False

    def get_POR(self):
        return tuple([self.pos[0]-self.size[0]//2, self.pos[1]-self.size[0]//2-self.size[1]+self.cannon_offset])

    def get_cannon_pos(self):
        return tuple([self.pos[0], self.pos[1]-self.size[1]+self.cannon_offset])

    def get_ID(self):
        return self.id

    def set_player_name(self, name):
        self.name = name

    def set_player_aim(self, target_pos):
        self.aim_angle = Worms.get_angle(self.pos, target_pos)

    def set_player_pos(self, destination):
        self.pos = destination

    def get_cannon_POR(self):
        cannonwidth = 1.5*SCALING
        angle = self.aim_angle * pi / 180
        x_offset = np.cos(angle)*cannonwidth
        y_offset = np.sin(angle)*cannonwidth

        # if (self.id == 0 and DEBUG):
        #     print(angle, np.cos(angle), np.sin(angle))
        return tuple([x_offset, y_offset])


    def draw(self):

        layer = np.zeros([self.size[0], self.size[0], 4])
        layer[:, :, 3] = 0  # macht Ebene transparent
        img = QImage(layer, self.size[0], self.size[0], QImage.Format_RGBA8888)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # draw cannon
        angle = np.floor(self.aim_angle)

        if DEBUG:
            pencolor = Qt.red
            brushcolor = QColor('#00000000')
            source = 'resources/tank2.png'

            painter.setPen(pencolor)
            painter.setBrush(brushcolor)
            painter.drawRect(0, 0, self.size[0], self.size[0])
        else:
            pencolor = QColor("#788E2D")
            brushcolor = QColor("#788E2D")
            source = 'resources/tank2.png'

            painter.setPen(pencolor)
            painter.setBrush(brushcolor)

        spirte = QPixmap(source).scaled(self.size[0], self.size[0], Qt.KeepAspectRatio)
        painter.drawPixmap(0, self.size[0]//2-(self.size[1]//2-self.cannon_offset), spirte)

        if DEBUG:
            painter.setPen(Qt.green)
            painter.drawEllipse(self.size[0]//2-3, self.size[0]//2-3, 6, 6)
            painter.setPen(pencolor)

        offsets = self.get_cannon_POR()
        painter.translate(self.size[0]//2-offsets[0], self.size[0]//2-offsets[1])
        # painter.translate(self.size[0]//2, self.size[0]//2)
        painter.rotate(angle)

        painter.drawRect(0, 0, 3*SCALING, self.size[0]//2)

        painter.end()

        return img


class Bullet:

    def __init__(self):

        self.color = Qt.gray
        self.pos = (100, 100)     # pos is at center of bullet
        self.size = int(8*SCALING)      # 8 is somewhat near sqrt(3**2 + 7.5 **2) because of rotation, 4x10 is png size scaled to 3 x 7.5
        self.speed = 0
        self.flight_angle = 270
        self.is_flying = False

    def get_POR(self):      # returns pos of the back of the bullet for easy positioning
        projectile_width = 7.5/2*SCALING
        angle = self.flight_angle * pi / 180
        x_offset = np.sin(angle)*projectile_width
        y_offset = -np.cos(angle)*projectile_width

        return tuple([self.pos[0]-self.size//2-x_offset, self.pos[1]-self.size//2-y_offset])

    def set_speed(self, speed):     # set speed in meters per second
        self.speed = speed

    def set_flight_angle(self, angle):
        self.flight_angle = angle

    def set_pos(self, pos):
        self.pos = pos

    def draw(self):

        layer = np.zeros([self.size, self.size, 4])
        layer[:, :, 3] = 0  # macht Ebene transparent
        img = QImage(layer, self.size, self.size, QImage.Format_RGBA8888)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        angle = int(self.flight_angle)

        if DEBUG:
            painter.setPen(Qt.red)
            painter.setBrush(QColor('#00000000'))
            painter.drawRect(0, 0, self.size, self.size)
            painter.drawEllipse(self.size//2-2, self.size//2-2, 4, 4)

        painter.translate(self.size // 2, self.size // 2)
        painter.rotate(angle)
        spirte = QPixmap('resources/bullet.png').scaled(3*SCALING, 7.5*SCALING, Qt.KeepAspectRatio)
        painter.drawPixmap(-3*SCALING//2, -7.5*SCALING//2, spirte)

        painter.end()

        return img

    def update(self):   # calculates next pos and flight angle in 16ms intervall
        if self.pos[1] > HEIGHT or self.pos[0] < -250 or self.pos[0] > WIDTH+250:
            print('peng', self.pos[0], self.pos[1])
            self.set_speed(0)
            self.is_flying = False
            self.set_flight_angle(0)
        else:
            tick = 8
            x_move = self.speed*-np.sin(self.flight_angle*pi/180)*1/tick
            y_move = self.speed*np.cos(self.flight_angle*pi/180)*1/tick+9.81*1/tick**2
            self.speed -= -np.cos(self.flight_angle*pi/180)*9.81*1/tick
            next_pos = tuple([self.pos[0]+x_move, self.pos[1]+y_move])
            self.flight_angle = Worms.get_angle(self.pos, next_pos)
            self.pos = next_pos
        # if self.is_flying and DEBUG:
        #     print(next_pos)


app = QApplication(sys.argv)
# app.setOverrideCursor(Qt.BlankCursor)  # lässt Mauszeiger verschwinden
Worms()
sys.exit(app.exec_())

