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

debug = True
wdh = 16
hght = 9
WIDTH = 1355
HEIGHT = int(np.floor(WIDTH * hght / wdh))
# because of how the simulation and the presentation of the simulation works, the resolution determines the
# power of the shot. this code fits the resolutions to the magnitude and creates a polynial function
# that finds the optimal magnitude
res = [1920, 1800, 1700, 1600, 1500, 1400, 1300, 1200, 1100, 1000, 900, 800]
mag = [13.5, 13, 13, 12.2, 17.5, 15.8, 18, 18, 21.8, 18.7, 18.7, 21]
magnitude_scaling_function = np.polyfit(res, mag, 11)
magnitude_scaling_function = np.poly1d(magnitude_scaling_function)


class Worms:
    def __init__(self):

        self.debug_counter = 0

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
        self.player1Pos = QPoint(20 * WIDTH / 100, self.curve[int(np.floor(20 * WIDTH / 100))] - 16)
        self.player2Pos = QPoint(80 * WIDTH / 100, self.curve[int(np.floor(80 * WIDTH / 100))] - 16)
        self.currentPlayer = 1
        self.player1Health = 100
        self.player2Health = 100

        self.worldImg = self.create_world_image()  # das Bild, das immer erhalten und bemalt wird
        self.worldImgFrozen = self.worldImg.copy()  # s. unten
        self.mappainter = QPainter(self.worldImg)
        self.mappainter.setRenderHint(QPainter.Antialiasing)
        self.healthpainter = QPainter(self.worldImg)
        self.healthpainter.setRenderHint(QPainter.Antialiasing)

        self.charsImg = self.create_chars_image()
        self.canonImg1 = self.create_canon_image(1)
        self.canonImg2 = self.create_canon_image(2)
        self.healthbar1 = self.create_healtbar()

        self.windfield = self.get_wind_vector_field()
        self.set_windboxes()
        self.bulletImg = self.create_bullet_image()
        self.bulletPos = self.player1Pos

        # self.make_crater(500, 50)  # demo: x = 500, radius = 50
        self.draw_chars_img(self.charsImg)
        self.redraw_canons(self.player1Pos.x(), self.player1Pos.y())

        # physics variables
        if (WIDTH >= 1600):
            self.travel_rate = 0  # makes bullet travel every travel-rate-th frame
        elif (WIDTH >= 1400 and WIDTH < 1600):
            self.travel_rate = 1
        elif (WIDTH >= 1200 and WIDTH < 1400):
            self.travel_rate = 2
        elif (WIDTH >= 1000 and WIDTH < 1200):
            self.travel_rate = 3
        elif (WIDTH >= 800 and WIDTH < 1000):
            self.travel_rate = 5

        self.rep = -1
        # decreasing this makes shots way less precise
        self.frame_count = self.travel_rate
        self.max_shot_magnitude = magnitude_scaling_function(
            WIDTH) * 4 / 5  # how string the shot will be. the less the travel_rate,
        # the lower this should be
        self.gravity_pull = 9.81
        self.mass = 9 * 10 ** -3  # the mass of default projectile

    def create_healtbar(self):
        bar = np.zeros([7, 60, 4])  # das canon image ist nur 7px*60px groß
        bar[:, :, 3] = 0
        img = QImage(bar, 7, 60, QImage.Format_RGBA8888)
        barpainter = QPainter(img)
        color = QColor(qRgb(0, 135, 0))
        barpainter.setPen(color)
        barpainter.setBrush(color)
        barpainter.drawRect(0, 0, 7, 30)
        barpainter.drawRect(7, 30, 7, 30)
        return img

    def set_takeoff_angle(self):
        # this computes the angle of the shot, measured by the line between the player
        # and the mouseclick and stores this as a Vector in shot_vector.
        # also resets pull and travel_counter ( see animation function)
        px = self.player1Pos.x() if self.currentPlayer == 1 else self.player2Pos.x()
        py = self.player1Pos.y() if self.currentPlayer == 1 else self.player2Pos.y()
        mouse_click_x = self.mousePos.x()
        mouse_click_y = self.mousePos.y()
        if mouse_click_x == px:
            if mouse_click_y <= py:
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

        self.shot_vector = QPoint(np.floor(self.max_shot_magnitude * np.cos(self.takeoff_angle))
                                  , np.floor(self.max_shot_magnitude * np.sin(self.takeoff_angle)))
        self.pull = 0
        self.travel_counter = 0

    # TODO: nicht für alle Pixel, sondern nur für eine Korrdinate berechnen, die übergeben wird
    def get_wind_vector_field(self):
        class obj:
            def __init__(self, width, height):
                self.vector = QPoint(0, 0)
                self.left_boundary = (WIDTH * width) / wdh
                self.right_boundary = (WIDTH * (width + 1)) / wdh
                self.upper_boundary = (HEIGHT * height) / hght
                self.lower_boundary = (HEIGHT * (height + 1)) / hght

        self.setup_windboxes = [[0 for x in range(wdh)] for y in range(hght)]
        for width in range(wdh):
            for height in range(hght):
                self.setup_windboxes[height][width] = obj(width, height)
                # if bullet.x > wind[1], < wind[2], bullet.y > wind[3] , bullet. < wind[4]
        return self.setup_windboxes

    def set_windboxes(self):
        # add to entity vectors
        # get general direction in vector form.  (-10t010,10to-10)

        randx = random.uniform(-5, 5)
        randy = random.uniform(-3, 3)
        self.mappainter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        self.mappainter.setPen(Qt.white)
        self.mappainter.setBrush(Qt.white)
        self.mappainter.drawEllipse(QPoint(HEIGHT - 62, 75), 20, 20)

        # ---------------

        self.mappainter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        self.mappainter.setPen(QPen(Qt.red, 10, Qt.SolidLine))
        self.mappainter.setBrush(Qt.red)

        if randx > 0:
            self.mappainter.drawLine(HEIGHT - 75, 75, HEIGHT - 50, 75)
            self.mappainter.drawLine(HEIGHT - 50, 75, HEIGHT - 60, 60)
            self.mappainter.drawLine(HEIGHT - 50, 75, HEIGHT - 60, 90)

        else:
            self.mappainter.drawLine(HEIGHT - 75, 75, HEIGHT - 50, 75)
            self.mappainter.drawLine(HEIGHT - 75, 75, HEIGHT - 60, 60)
            self.mappainter.drawLine(HEIGHT - 75, 75, HEIGHT - 60, 90)
        # debug
        if debug:
            if self.debug_counter != 0:
                for width in range(wdh):
                    for height in range(hght):
                        self.mappainter.setCompositionMode(QPainter.CompositionMode_Clear)
                        self.mappainter.setPen(Qt.white)
                        self.mappainter.setBrush(Qt.white)

                        self.mappainter.drawLine(int(np.floor((width * WIDTH) / wdh)),
                                                 int(np.floor(height * HEIGHT) / hght),
                                                 5 * self.windfield[height][width].vector.x() + int(
                                                     np.floor((width * WIDTH) / wdh)),
                                                 5 * self.windfield[height][width].vector.y() + int(
                                                     np.floor(height * HEIGHT) / hght))
                        self.mappainter.setPen(QPen(Qt.white, 3, Qt.SolidLine))
                        self.mappainter.drawPoint(
                            5 * self.windfield[height][width].vector.x() + int(np.floor((width * WIDTH) / wdh)),
                            5 * self.windfield[height][width].vector.y() + int(np.floor(height * HEIGHT) / hght))
            self.debug_counter = 1
        for width in range(wdh):
            for height in range(hght):
                # get slightly varying direction from upper value
                vec = QPoint(np.floor(randx + random.uniform(-1.6, 1.6)), np.floor(randy + random.uniform(-1, 1)))
                self.windfield[height][width].vector = vec  # set direction
            if debug:
                self.mappainter.setPen(QPen(Qt.red, 3, Qt.SolidLine))
                self.mappainter.setBrush(Qt.red)
                self.mappainter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                self.mappainter.drawLine(int(np.floor((width * WIDTH) / wdh)), int(np.floor(height * HEIGHT) / hght),
                                         5 * vec.x() + int(np.floor((width * WIDTH) / wdh)),
                                         5 * vec.y() + int(np.floor(height * HEIGHT) / hght))
                self.mappainter.setPen(QPen(Qt.blue, 4, Qt.SolidLine))
                self.mappainter.drawPoint(5 * vec.x() + int(np.floor((width * WIDTH) / wdh)),
                                          5 * vec.y() + int(np.floor(height * HEIGHT) / hght))

    def create_curve(self):
        random1 = [random.uniform(0, 2 * pi) for _ in range(len(self.W))]
        random2 = [random.uniform(-1, 1) for _ in range(len(self.W))]
        return [self.get_curve_fx(i, random1, random2) for i in range(WIDTH)]

    # liefert für x den Wert f(x) der Kurve für die Landschaft
    def get_curve_fx(self, x, r1, r2):
        fx = 0
        for i in range(len(self.W)):
            fx += 1 / np.sqrt(self.W[i]) * np.sin(self.W[i] * x + r1[i]) * r2[i]
        return fx * 3 + HEIGHT / 1.9  # willkürliche Skalierung (Ausprobieren)

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
        # x = self.bullet1Pos.x() beim aufschlag der kugel
        # setzt den painter auf den "Radiermodus"
        self.mappainter.setCompositionMode(QPainter.CompositionMode_Clear)
        self.mappainter.setPen(Qt.white)
        self.mappainter.setBrush(Qt.white)
        self.old_crater_yPos = self.curve[x]
        self.old_player1Pos = self.player1Pos
        self.old_player2Pos = self.player2Pos
        # zeichnet Krater an die Funktionsstelle von 500 mit Radius 50
        self.mappainter.drawEllipse(QPoint(x, self.curve[x]), radius + 5, radius + 5)

        for width in range(-radius, 0):
            height = np.floor(
                np.sqrt(
                    np.abs(
                        np.abs(
                            np.power(radius, 2))
                        -
                        np.power(width, 2))))
            if not self.curve[x + width] > self.curve[x] + height + 5:
                self.curve[x + width] = self.curve[x] + height + 5
            if not self.curve[x - width] > self.curve[x] + height + 5:
                self.curve[x - width] = self.curve[x] + height + 5
        self.curve[x] += radius

        # debug paint
        if debug:
            self.mappainter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            self.mappainter.setPen(QPen(Qt.red, 3, Qt.SolidLine))
            self.mappainter.setBrush(Qt.red)
            for i in range(len(self.curve)):
                self.mappainter.drawPoint(i, self.curve[i])
            self.mappainter.setCompositionMode(QPainter.CompositionMode_Clear)
            self.mappainter.setPen(Qt.white)
            self.mappainter.setBrush(Qt.white)

        if ((np.sqrt(np.power(self.old_player1Pos.x() - x, 2)
                     + np.power(self.old_player1Pos.y() - self.old_crater_yPos, 2)) < radius)):
            self.player1Pos = QPoint(self.old_player1Pos.x(), -12 + self.curve[self.old_player1Pos.x()])
            self.mappainter.drawEllipse(QPoint(self.old_player1Pos.x(), self.old_player1Pos.y()), 16, 16)
            self.player1Health -= 0.8 * (radius * 1.8 - np.sqrt(np.power(self.old_player1Pos.x() - x, 2)
                                                                + np.power(self.old_player1Pos.y() - self.curve[x], 2)))

            print("Player 1 took ", int(0.8 * (radius * 1.8 - np.sqrt(np.power(self.old_player1Pos.x() - x, 2)
                                                                      + np.power(
                self.old_player1Pos.y() - self.curve[x], 2)))), " damage!")
            print("Player 1 has ", int(self.player1Health), " health!")
            if self.player1Health <= 0:
                print("game over! Player 2 won!")
                sys.exit()

        if (np.sqrt(np.power(self.old_player2Pos.x() - x, 2)
                    + np.power(self.old_player2Pos.y() - self.old_crater_yPos, 2)) < radius):
            self.player2Pos = QPoint(self.old_player2Pos.x(), -12 + self.curve[self.old_player2Pos.x()])
            self.mappainter.drawEllipse(QPoint(self.old_player2Pos.x(), self.old_player2Pos.y()), 16, 16)
            self.player2Health -= 0.8 * (radius * 1.8 - np.sqrt(np.power(self.old_player2Pos.x() - x, 2)
                                                                + np.power(self.old_player2Pos.y() - self.curve[x], 2)))

            print("Player 2 took ", int(radius * 1.8 - np.sqrt(np.power(self.old_player2Pos.x() - x, 2)
                                                               + np.power(self.old_player2Pos.y() - self.curve[x], 2))),
                  " damage!")
            print("Player 2 has ", int(self.player2Health), " health!")
            if self.player2Health <= 0:
                print("game over! Player 1 won!")
                sys.exit()

        self.charsImg = self.create_chars_image()
        self.draw_chars_img(self.charsImg)

    def create_chars_image(self):
        chars = np.zeros([WIDTH, HEIGHT, 4])  # TODO: char image kleiner machen und in zwei einzelne aufsplitten
        chars[:, :, 3] = 0  # macht Ebene transparent
        img = QImage(chars, WIDTH, HEIGHT, QImage.Format_RGBA8888)


        return img

    def draw_chars_img(self, img):
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

            temp = self.windfield[int(np.floor(hght * self.bulletPos.y() / HEIGHT))][
                int(np.floor(wdh * self.bulletPos.x() / WIDTH))].vector
            temp = QPoint(temp.x() / 3, temp.y() / 3)
            self.rep += 1
            if self.rep >= 5:
                self.shot_vector += temp
                self.rep = -1
            #shot += temp
            self.bulletPos = shot

        self.frame_count += 1

        painter.translate(-self.bulletPos)
        painter.rotate(-angle)
        painter.end()

        self.display.setPixmap(QPixmap.fromImage(img))
        self.display.show()



        # if bullet goes out of bounds
        if self.bulletPos.x() >= WIDTH or self.bulletPos.x() <= 0 \
                or self.bulletPos.y() >= HEIGHT or self.bulletPos.y() <= -500:
            self.timer.stop()
            self.bulletPos = self.player2Pos + QPoint(0, -8) \
                if self.currentPlayer == 1 else self.player1Pos + QPoint(0, 0)
            self.currentPlayer = 2 if self.currentPlayer == 1 else 1
            self.display.setMouseTracking(True)
            self.set_windboxes()
            self.redraw_canons(0, 0)

        # if bullet hits terrain
        if self.bulletPos.y() >= self.curve[self.bulletPos.x()]:
            self.make_crater(self.bulletPos.x(), 50)
            self.timer.stop()
            self.bulletPos = self.player2Pos + QPoint(0, -8) \
                if self.currentPlayer == 1 else self.player1Pos + QPoint(0, 00)
            self.currentPlayer = 2 if self.currentPlayer == 1 else 1
            self.display.setMouseTracking(True)
            self.set_windboxes()
            self.redraw_canons(0, 0)


    def move_tank_left(self):
        self.mappainter.setCompositionMode(QPainter.CompositionMode_Clear)
        self.mappainter.setPen(Qt.white)
        self.mappainter.setBrush(Qt.white)
        if self.currentPlayer == 1:
            self.mappainter.drawEllipse(QPoint(self.player1Pos.x(), self.player1Pos.y()), 16, 16)
            self.player1Pos = QPoint(self.player1Pos.x() - 4, self.curve[self.player1Pos.x() - 4] -16)
            self.bulletPos = self.player1Pos

        else:
            self.mappainter.drawEllipse(QPoint(self.player2Pos.x(), self.player2Pos.y()), 16, 16)
            self.player2Pos = QPoint(self.player2Pos.x() - 4, self.curve[self.player2Pos.x() - 4] -16)
            self.bulletPos = self.player2Pos
        self.charsImg = self.create_chars_image()
        self.draw_chars_img(self.charsImg)
        self.redraw_canons(WIDTH / 2, HEIGHT / 2)


    def move_tank_right(self):
        self.mappainter.setCompositionMode(QPainter.CompositionMode_Clear)
        self.mappainter.setPen(Qt.white)
        self.mappainter.setBrush(Qt.white)
        if self.currentPlayer == 1:
            self.mappainter.drawEllipse(QPoint(self.player1Pos.x(), self.player1Pos.y()), 16, 16)
            self.player1Pos = QPoint(self.player1Pos.x() + 4, self.curve[self.player1Pos.x() + 4] -16)
            self.bulletPos = self.player1Pos
        else:
            self.mappainter.drawEllipse(QPoint(self.player2Pos.x(), self.player2Pos.y()), 16, 16)
            self.player2Pos = QPoint(self.player2Pos.x() + 4, self.curve[self.player2Pos.x() + 4] -16)
            self.bulletPos = self.player2Pos
        self.charsImg = self.create_chars_image()
        self.draw_chars_img(self.charsImg)
        self.redraw_canons(WIDTH / 2, HEIGHT / 2)



    def mouse_press_event(self, event):
        self.mousePos = event.pos()
        #print(self.mousePos.x(), " ", self.mousePos.y(), " ", self.curve[self.mousePos.x()])
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
        if event.key() == Qt.Key_A:
            self.move_tank_left()
        if event.key() == Qt.Key_D:
            self.move_tank_right()



app = QApplication(sys.argv)
# app.setOverrideCursor(Qt.BlankCursor)  # lässt Mauszeiger verschwinden
Worms()
sys.exit(app.exec_())