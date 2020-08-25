import requests
import json
import time
import random
import math
import numpy as np

# 测评服务地址
base_url = "http://127.0.0.1/"
# 请求间隔时间
dt = .5


def inSegment(p,line,line2):
    if line[0][0] == line[1][0]:
        if  p[1] > min(line[0][1],line[1][1]) and p[1] < max(line[0][1],line[1][1]):
            if p[0] >= min(line2[0][0],line2[1][0]) and p[0] <= max(line2[0][0],line2[1][0]):
                return True
    elif line[0][1] == line[1][1]:
        if p[0] > min(line[0][0],line[1][0]) and p[0] < max(line[0][0],line[1][0]):
            if p[1] >= min(line2[0][1],line2[1][1]) and p[1] <= max(line2[0][1],line2[1][1]):
                return True
    else:
        if p[0] > min(line[0][0],line[1][0]) and p[0] < max(line[0][0],line[1][0]):
            if p[1] >= min(line2[0][1],line2[1][1]) and p[1] <= max(line2[0][1],line2[1][1]) and p[0] >= min(line2[0][0],line2[1][0]) and p[0] <= max(line2[0][0],line2[1][0]):
                return True
    return False

def getLinePara(line):
    a = line[0][1] - line[1][1]
    b = line[1][0] - line[0][0]
    c = line[0][0] *line[1][1] - line[1][0] * line[0][1]
    return a,b,c

def getCrossPoint(line1,line2):
    a1,b1,c1 = getLinePara(line1)
    a2,b2,c2 = getLinePara(line2)
    d = a1* b2 - a2 * b1
    p = [0,0]
    if d == 0:
        return ()
    else:
        p[0] = (b1 * c2 - b2 * c1)*1.0 / d
        p[1] = (c1 * a2 - c2 * a1)*1.0 / d
    p = tuple(p)
    if inSegment(p, line1, line2):
        return p
    else:
        return None




def action(speed, angle):
    while True:
        status = requests.get(base_url + 'status').json()['status']
        if status == 'free':
            requests.post(base_url + 'action', json={'speed': speed, 'angle': angle})
            break
        elif status == 'done':
            break
        time.sleep(dt)

def isFree():
        status = requests.get(base_url + 'status').json()['status']
        if status == 'free':
            return 0
        else:
            return -1

if __name__ == "__main__":

    observation = requests.get(base_url + 'scene').json()
    obstacles = observation['obstacles']
    speed = 100
    lines = []
    for i in range(len(obstacles)):
        obstacle_center = obstacles[i]['center']
        obstacle_width = obstacles[i]['width']
        obstacle_rotation = obstacles[i]['rotation']
        if (obstacle_center[0] == 0) or (obstacle_center[1] == 0):
            break
        obstacle_x1 = obstacle_center[0] + ((obstacle_width / 2) * math.cos(math.radians(obstacle_rotation)))
        obstacle_y1 = obstacle_center[1] - ((obstacle_width / 2) * math.sin(math.radians(obstacle_rotation)))
        obstacle_x2 = obstacle_center[0] - ((obstacle_width / 2) * math.cos(math.radians(obstacle_rotation)))
        obstacle_y2 = obstacle_center[1] + ((obstacle_width / 2) * math.sin(math.radians(obstacle_rotation)))
        point1 = [obstacle_x1, obstacle_y1]
        point2 = [obstacle_x2, obstacle_y2]
        line = []
        line.append(point1)
        line.append(point2)
        lines.append(line)

    while True:

        if isFree() != 0:
            time.sleep(dt)
            continue

        observation = requests.get(base_url + 'scene').json()
        player = observation['player']
        player_x = player['center'][0]
        player_y = player['center'][1]
        enemies = observation['enemies']

        targetIndex = -1

        for i in range(len(enemies)):
            enemy_x = enemies[i]['center'][0]
            enemy_y = enemies[i]['center'][1]
            player_enemy = [[player_x, player_y], [enemy_x, enemy_y]]
            score = 0
            flag = 0
            for j in range(len(lines)):
                flag = 0
                if getCrossPoint(player_enemy, lines[j]) != None:
                    flag = 1
                    break
            
            if flag == 1:
                continue
            else:
                if score < enemies[i]['score']:
                    score = enemies[i]['score']
                    targetIndex = i

        if targetIndex != -1:
            if enemies[targetIndex]['center'][0] != player_x:
                angle = math.degrees(math.atan((enemies[targetIndex]['center'][1] - player_y)/(enemies[targetIndex]['center'][0] - player_x)))
                if enemies[targetIndex]['center'][0] - player_x < 0:
                    angle = angle + 180
            else:
                angle = 90
        else:
            angle = random.random() * 360

        action(speed, angle)

        observation = requests.get(base_url + 'scene').json()
        status = requests.get(base_url + 'status').json()['status']

        if status == 'done':
            break
