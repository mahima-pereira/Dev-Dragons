import cv2
import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\mahim\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Initialize the YOLO model
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Load class labels
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

# Function to detect red cross sign
def detect_red_cross(roi):
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)

    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    mask = mask1 + mask2

    res = cv2.bitwise_and(roi, roi, mask=mask)
    gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return len(contours) > 0

# Function to detect ambulance using YOLO and additional checks
def detect_ambulance(frame):
    height, width = frame.shape[:2]

    # Preprocess the image
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                # Object detected
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # Rectangle coordinates
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    # Debug: print detected classes and confidences
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            print(f"Detected {label} with confidence {confidences[i]}")
            if label == "truck":
                # Ensure coordinates are within image bounds
                if x < 0: x = 0
                if y < 0: y = 0
                if x + w > width: w = width - x
                if y + h > height: h = height - y

                # Draw the bounding box
                color = (0, 255, 0)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # Check for red and blue lights within the bounding box
                roi = frame[y:y + h, x:x + w]
                if roi.size == 0:
                    continue

                hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

                # Red color range
                lower_red1 = np.array([0, 50, 50])
                upper_red1 = np.array([10, 255, 255])
                lower_red2 = np.array([170, 50, 50])
                upper_red2 = np.array([180, 255, 255])
                red_mask = cv2.inRange(hsv_roi, lower_red1, upper_red1) + cv2.inRange(hsv_roi, lower_red2, upper_red2)

                # Blue color range
                lower_blue = np.array([100, 50, 50])
                upper_blue = np.array([140, 255, 255])
                blue_mask = cv2.inRange(hsv_roi, lower_blue, upper_blue)

                # Check if red and blue lights are detected
                red_detected = np.any(red_mask)
                blue_detected = np.any(blue_mask)

                # Detect the red cross sign using the new function
                red_cross_detected = detect_red_cross(roi)

                # OCR to detect "AMBULANCE" text
                text = pytesseract.image_to_string(roi)
                ambulance_text_detected = "AMBULANCE" in text.upper()

                if red_detected and blue_detected and (red_cross_detected or ambulance_text_detected):
                    print("Ambulance detected with red and blue lights, and additional checks")
                    cv2.putText(frame, "Ambulance", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

    return frame

# Load a video
video_path = "C:\\Users\\mahim\\ambu\\New folder\\video3.mp4"  # Provide the full path if necessary
cap = cv2.VideoCapture(video_path)

# Check if the video was successfully loaded
if not cap.isOpened():
    print(f"Error: Unable to open video at {video_path}")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detect ambulance in the frame
        result_frame = detect_ambulance(frame)

        # Display the result frame
        cv2.imshow('Ambulance Detection', result_frame)

        # Exit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
