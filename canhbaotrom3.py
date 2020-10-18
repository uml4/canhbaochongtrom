import cv2
import math
import numpy as np


# Ham detect car và bus tu anh input
def get_object(net, image, conf_threshold=0.4, h=360, w=460):
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()
    boxes = []

    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            idx = int(detections[0, 0, i, 1])
            # Phát hiện các đối tượng dựa trên các ID của label
            if 6 <= idx <= 7 or  idx == 14 or  idx == 2  :
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                box = [startX, startY, endX - startX, endY - startY, idx]
                boxes.append(box)

    return boxes


# Ham check xem old hay new
def is_old(center_Xd, center_Yd, boxes):
    for box_tracker in boxes:
        (xt, yt, wt, ht, idx) = [int(c) for c in box_tracker]
        center_Xt, center_Yt = int((xt + (xt + wt)) / 2.0), int((yt + (yt + ht)) / 2.0)
        distance = math.sqrt((center_Xt - center_Xd) ** 2 + (center_Yt - center_Yd) ** 2)

        if distance < max_distance:
            return True
    return False

# trả về nội dung tọa độ của  vật thể và vị trí ID của vật thê (tên)
def get_box_info(box):
    (x, y, w, h, idx) = [int(v) for v in box]
    center_X = int((x + (x + w)) / 2.0)
    center_Y = int((y + (y + h)) / 2.0)
    return x, y, w, h, center_X, center_Y, idx


# Labels of Network.
classNames = { 0: 'background',
    1: 'aeroplane', 2: 'xe dap', 3: 'bird', 4: 'boat',
    5: 'bottle', 6: 'bus', 7: 'oto', 8: 'cat', 9: 'chair',
    10: 'cow', 11: 'diningtable', 12: 'dog', 13: 'horse',
    14: 'xe may', 15: 'person', 16: 'pottedplant',
    17: 'sheep', 18: 'sofa', 19: 'train', 20: 'tvmonitor' }

# Define cac tham so

prototype_url = 'models/MobileNetSSD_deploy.prototxt'
model_url = 'models/MobileNetSSD_deploy.caffemodel'
video_path = 'xemay2.mp4'

max_distance = 50
input_h = 360
input_w = 480
laser_line = input_h - 50
laser_line2 = input_h - 310
laser_line3 = input_w - 50
laser_line4 = input_w - 410

net = cv2.dnn.readNetFromCaffe(prototype_url, model_url)
vid = cv2.VideoCapture(video_path)

# Khoi tao tham so
frame_count = 0
car_number = 0
obj_cnt = 0
curr_trackers = []

while vid.isOpened():

    laser_line_color = (0, 0, 255)
    boxes = []

    # Doc anh tu video
    _, frame = vid.read()
    if frame is None:
        break

    # Resize nho lai
    frame = cv2.resize(frame, (input_w, input_h))

    # Duyet qua cac doi tuong trong tracker
    old_trackers = curr_trackers
    curr_trackers = []

    for car in old_trackers:

        # Update tracker
        tracker = car['tracker']
        (_, box) = tracker.update(frame)

     #   if 'id_class' not in car.values():
    #      car['id_class'] = -1
        #if car['id_class'] is None:
        #    car['id_class'] = -1    

        # gán tham so id_class vao  
        box  =  box + (car['id_class'],) 
        #print(box)
        
        
        boxes.append(box)

        new_obj = dict()
        new_obj['tracker_id'] = car['tracker_id']
        new_obj['tracker'] = tracker
        new_obj['id_class'] = car['id_class']

        # Tinh toan tam doi tuong
        x, y, w, h, center_X, center_Y, class_id = get_box_info(box)

        # Ve hinh chu nhat quanh doi tuong
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Ve hinh tron tai tam doi tuong
        cv2.circle(frame, (center_X, center_Y), 4, (0, 255, 0), -1)

        # Draw label and confidence of prediction in frame resized
        #Comment đoạn này lại nếu muốn xóa tên đồ vật
        if class_id in classNames:
            label = classNames[class_id] 
            labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

            yLeftBottom = max(y, labelSize[1])
            cv2.rectangle(frame, (x, y - labelSize[1]),
                                    (x + labelSize[0], y + baseLine),
                                    (255, 255, 255), cv2.FILLED)
            cv2.putText(frame, label, (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))     





        # So sanh tam doi tuong voi duong laser line  center_X > laser_line3 or center_X < laser_line4
        if   center_Y > laser_line :
            # Neu vuot qua thi khong track nua ma dem xe
            laser_line_color = (0, 255, 255)
            car_number += 1
            print("Phat hien có sự thay đổi vị trí đồ vật")
        else:
            # Con khong thi track tiep
            curr_trackers.append(new_obj)

    # Thuc hien object detection moi 5 frame
    if frame_count % 5 == 0:
        # Detect doi tuong
        boxes_d = get_object(net, frame)

        for box in boxes_d:
            old_obj = False

            xd, yd, wd, hd, center_Xd, center_Yd, class_id = get_box_info(box)

            if center_Yd <= laser_line - max_distance:

                # Duyet qua cac box, neu sai lech giua doi tuong detect voi doi tuong da track ko qua max_distance thi coi nhu 1 doi tuong
                if not is_old(center_Xd, center_Yd, boxes):
                    cv2.rectangle(frame, (xd, yd), ((xd + wd), (yd + hd)), (0, 255, 255), 2)
                    # Tao doi tuong tracker moi
                    

                    tracker = cv2.TrackerMOSSE_create()
   
                    obj_cnt += 1
                    new_obj = dict()
                    #loai tham so id ra vi ham tracker ko cho phep
                    n_box = box.copy()
                    n_box.pop(4)
                    tracker.init(frame, tuple(n_box))
                    #print(box[4])
                    new_obj['tracker_id'] = obj_cnt
                    new_obj['tracker'] = tracker
                    new_obj['id_class'] = box[4]

                    curr_trackers.append(new_obj)

    # Tang frame
    frame_count += 1

    # Hien thi so xe

    cv2.putText(frame, "So lan di chuyen: " + str(car_number), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255 , 0), 2)
    cv2.putText(frame, "Press Esc to quit", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

    # Draw laser line
    cv2.line(frame, (0, laser_line), (input_w, laser_line), laser_line_color, 2)
    cv2.putText(frame, "Laser line", (10, laser_line - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, laser_line_color, 2)

    # ve các laser line  2 3 4
   

    # Frame
    cv2.imshow("Image", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break

vid.release()
cv2.destroyAllWindows
