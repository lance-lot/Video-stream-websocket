# ce.py

import sys


import cv2

import time
import multiprocessing as mp

import numpy as np
import asyncio
import websockets

frame = None


def websocket_process(img_dict):
    # 服务器端主逻辑
    async def main_logic(websocket, path):
        await recv_msg(websocket, img_dict)

    start_server = websockets.serve(main_logic, '0.0.0.0', 7878)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


async def recv_msg(websocket, img_dict):  # websocket发送图片
    recv_text = await websocket.recv()
    print("client connected")
    if recv_text == 'begin':
        while True:
            frame = img_dict['img']
            if isinstance(frame, np.ndarray):
                enconde_data = cv2.imencode('.png', frame)[1]
                enconde_str = enconde_data.tostring()
                try:
                    await websocket.send(enconde_str)
                    time.sleep(0.07)  # 设置时延
                except Exception as e:
                    print(e)
                    return True


def image_put(q, id):
    cap = cv2.VideoCapture(id, cv2.CAP_DSHOW)
    cap.set(6, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))  # 视频流格式
    # cap.set(6, cv2.VideoWriter.fourcc('H', '2', '6', '4'))  # 视频流格式
    cap.set(3, 1280)  # 帧宽
    cap.set(4, 720)  # 帧高  #主要调整图片大小 可设置图片帧率等
    while True:
        ret, frame = cap.read()
        cv2.imshow('frame_resize', frame)
        k = cv2.waitKey(1)
        if k & 0xFF == ord('q'):
            break
        # image_path = "22.jpg"  # 图片路径
        # img = cv2.imread(image_path)
        # q.put(img)
        # q.get() if q.qsize() > 1 else time.sleep(0.01)

        if ret:
            frame = cv2.resize(frame, None, fx=0.7, fy=0.7)  # 压缩图片
            q.put(frame)
            q.get() if q.qsize() > 1 else time.sleep(0.01)


def image_get(q, img_dict):
    while True:
        frame = q.get()
        if isinstance(frame, np.ndarray):
            img_dict['img'] = frame


def run_single_camera(id):
    mp.set_start_method(method='spawn')  # init
    queue = mp.Queue(maxsize=3)
    m = mp.Manager()
    img_dict = m.dict()
    Processes = [mp.Process(target=image_put, args=(queue, id)),
                 mp.Process(target=image_get, args=(queue, img_dict)),
                 mp.Process(target=websocket_process, args=(img_dict,))]

    [process.start() for process in Processes]
    [process.join() for process in Processes]


def run():
    run_single_camera(0)  # 使用内置摄像头 即/dev/video0


if __name__ == '__main__':
    run()

