import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np
import random
from math import pi
import time

# import skfmm
# import matplotlib.pyplot as plt


WIDTH = 1200
HEIGHT = 600


class Worms:
    def __init__(self):

        self.display = QLabel()
        self.display.setMouseTracking(True)
        self.display.mouseMoveEvent = self.mouse_move_event
        self.display.mousePressEvent = self.mouse_press_event  # Klick wechselt Spieler
        self.display.keyPressEvent = self.keyPressEvent

        self.W = np.linspace(0.001, 0.05, 20)  # W war vorgegeben
        self.curve = self.create_curve()

        self.timer = QTimer()
        self.timer.timeout.connect(self.animation)

        self.mousePos = None
        self.player1Pos = QPoint(200, self.curve[200])
        self.player2Pos = QPoint(1000, self.curve[1000])
        self.currentPlayer = 1

        self.worldImg = self.create_world_image()  # das Bild, das immer erhalten und bemalt wird
        self.worldImgFrozen = self.worldImg.copy()  # s. unten
        self.mappainter = QPainter(self.worldImg)
        self.mappainter.setRenderHint(QPainter.Antialiasing)

        self.charsImg = self.create_chars_image()
        self.canonImg1 = self.create_canon_image(1)
        self.canonImg2 = self.create_canon_image(2)

        self.bulletImg = self.create_bullet_image()
        self.bulletPos = self.player1Pos + QPoint(0, 0)

        # self.make_crater(500, 50)  # demo: x = 500, radius = 50
        self.draw_chars_img()
        self.redraw_canons(self.player1Pos.x(), self.player1Pos.y())

        # physics variables
        self.travel_rate = 3  # makes bullet travel every travel-rate-th frame
        # decreasing this makes shots way less precise
        self.frame_count = self.travel_rate
        self.shot_magnitude = 18.4  # how string the shot will be. the less the travel_rate,
        # the lower this should be
        self.gravity_pull = 9.81
        self.mass = 9 * 10 ** -3  # the mass of default projectile

    def set_takeoff_angle(self):
        # this computes the angle of the shot, measured by the line between the player
        # and the mouseclick and stores this as a Vector in shot_vector.
        # also resets pull and travel_counter ( see animation function)
        px = self.player1Pos.x() if self.currentPlayer == 1 else self.player2Pos.x()
        py = self.player1Pos.y() if self.currentPlayer == 1 else self.player2Pos.y()
        mouse_click_x = self.mousePos.x()
        mouse_click_y = self.mousePos.y()

        if mouse_click_x == px:
            if y <= py:
                self.takeoff_angle = -np.pi / 2
            else:
                self.takeoff_angle = np.pi / 2
        elif mouse_click_x < px:
            if mouse_click_y < py:
                self.takeoff_angle = np.pi - np.arctan((mouse_click_y - py) / (mouse_click_x - px))
            else:
                self.takeoff_angle = np.pi - np.arctan((mouse_click_y - py) / (mouse_click_x - px))
        else:
            self.takeoff_angle = np.arctan((py - mouse_click_y) / (mouse_click_x - px))

        self.shot_vector = QPoint(np.floor(self.shot_magnitude * np.cos(self.takeoff_angle))
                                  , np.floor(self.shot_magnitude * np.sin(self.takeoff_angle)))
        self.pull = 0
        self.travel_counter = 0

    # TODO: nicht für alle Pixel, sondern nur für eine Korrdinate berechnen, die übergeben wird
    def get_wind_vector_field(self):
        r1 = [random.uniform(0, 2 * pi) for _ in range(len(self.W))]
        r2 = [random.uniform(-1, 1) for _ in range(len(self.W))]
        r3 = [random.uniform(0, 2 * pi) for _ in range(len(self.W))]
        r4 = [random.uniform(-1, 1) for _ in range(len(self.W))]
        windvector = np.zeros([HEIGHT, WIDTH])

        for i in range(WIDTH):
            tmp = self.get_curve_fx(i, r1, r2)
            for j in range(HEIGHT):
                if j > self.curve[i]:
                    break
                windvector[j][i] = (tmp + self.get_curve_fx(j, r3, r4) - 700) / 6
        return windvector

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
        self.land = self.create_bool_landscape()

        # färbt den Boden entsprechend der Distanz zur Oberfläche
        # map_dist = skfmm.distance(land)
        # map_dist = map_dist / np.max(map_dist) * 4  # willkürlicher Faktor (alternativ 0.6 draufaddieren)
        # world = plt.cm.copper_r(map_dist)
        world = np.zeros([HEIGHT, WIDTH, 4])
        world[:, :, 3] = self.land
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

    def make_crater(self, x, radius):
        # setzt den painter auf den "Radiermodus"
        self.mappainter.setCompositionMode(QPainter.CompositionMode_Clear)
        self.mappainter.setPen(Qt.white)
        self.mappainter.setBrush(Qt.white)

        # zeichnet Krater an die Funktionsstelle von 500 mit Radius 50
        self.mappainter.drawEllipse(QPoint(x, self.curve[x]), radius, radius)
        for width in range(-radius - 1, radius + 1):
            height = np.sqrt(np.power(radius, 2) - np.power(width, 2))
            self.curve[x + width] = self.curve[x + width] + height

    def create_chars_image(self):
        chars = np.zeros([WIDTH, HEIGHT, 4])  # TODO: char image kleiner machen und in zwei einzelne aufsplitten
        chars[:, :, 3] = 0  # macht Ebene transparent
        img = QImage(chars, WIDTH, HEIGHT, QImage.Format_RGBA8888)
        charpainter = QPainter(img)
        charpainter.setRenderHint(QPainter.Antialiasing)

        # erster Spieler
        charpainter.setPen(Qt.green)
        charpainter.setBrush(Qt.green)
        charpainter.drawEllipse(QPoint(self.player1Pos.x(), self.player1Pos.y()), 15, 15)

        # zweiter Spieler
        charpainter.setPen(Qt.blue)
        charpainter.setBrush(Qt.blue)
        charpainter.drawEllipse(QPoint(self.player2Pos.x(), self.player2Pos.y()), 15, 15)

        return img

    def draw_chars_img(self):
        # setzt den painter af einen Modus, in welchem er Pixmaps übereinander zeichnen kann
        self.mappainter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        self.mappainter.drawPixmap(0, 0, QPixmap.fromImage(self.charsImg))

    def create_canon_image(self, player):
        canon = np.zeros([7, 60, 4])  # das canon image ist nur 7px*60px groß
        canon[:, :, 3] = 0
        img = QImage(canon, 7, 60, QImage.Format_RGBA8888)
        canonpainter = QPainter(img)
        color = QColor(qRgb(0, 135, 0)) if player == 1 else QColor(qRgb(0, 0, 135))
        canonpainter.setPen(color)
        canonpainter.setBrush(color)
        canonpainter.drawRect(0, 0, 7, 30)
        canonpainter.drawRect(7, 30, 7, 30)
        return img

    def create_bullet_image(self):
        ball = np.zeros([8, 8, 4])
        ball[:, :, 3] = 0
        img = QImage(ball, 8, 8, QImage.Format_RGBA8888)
        ballpainter = QPainter(img)
        ballpainter.setPen(Qt.red)
        ballpainter.setBrush(Qt.red)
        ballpainter.drawRect(0, 0, 8, 8)
        return img

    # x und y in der Regel Mauskoordinaten; berechnet Winkel zur Mitte des Spielers
    def get_angle(self, x, y):
        px = self.player1Pos.x() if self.currentPlayer == 1 else self.player2Pos.x()
        py = self.player1Pos.y() if self.currentPlayer == 1 else self.player2Pos.y()

        if x == px:
            if y <= py:
                return 0
            else:
                return 180
        elif y == py:
            if x <= px:
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

    def redraw_canons(self, x, y):
        img = self.worldImg.copy()
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # zeichnet das Kanonenrohr des jeweils anderen Spielers
        if self.currentPlayer == 1:
            painter.drawPixmap(self.player2Pos.x() - 4, self.player2Pos.y() - 30, QPixmap.fromImage(self.canonImg2))
        else:
            painter.drawPixmap(self.player1Pos.x() - 4, self.player1Pos.y() - 30, QPixmap.fromImage(self.canonImg1))

        new_corner = self.player1Pos if self.currentPlayer == 1 else self.player2Pos
        painter.translate(new_corner)

        angle = self.get_angle(x, y)
        painter.rotate(-angle + 180)

        if self.currentPlayer == 1:
            painter.drawPixmap(QPoint(-4, 0), QPixmap.fromImage(self.canonImg1))
        else:
            painter.drawPixmap(QPoint(-4, 0), QPixmap.fromImage(self.canonImg2))

        # setze alles wieder zurück, damit beim nächsten Aufruf das Kanonenrohr des anderen richtig gezeichnet wird
        painter.rotate(-180 + angle)
        painter.translate(-new_corner)
        painter.end()

        self.worldImgFrozen = img  # speichere die Kanonenpositionen für den Fall dass eine Animation folgt
        self.display.setPixmap(QPixmap.fromImage(img))
        self.display.show()

    def animation(self):
        img = self.worldImgFrozen.copy()  # die frozen Kopie, damit die Kanonenpositionen erhalten bleiben
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        painter.translate(self.bulletPos)
        # willkürlicher Winkel, muss später entsprechend F=mg berechent werden
        # np.degrees(self.bulletPos.x()) ist ganz witzig
        angle = 45 if self.currentPlayer == 1 else -45

        painter.drawPixmap(QPoint(0, 0), QPixmap.fromImage(self.bulletImg))

        # pull is the gravitational pull. This variable is added to the y-component of
        # shot_vector IF the value of this variable exceeds 1. This is because
        # shot_vector is of data_type QPoint which only holds Integers
        self.pull += self.gravity_pull * self.mass

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

        painter.translate(-self.bulletPos)
        painter.rotate(-angle)
        painter.end()

        self.display.setPixmap(QPixmap.fromImage(img))
        self.display.show()

        # if bullet hits terrain
        if self.bulletPos.y() >= self.curve[self.bulletPos.x()]:
            self.make_crater(self.bulletPos.x(), 50)
            self.timer.stop()
            self.bulletPos = self.player2Pos + QPoint(0, 0) \
                if self.currentPlayer == 1 else self.player1Pos + QPoint(0, 00)
            self.currentPlayer = 2 if self.currentPlayer == 1 else 1
            self.display.setMouseTracking(True)
            self.redraw_canons(0, 0)

        # if bullet goes out of bounds
        if self.bulletPos.x() >= WIDTH or self.bulletPos.x() <= 0 \
                or self.bulletPos.y() >= HEIGHT or self.bulletPos.y() <= -500:
            self.timer.stop()
            self.bulletPos = self.player2Pos + QPoint(0, 0) \
                if self.currentPlayer == 1 else self.player1Pos + QPoint(0, 0)
            self.currentPlayer = 2 if self.currentPlayer == 1 else 1
            self.display.setMouseTracking(True)
            self.redraw_canons(0, 0)

    def mouse_press_event(self, event):
        self.mousePos = event.pos()
        print(self.mousePos.x(), " ", self.mousePos.y(), " ", self.curve[self.mousePos.x()])
        self.set_takeoff_angle()
        self.display.setMouseTracking(False)
        self.timer.start(1)

    def mouse_move_event(self, event):
        self.redraw_canons(event.pos().x(), event.pos().y())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.timer.stop()
            self.bulletPos = self.player2Pos if self.currentPlayer == 1 else self.player1Pos
            self.currentPlayer = 2 if self.currentPlayer == 1 else 1
            self.display.setMouseTracking(True)
            self.redraw_canons(0, 0)
        if event.key() == Qt.Key_Return:
            self.close()


app = QApplication(sys.argv)
# app.setOverrideCursor(Qt.BlankCursor)  # lässt Mauszeiger verschwinden
Worms()
sys.exit(app.exec_())
