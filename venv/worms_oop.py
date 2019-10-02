import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np
import random
from math import sqrt, sin, pi
import skfmm
import matplotlib.pyplot as plt


WIDTH = 1200
HEIGHT = 600


class Worms:
    def __init__(self):
        self.display = QLabel()
        self.display.mouseEvent = self.mouse_event
        self.W = np.linspace(0.001, 0.05, 20)  # W war vorgegeben
        self.curve = self.create_curve()
        self.worldImg = self.create_world_image()
        self.mappainter = QPainter(self.worldImg)
        self.make_crater()  # demo
        self.charsImg = self.create_chars_image()
        self.charpainter = QPainter(self.charsImg)
        self.create_chars()
        # self.windVectors = self.get_wind_vector_field()
        self.redraw()

    def create_curve(self):
        random1 = [random.uniform(0, 2 * pi) for i in range(len(self.W))]
        random2 = [random.uniform(-1, 1) for i in range(len(self.W))]
        return [self.get_curve(i, random1, random2) for i in range(WIDTH)]

    def get_curve(self, x, r1, r2):
        fx = 0
        for i in range(len(self.W)):
            fx += 1 / sqrt(self.W[i]) * sin(self.W[i] * x + r1[i]) * r2[i]
        return fx * 3 + 350  # willkürliche Skalierung (Ausprobieren)

    def create_world_image(self):
        m = self.create_bool_landscape()

        # färbt den Boden entsprechend der Distanz zur Oberfläche
        map_dist = skfmm.distance(m)
        map_dist = map_dist / np.max(map_dist) * 4  # willkürlicher Faktor (alternativ 0.6 draufaddieren)
        world = plt.cm.copper_r(map_dist)
        world[:, :, 3] = m
        world = np.asarray(world * 255, np.uint8)
        return QImage(world, WIDTH, HEIGHT, QImage.Format_RGBA8888)

    def create_bool_landscape(self):
        m = np.zeros([HEIGHT, WIDTH], dtype=np.bool)

        # prüfe für jeden Pixel, ob er unter dem Funktionswert an der x-Stelle liegt
        for i in range(WIDTH):
            for j in range(HEIGHT):
                if j > self.curve[i]:
                    m[j, i] = True
                else:
                    m[j, i] = False
        return m

    def make_crater(self):
        self.mappainter.setCompositionMode(QPainter.CompositionMode_Clear)
        self.mappainter.setPen(Qt.white)
        self.mappainter.setBrush(Qt.white)

        # zeichnet Krater an die Funktionsstelle von 500 mit Radius 50
        self.mappainter.drawEllipse(QPoint(500, self.curve[500]), 50, 50)

    def create_chars_image(self):
        chars = np.zeros([WIDTH, HEIGHT, 4])
        chars[:, :, 3] = 0  # macht Ebene transparent
        return QImage(chars, WIDTH, HEIGHT, QImage.Format_RGBA8888)

    def create_chars(self):
        # erster Spieler
        self.charpainter.setPen(Qt.green)
        self.charpainter.setBrush(Qt.green)
        self.charpainter.drawEllipse(QPoint(200, self.curve[200]), 15, 15)

        # zweiter Spieler
        self.charpainter.setPen(Qt.blue)
        self.charpainter.setBrush(Qt.blue)
        self.charpainter.drawEllipse(QPoint(1000, self.curve[1000]), 15, 15)

    def redraw(self):
        # zeichne Ebene mit Spielern auf die map
        self.mappainter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        self.mappainter.drawPixmap(0, 0, QPixmap.fromImage(self.charsImg))

        self.display.setPixmap(QPixmap.fromImage(self.worldImg))
        self.display.show()

    # TODO: die Funktion ist wahrscheinlich doch Blödsinn
    def get_wind_vector_field(self):
        r1 = [random.uniform(0, 2 * pi) for i in range(len(self.W))]
        r2 = [random.uniform(-1, 1) for j in range(len(self.W))]
        r3 = [random.uniform(0, 2 * pi) for i in range(len(self.W))]
        r4 = [random.uniform(-1, 1) for j in range(len(self.W))]
        windvector = np.zeros([HEIGHT, WIDTH])

        for i in range(WIDTH):
            tmp = self.get_curve(i, r1, r2)
            for j in range(HEIGHT):
                if j > self.curve[i]:
                    break
                windvector[j][i] = (tmp + self.get_curve(j, r3, r4) - 700) / 6
        return windvector

    def mouse_event(self, event):
        pass


app = QApplication(sys.argv)
Worms()
sys.exit(app.exec_())

