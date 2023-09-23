import time
import string
import pickle
import math
import logging

import picar

logging.basicConfig(format='[%(asctime)s][%(module)s:%(funcName)s:%(lineno)d|%(levelname)s] -> %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


force_turning = 0  # 0 = random direction, 1 = force left, 2 = force right, 3 = orderdly

ua = picar.UHead(db='config.json')
bw = picar.Backwheels(db='config.json')
lf = picar.Linefollower()

last_angle = 90
direction = ''
last_direction = ['l', 's', 'r', 's']
last_direction_index = 0
#keep_lock_calls = 0

LineSensorStatus = []

DEFAULT_REFERENCES = [150,150,150,150,150]
calibriert = True
"""if calibriert == False:
    references = lf.cali(fw)
else:
    references = DEFAULT_REFERENCES"""

def check_obstacle(direction):
    if direction == 'l':
        ua.turn(180)
    elif direction == 's':
        ua.turn_straight()
    elif direction == 'r':
        ua.turn(0)

    distance = ua.get_distance()
    # tu them
    logger.info("distance: %scm" % distance)

    if distance < 7:
        bw.stop()
        avoid_obstacle(checkoutObstacle())
        time.sleep(1)
        ua.turn_straight()
        bw.left_wheel.speed = 30
        bw.right_wheel.speed = 30
        bw.forward()
def checkoutObstacle():
    vision = getVision()
    logger.info("checkoutObstacle vision:")
    for i in vision:
        logger.info(i)
    if vision == [0,0,0]:
        return "nothing"
    elif vision == [0,1,0]:
        return "single"
    elif vision == [1,1,1]:
        return "single"
    elif vision == [1,0,1]:
        return "double"
    elif vision == [1,1,0]:
        return "singleLeft"
    elif vision == [0,1,1]:
        return "singleRight"
    elif vision == [1,0,0]:
        return "left"
    elif vision == [0,0,1]:
        return "right"

def avoid_obstacle(obstacle):
    global last_angle
    global LineSensorStatus
    logger.info("avoiding obstacle")

    if obstacle=="single":
        avoid_single()
    elif obstacle=="double":
        avoid_double()
    elif obstacle=="singleRight" or "right":
        avoid_single('l')
    elif obstacle=="singleLeft" or "left":
        avoid_single('r')
    else:
        logger.info("%s does not require action" % obstacle)

    ua.turn_straight()

#default direction is right
def avoid_single(direction = 'r'):
    logger.info("avoiding single")

    global last_angle
    ua_direction = 0

    if direction == 'r':
        ua_direction = 180
    else:
        ua_direction = 0

    distance = ua.get_distance()

    while distance < 25:
        distance = ua.get_distance()
        bw.backward(40)
    bw.stop()

    ua.turn_straight()
    bw.forward(20)

    if direction == 'l':
        bw.left_wheel.speed = 60
    else:
        bw.right_wheel.speed = 60

    lock = False
    frontClear = False

    while lock==frontClear:
        distance = ua.get_distance()
        if distance > 27:
            frontClear = True
            break

    ua.turn(ua_direction)

    while lock!=frontClear:
        distance = ua.get_distance()
        if distance < 20:
            lock = True
            break

    bw.left_wheel.speed = 30
    bw.right_wheel.speed =30
    #last_angle = rection
    wait_until_allWhite()

    time.sleep(0.2)
    while not track_caught(direction):
        keep_lock(direction)
        ignore_offTrack(direction)
    #resetting avoidance variables in case another obstacle has to be avoided
    last_angle = 90

def avoid_double():
    global last_angle
    logger.info("avoiding double")

    lock = False
    leftClear = False
    rightClear = False

    bw.forward(30)
    tunnel_passed = False

    last_dist = ua.get_distance()
    time.sleep(0.1)

    dist = ua.get_distance()

    while not tunnel_passed:
        vision = getVision(180, -90, -90, 13)

        if vision==[0, 0, 0]:
            tunnel_passed = True
        elif (vision==[1,1,0]) or (vision==[1,0,0]):
            direction = 'l'
            if direction == 'l':
                ua_direction = 180
            else:
                ua_direction = 0

            distance = ua.get_distance()

            bw.stop()

            ua.turn_straight()
            bw.forward(20)

            if direction == 'l':
                bw.left_wheel.speed = 60
            else:
                bw.right_wheel.speed = 60

            lock = False
            frontClear = False

            while lock == frontClear:
                distance = ua.get_distance()
                if distance > 27:
                    frontClear = True
                    break

            ua.turn(ua_direction)

            while lock != frontClear:
                distance = ua.get_distance()
                if distance < 20:
                    lock = True
                    break

            bw.left_wheel.speed = 30
            bw.right_wheel.speed = 30
            # last_angle = rection
            wait_until_allWhite()

            time.sleep(0.2)
            while not track_caught(direction):
                keep_lock(direction)
                ignore_offTrack(direction)

        elif (vision==[0,1,1]) or (vision==[0,0,1]):
            direction = 'r'
            if direction == 'r':
                ua_direction = 180
            else:
                ua_direction = 0

            bw.stop()

            ua.turn_straight()
            bw.forward(20)

            if direction == 'l':
                bw.left_wheel.speed = 60
            else:
                bw.right_wheel.speed = 60

            lock = False
            frontClear = False

            while lock == frontClear:
                distance = ua.get_distance()
                if distance > 27:
                    frontClear = True
                    break

            ua.turn(ua_direction)

            while lock != frontClear:
                distance = ua.get_distance()
                if distance < 20:
                    lock = True
                    break

            bw.left_wheel.speed = 30
            bw.right_wheel.speed = 30
            # last_angle = rection
            wait_until_allWhite()

            time.sleep(0.2)
            while not track_caught(direction):
                keep_lock(direction)
                ignore_offTrack(direction)
        else:
            bw.left_wheel.speed = 30
            bw.right_wheel.speed = 30
            bw.forward()
            time.sleep(0.5)
            bw.stop()

def getVision(left= 150, right= -30, step= -60, radius = 8):
    vision = []
    for i in range(left, right, step):
        ua.turn(i)
        time.sleep(0.25)
        vision.append(ua.get_distance() < radius)
    ua.turn_straight()
    return vision

def ignore_offTrack(direction):
    LineSensorStatus = lf.read_digital()
    if direction == 'l':
        if 1 in LineSensorStatus[0:1]:
            bw.left_wheel.speed = 50
            bw.right_wheel.speed = 30
            wait_until_allWhite()
    else:
        if 1 in LineSensorStatus[-2:-1]:
            bw.left_wheel.speed = 30
            bw.right_wheel.speed = 50
            wait_until_allWhite()

def track_caught(direction) -> bool:
    LineSensorStatus = lf.read_digital()

    if direction== 'r':
        if True in LineSensorStatus[-2:-1]:
            return False
        elif True in LineSensorStatus[0:3:1]:
            return True
        else:
            logger.info("no lines found! keep driving...")
            return False
    else:
        if True in LineSensorStatus[0:1]:
            return False
        elif True in LineSensorStatus[-3:-1:1]:
            return True
        else:
            logger.info("no lines found! keep driving...")
            return False

def keep_lock(direction):
    global keep_lock_calls
    global last_angle

    if direction == 'r':
        last_dist = ua.get_distance()
        time.sleep(0.1)

        dist = ua.get_distance()
        if dist > 10:

            bw.left_wheel.speed = 30
            bw.right_wheel.speed = 20
            bw.forward()
        elif dist < 7:
            bw.left_wheel.speed = 20
            bw.right_wheel.speed = 30
            bw.forward()
        elif dist < last_dist:
            bw.left_wheel.speed = 30
            bw.right_wheel.speed = 20
            bw.forward()
        elif dist > last_dist:
            bw.left_wheel.speed = 30
            bw.right_wheel.speed = 20
            bw.forward()
        elif (dist == last_dist) and (dist < 10) and (last_dist < 10):
            bw.right_wheel.speed = 30
            bw.left_wheel.speed = 30
            bw.forward()

    else:
        last_dist = ua.get_distance()
        time.sleep(0.1)

        dist = ua.get_distance()
        if dist > 10:
            bw.left_wheel.speed = 20
            bw.right_wheel.speed = 30
            bw.forward()
        elif dist < 7:
            bw.left_wheel.speed = 30
            bw.right_wheel.speed = 20
            bw.forward()
        elif dist < last_dist:
            bw.left_wheel.speed = 20
            bw.right_wheel.speed = 30
            bw.forward()
        elif dist > last_dist:
            bw.left_wheel.speed = 30
            bw.right_wheel.speed = 20
            bw.forward()
        elif (dist == last_dist) and (dist < 10):
            bw.right_wheel.speed = 30
            bw.left_wheel.speed = 30
def wait_until_allWhite():
    while True in lf.read_digital():
        time.sleep(0.1)

if __name__ == '__main__':
    try:
        while True:
            getVision()
    except Exception as e:
        logger.exception("Error..!")
    except KeyboardInterrupt:
        logger.info("Goodbye..!")
