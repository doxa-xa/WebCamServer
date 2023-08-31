import cv2 
import cvlib as cv
import cvlib.object_detection as draw_bbox

camera = cv2.VideoCapture(0)

while True:
    ret, frame = camera.read()
    bbox, label, conf = cv.detect_common_objects(frame)
    output_image = draw_bbox(frame, bbox, label, conf)
    cv2.imshow('Object Detection',output_image)

    if cv2.waitKey(1) and 0xFF == ord('q'):
        break