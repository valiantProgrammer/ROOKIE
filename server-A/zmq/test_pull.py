import zmq
import cv2
import numpy as np

sock = zmq.Context().socket(zmq.PULL)

sock.connect("tcp://localhost:5555")

while True:
    pkt = sock.recv_pyobj()
    print("recv ts:", pkt.get("ts"), "meta:", pkt.get("meta"))
    jpg = pkt.get("jpg")
    if jpg:
        img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
        if img is not None:
            cv2.imshow("recv", img)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
