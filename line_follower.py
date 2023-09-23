#!/usr/bin/env python
'''
**********************************************************************
* Filename    : line_follower
* Description : An example for sensor car kit to followe line
* Author      : Dream
* Brand       : SunFounder
* E-mail      : service@sunfounder.com
* Website     : www.sunfounder.com
* Update      : Dream    2016-09-21    New release
**********************************************************************
'''
import time
import logging
import obstacleAvoidance as oa
import picar

REFERENCES = [170, 170, 170, 170, 170]
calibrate = False #True
forward_speedLeft = 30
forward_speedRight = 30
backward_speedLeft = 30
backward_speedRight = 30
base_speed = 30
fast_speed = 70

#turning_angle = 40

logging.basicConfig(format='[%(asctime)s][%(module)s:%(funcName)s:%(lineno)d|%(levelname)s] -> %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

bw = picar.Backwheels(db='config.json')
lf = picar.Linefollower(references=REFERENCES)

max_off_track_count = 10
max_on_track_count = 300

delay = 0.0005

bw.ready()

def straight_run():
    while True:
        bw.speedLeft = 70
        bw.speedRight = 70
        bw.forward()

def setup():
    if calibrate:
        cali()

def main():
    #global turning_angle
    off_track_count = 0 # experimental value
    on_track_count = 0
    # True just have turned right , False just have turned left
    last_forward_direction = 0
    last_backward_direction = 0
    bw.speedLeft = forward_speedLeft
    bw.speedRight = forward_speedRight
    count = 0
    # calculate possible speed factors for proper turning (you might want to adjust those)
    a_step = 0.9
    b_step = 0.7
    c_step = 0.5
    d_step = 0.3
    e_step = 0.1

    #bw.forward()
    while True:
        oa.check_obstacle('s')
        lt_status_now = lf.read_digital()
        logging.info(lt_status_now)

        # Angle calculate
        if  lt_status_now == [0,0,1,0,0]:
            step = 1
        elif lt_status_now == [0,1,1,0,0] or lt_status_now == [0,0,1,1,0]:
            step = a_step
        elif lt_status_now == [0,1,0,0,0] or lt_status_now == [0,0,0,1,0] :
            step = b_step
        elif lt_status_now == [1,1,0,0,0] or lt_status_now == [0,0,0,1,1] or lt_status_now == [1,0,0,0,0] or lt_status_now == [0,0,0,0,1]:
            step = c_step
        elif lt_status_now == [1,1,1,0,0] or lt_status_now == [0,0,1,1,1] or lt_status_now == [1,1,1,1,0] or lt_status_now == [0,1,1,1,1]:
            step = d_step
        elif lt_status_now == [1,1,1,1,1]:
            step = 1

        # Direction calculate
        if  lt_status_now in ([0,0,1,0,0]):
            off_track_count = 0
            on_track_count = 0
            last_forward_direction = 0
            # same speed for both wheels
            bw.left_wheel.speed = base_speed
            bw.right_wheel.speed = base_speed
            bw.forward()

        # turn right
        elif lt_status_now in ([0,0,1,1,0], [0,0,0,1,0], [0,0,0,1,1], [0,0,0,0,1]):
            off_track_count = 0
            on_track_count = 0
            count = 0
            last_forward_direction = 2
            bw.left_wheel.speed = int(forward_speedLeft * step)
            bw.right_wheel.speed = int(forward_speedRight)
            bw.forward()

        elif lt_status_now in ([0,0,1,1,1], [0,1,1,1,1]):
            off_track_count = 0
            on_track_count = 0
            last_forward_direction = 2
            bw.left_wheel.speed = int(forward_speedRight)
            bw.right_wheel.speed = int(forward_speedRight)
            bw.forward()

        # turn left
        elif lt_status_now in ([0,1,1,0,0], [0,1,0,0,0], [1,1,0,0,0], [1,0,0,0,0]):
            off_track_count = 0
            on_track_count = 0
            count = 0
            last_forward_direction = 1
            bw.left_wheel.speed = int(forward_speedLeft)
            bw.right_wheel.speed = int(forward_speedRight * step)
            bw.forward()

        elif lt_status_now in ([1,1,1,0,0], [1,1,1,1,0]):
            off_track_count = 0
            on_track_count = 0
            last_forward_direction = 1
            bw.left_wheel.speed = int(forward_speedLeft)
            bw.right_wheel.speed = int(forward_speedLeft)
            bw.forward()

        elif lt_status_now == [0,0,0,0,0]:
            off_track_count += 1
            if off_track_count > max_off_track_count:
                # make sure picar drives in a curve backwards
                if last_forward_direction == 0:
                    bw.left_wheel.speed = base_speed
                    bw.right_wheel.speed = base_speed
                    bw.backward()

                    lf.wait_tile_center()
                    bw.stop()

                if last_forward_direction == 1:
                    bw.left_wheel.speed = int(base_speed*0.1)
                    bw.right_wheel.speed = base_speed
                    bw.backward()

                    lf.wait_tile_center()
                    bw.stop()
                    last_backward_direction = 2

                if last_forward_direction == 2:
                    bw.left_wheel.speed = base_speed
                    bw.right_wheel.speed = int(base_speed*0.1)
                    bw.backward()

                    lf.wait_tile_center()
                    bw.stop()
                    last_backward_direction = 1

                # fw.turn(turning_angle)
                time.sleep(0.2)
                bw.left_wheel.speed = base_speed
                bw.right_wheel.speed = base_speed
                bw.forward()
                time.sleep(0.2)

        else:
            off_track_count = 0

        time.sleep(delay)

def cali():
    references = [0, 0, 0, 0, 0]
    logging.info("cali for module -> first put all sensors on white, then put all sensors on black")
    mount = 100
    time.sleep(4)
    logging.info("cali white")
    time.sleep(4)
    white_references = lf.get_average(mount)
    time.sleep(4)

    logging.info("cali black")
    time.sleep(4)
    black_references = lf.get_average(mount)
    time.sleep(2)

    for i in range(0, 5):
        references[i] = (white_references[i] + black_references[i]) / 2
    lf.references = references
    logging.info('Middle references: %d' % (references))
    time.sleep(1)

def destroy():
    bw.stop()

if __name__ == '__main__':
    try:
        while True:
            #setup()
            main()
    except Exception as e:
        logger.exception("Error ...!")
        destroy()
    except KeyboardInterrupt:
        logger.info("Keyboard Interrupt - Goodbye")
        destroy()
