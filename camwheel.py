#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright © 2010  Santiago Piccinini
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import math
import time

import cv
import uinput

class WheelMouse(object):
    def __init__(self):
        capabilities = {uinput.EV_REL: [uinput.REL_X, uinput.REL_Y],
                        uinput.EV_KEY: [uinput.BTN_LEFT, uinput.BTN_RIGHT]}

        self.device = uinput.Device(name="python-uinput-mouse",
                               capabilities=capabilities)

        self._dangle = 0
        self._last_angle = 0

    def update(self, angle):
        print angle
        if angle is not None:
            dangle = angle - self._last_angle
            self._dangle = dangle
            self._last_angle = angle
            self.emit()

    def emit(self):
        val = self.abs_from_dangle()
        if val:
            print "val", val
            self.device.emit(uinput.EV_REL, uinput.REL_X, self.abs_from_dangle())

    def abs_from_dangle(self):
        return int(self._dangle*200)


class WheelJoystick(object):
    def __init__(self):
        capabilities = {uinput.EV_ABS: [uinput.ABS_X, uinput.ABS_Y],
                        uinput.EV_KEY: [uinput.BTN_LEFT, uinput.BTN_RIGHT]}
        abs_parameters = {uinput.ABS_X:(0, 255, 0, 0), uinput.ABS_Y:(0, 255, 0, 0)} #abs_min, abs_max, abs_fuzz, abs_flat

        self.device = uinput.Device(name="python-uinput-joystick",
                           capabilities=capabilities, abs_parameters=abs_parameters)
        self.wheel_position = 127
        self.emit()
    
    def update(self, angle):
        if angle is not None:
            self.wheel_position = int(angle * (255./3.14) + 127)
            self.emit()

    def emit(self):
        print self.wheel_position
        self.device.emit(uinput.EV_ABS, uinput.ABS_X, self.wheel_position)


def detect(image, config):
    angle = None
    image_size = cv.GetSize(image)
    # create grayscale version
    grayscale = cv.CreateImage(image_size, 8, 1)
    cv.CvtColor(image, grayscale, cv.CV_BGR2GRAY)
    if config["EqualizeHist"]:
        cv.EqualizeHist(grayscale, grayscale)

    pattern_width = 5
    pattern_height = 4
    found, corners = cv.FindChessboardCorners(grayscale, (pattern_width, pattern_height))

    if found:
        new_corners = cv.FindCornerSubPix(grayscale, corners, (11, 11), (-1, -1), (cv.CV_TERMCRIT_EPS+cv.CV_TERMCRIT_ITER, 30, 0.1))
        angle = corners_to_angle(new_corners)
        #print "angle: ", angle

        def to_int(t):
            return (int(t[0]), int(t[1]))

        #nc = [to_int(corner) for corner in new_corners]
        #cv.Line( grayscale, nc[0], nc[4], (255,0,0), 2)
        #cv.Line( grayscale, nc[4], nc[19], (0,255,0),2)
        #cv.Line( grayscale, nc[19], nc[15], (0,0,255),2)
        #cv.Line( grayscale, nc[15], nc[0], (255,255,0),2)

    #cv.ShowImage('Processed', grayscale)
    return angle


def corners_to_angle(corners):
    adj = corners[19][0] - corners[15][0]
    hip = math.sqrt(pow(corners[19][0] - corners[15][0], 2) + pow(corners[19][1] - corners[15][1], 2))
    angle = math.acos(adj/hip)
    if corners[19][1] < corners[15][1]:
        angle *= -1.0
    return angle


if __name__ == "__main__":
    # create windows
    cv.NamedWindow('Raw', cv.CV_WINDOW_AUTOSIZE)
    #cv.NamedWindow('Processed', cv.CV_WINDOW_AUTOSIZE)

    # create capture
    device = 0 # assume we want first device
    capture = cv.CaptureFromCAM(0)
    cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 640)
    cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 480)

    # Check device
    if not capture:
        print "Error opening capture device"
        sys.exit(1)

    config = {"EqualizeHist":False}

    wheel = WheelJoystick()

    while 1:
        # capture the current frame
        frame = cv.QueryFrame(capture)
        if frame is None:
            break

        # mirror
        cv.Flip(frame, None, 1)
        angle = detect(frame, config)
        wheel.update(angle)

        # display webcam image
        #cv.ShowImage('Raw', frame)

        # handle events
        k = cv.WaitKey(10)

        if k == 1048680: # h
            wheel.device.emit(uinput.EV_KEY, uinput.BTN_LEFT, 1)
            time.sleep(0.5)
            wheel.device.emit(uinput.EV_KEY, uinput.BTN_LEFT, 0)

