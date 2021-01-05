import pickle
import os
from threading import Thread
import time


def init_face_recognition():
    history = open("/Users/Vincent/Desktop/Programming/Drone/Drone_Blocks/face_history.pickle", "wb")
    pickle.dump([], history)
    history.close()
    current = open("/Users/Vincent/Desktop/Programming/Drone/Drone_Blocks/current_faces.pickle", "wb")
    pickle.dump([], current)
    current.close()

    def face_recognition():
        os.system(
            'python /Users/Vincent/Desktop/pi-face-recognition/pi_face_recognition.py --cascade /Users/Vincent/Desktop/pi-face-recognition/haarcascade_frontalface_default.xml --encodings /Users/Vincent/Desktop/pi-face-recognition/encodings.pickle')
    Thread(target=face_recognition).start()


def get_current_faces():

    try:
        file = open("/Users/Vincent/Desktop/Programming/Drone/Drone_Blocks/current_faces.pickle", "rb")
        faces = pickle.load(file)
        file.close()
        time.sleep(1)
    except EOFError:
        faces = []
    return faces


def get_face_history():
    file = open("/Users/Vincent/Desktop/Programming/Drone/Drone_Blocks/face_history.pickle", "rb")
    faces = pickle.load(file)
    file.close()
    time.sleep(3)
    return faces


def check_if_face_in_current(name):
    time.sleep(5)
    if name in get_current_faces():
        return True
    else:
        return False


def check_if_face_in_history(name):
    time.sleep(5)
    if name in get_face_history():
        return True
    else:
        return False
