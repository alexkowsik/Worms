import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np
import random
from math import sqrt, sin, pi
import skfmm
import matplotlib.pyplot as plt


def getCurve(w, x, r1, r2):
    fx = 0
    for i in range(len(w)):
        fx += 1/sqrt(w[i]) * sin(w[i] * x + r1[i]) * r2[i]
    return fx * 3 + 350   # willkürliche Skalierung (Ausprobieren)


# TODO: die Funktion ist wahrscheinlich doch Blödsinn
def getWindVectorField(w, curve):
    r1 = [random.uniform(0, 2 * pi) for i in range(len(w))]
    r2 = [random.uniform(-1, 1) for j in range(len(w))]
    r3 = [random.uniform(0, 2 * pi) for i in range(len(w))]
    r4 = [random.uniform(-1, 1) for j in range(len(w))]
    windvector = np.zeros([HEIGHT, WIDTH])

    for i in range(WIDTH):
        tmp = getCurve(w, i, r1, r2)
        for j in range(HEIGHT):
            if j > curve[i]:
                break
            windvector[j][i] = (tmp + getCurve(w, j, r3, r4) - 700) / 6

    return windvector


if __name__ == '__main__':
    WIDTH = 1200
    HEIGHT = 600

    app = QApplication(sys.argv)
    display = QLabel()

    # W war vorgegeben
    W = np.linspace(0.001, 0.05, 20)

    # Zufallszahlen für die Funktion
    random1 = [random.uniform(0, 2 * pi) for i in range(len(W))]
    random2 = [random.uniform(-1, 1) for j in range(len(W))]

    curve = [getCurve(W, i, random1, random2) for i in range(WIDTH)]
    # windvectorfield = getWindVectorField(W, curve)  # alpha(x, y), also der Winkel

    m = np.zeros([HEIGHT, WIDTH], dtype=np.bool)

    # prüfe für jeden Pixel, ob er unter dem Funktionswert an der x-Stelle liegt
    for i in range(WIDTH):
        for j in range(HEIGHT):
            if j > curve[i]:
                m[j, i] = True
            else:
                m[j, i] = False

    # färbt den Boden entsprechend der Distanz zur Oberfläche
    map_dist = skfmm.distance(m)
    map_dist = map_dist / np.max(map_dist) * 4  # willkürlicher Faktor (alternativ 0.6 draufaddieren)
    world = plt.cm.copper_r(map_dist)
    world[:, :, 3] = m
    world = np.asarray(world * 255, np.uint8)
    world_img = QImage(world, WIDTH, HEIGHT, QImage.Format_RGBA8888)

    # Painter, der Landschaft entfernen kann
    mappainter = QPainter(world_img)
    mappainter.setCompositionMode(QPainter.CompositionMode_Clear)
    mappainter.setPen(Qt.white)
    mappainter.setBrush(Qt.white)

    # zeichnet Krater an die Funktionsstelle von 500 mit Radius 50
    mappainter.drawEllipse(QPoint(500, curve[500]), 50, 50)

    # Ebene mit den Figuren
    chars = np.zeros([WIDTH, HEIGHT, 4])
    chars[:, :, 3] = 0  # macht Ebene transparent
    char_img = QImage(chars, WIDTH, HEIGHT, QImage.Format_RGBA8888)
    charpainter = QPainter(char_img)

    # erster Spieler
    charpainter.setPen(Qt.green)
    charpainter.setBrush(Qt.green)
    charpainter.drawEllipse(QPoint(200, curve[200]), 15, 15)

    # zweiter Spieler
    charpainter.setPen(Qt.blue)
    charpainter.setBrush(Qt.blue)
    charpainter.drawEllipse(QPoint(1000, curve[1000]), 15, 15)

    # zeichne Ebene mit Spielern auf die map
    mappainter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    mappainter.drawPixmap(0, 0, QPixmap.fromImage(char_img))

    display.setPixmap(QPixmap.fromImage(world_img))
    display.show()

    sys.exit(app.exec_())

