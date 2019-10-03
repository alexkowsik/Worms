import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np
import random
from math import pi
import skfmm
import matplotlib.pyplot as plt


WIDTH = 1200
HEIGHT = 600


class Worms:
    def __init__(self):
        self.display = QLabel()
        self.display.setMouseTracking(True)
        self.display.mouseMoveEvent = self.mouse_move_event
        self.display.mousePressEvent = self.mouse_press_event  # Klick wechselt Spieler

        self.W = np.linspace(0.001, 0.05, 20)  # W war vorgegeben
        self.curve = self.create_curve()

        self.player1Pos = QPoint(200, self.curve[200])
        self.player2Pos = QPoint(1000, self.curve[1000])
        self.currentPlayer = 1

        self.worldImg = self.create_world_image()
        self.mappainter = QPainter(self.worldImg)

        self.charsImg = self.create_chars_image()
        self.canonImg = self.create_canon_image()

        self.make_crater(500, 50)  # demo: x = 500, radius = 50
        self.draw_charsImg()

        # self.windVectors = self.get_wind_vector_field()
        self.redraw(self.player1Pos.x(), 0)

    def create_curve(self):
        random1 = [random.uniform(0, 2 * pi) for _ in range(len(self.W))]
        random2 = [random.uniform(-1, 1) for _ in range(len(self.W))]
        return [self.get_curve_fx(i, random1, random2) for i in range(WIDTH)]

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
        world[:, :, 3] = land
        world = np.asarray(world * 255, np.uint8)
        return QImage(world, WIDTH, HEIGHT, QImage.Format_RGBA8888)

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

    def make_crater(self, x, radius):
        self.mappainter.setCompositionMode(QPainter.CompositionMode_Clear)
        self.mappainter.setPen(Qt.white)
        self.mappainter.setBrush(Qt.white)

        # zeichnet Krater an die Funktionsstelle von 500 mit Radius 50
        self.mappainter.drawEllipse(QPoint(x, self.curve[x]), radius, radius)

    def create_chars_image(self):
        chars = np.zeros([WIDTH, HEIGHT, 4])
        chars[:, :, 3] = 0  # macht Ebene transparent
        img = QImage(chars, WIDTH, HEIGHT, QImage.Format_RGBA8888)
        charpainter = QPainter(img)

        # erster Spieler
        charpainter.setPen(Qt.green)
        charpainter.setBrush(Qt.green)
        charpainter.drawEllipse(QPoint(200, self.curve[200]), 15, 15)

        # zweiter Spieler
        charpainter.setPen(Qt.blue)
        charpainter.setBrush(Qt.blue)
        charpainter.drawEllipse(QPoint(1000, self.curve[1000]), 15, 15)

        return img

    def draw_charsImg(self):
        self.mappainter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        self.mappainter.drawPixmap(0, 0, QPixmap.fromImage(self.charsImg))

    def create_canon_image(self):
        canon = np.zeros([7, 60, 4])
        canon[:, :, 3] = 0
        img = QImage(canon, 7, 60, QImage.Format_RGBA8888)
        canonpainter = QPainter(img)
        canonpainter.setPen(QColor(qRgb(0, 52, 135)))
        canonpainter.setBrush(QColor(qRgb(0, 52, 135)))
        canonpainter.drawRect(0, 0, 7, 30)
        canonpainter.drawRect(7, 30, 7, 30)
        return img

    def get_angle(self, x, y):
        px = self.player1Pos.x() if self.currentPlayer == 1 else self.player2Pos.x()
        py = self.player1Pos.y() if self.currentPlayer == 1 else self.player2Pos.y()

        if x == px:
            if y <= py:
                return 0
            else:
                return 180
        elif y == py:
            if x <= py:
                return 90
            else:
                return -90
        elif x < px:
            if y < py:
                return np.degrees(np.arctan((px - x) / (py - y)))
            else:
                return 180 + np.degrees(np.arctan((px - x) / (py - y)))
        else:
            if y < py:
                return 360 + np.degrees(np.arctan((px - x) / (py - y)))
            else:
                return 180 - np.degrees(np.arctan((px - x) / (y - py)))

    def redraw(self, x, y):
        img = self.worldImg.copy()
        painter = QPainter(img)

        painter.setPen(QColor(qRgb(0, 52, 135)))
        painter.setBrush(QColor(qRgb(0, 52, 135)))
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        c = QPointF(self.player1Pos.x(), self.player1Pos.y()) if self.currentPlayer == 1 else \
            QPointF(self.player2Pos.x(), self.player2Pos.y())

        painter.translate(c)
        angle = self.get_angle(x, y)
        painter.rotate(-angle + 180)
        painter.drawPixmap(QPoint(-4, 0), QPixmap.fromImage(self.canonImg))
        painter.rotate(-180 + angle)
        painter.translate(-c)
        painter.end()

        self.display.setPixmap(QPixmap.fromImage(img))
        self.display.show()

    # TODO: die Funktion ist wahrscheinlich doch Blödsinn
    def get_wind_vector_field(self):
        r1 = [random.uniform(0, 2 * pi) for i in range(len(self.W))]
        r2 = [random.uniform(-1, 1) for j in range(len(self.W))]
        r3 = [random.uniform(0, 2 * pi) for i in range(len(self.W))]
        r4 = [random.uniform(-1, 1) for j in range(len(self.W))]
        windvector = np.zeros([HEIGHT, WIDTH])

        for i in range(WIDTH):
            tmp = self.get_curve_fx(i, r1, r2)
            for j in range(HEIGHT):
                if j > self.curve[i]:
                    break
                windvector[j][i] = (tmp + self.get_curve_fx(j, r3, r4) - 700) / 6
        return windvector

    def mouse_press_event(self, event):
        self.currentPlayer = 2 if self.currentPlayer == 1 else 1
        print('press', event.pos())

    def mouse_move_event(self, QMouseEvent):
        self.redraw(QMouseEvent.pos().x(), QMouseEvent.pos().y())


app = QApplication(sys.argv)
# app.setOverrideCursor(Qt.BlankCursor)  # lässt Mauszeiger verschwinden
Worms()
sys.exit(app.exec_())

