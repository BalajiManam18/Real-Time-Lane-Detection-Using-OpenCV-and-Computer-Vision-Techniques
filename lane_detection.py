import cv2
import numpy as np

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera not detected")
    exit()

prev_left = None
prev_right = None


def region_of_interest(img):

    height, width = img.shape

    mask = np.zeros_like(img)

    polygon = np.array([[
        (int(width * 0.1), height),
        (int(width * 0.9), height),
        (int(width * 0.6), int(height * 0.55)),
        (int(width * 0.4), int(height * 0.55))
    ]])

    cv2.fillPoly(mask, polygon, 255)

    return cv2.bitwise_and(img, mask)


def make_coordinates(image, line_parameters):

    slope, intercept = line_parameters

    y1 = image.shape[0]
    y2 = int(y1 * 0.6)

    if abs(slope) < 0.1:
        return None

    x1 = int((y1 - intercept) / slope)
    x2 = int((y2 - intercept) / slope)

    return np.array([x1, y1, x2, y2])


def average_slope_intercept(image, lines):

    global prev_left, prev_right

    left_fit = []
    right_fit = []

    if lines is None:
        return []

    height, width = image.shape[:2]
    mid_x = width / 2

    for line in lines:

        x1, y1, x2, y2 = line.reshape(4)

        if x1 == x2:
            continue

        slope = (y2 - y1) / (x2 - x1)

        if abs(slope) < 0.35:
            continue

        length = np.sqrt(
            (x2 - x1)**2 +
            (y2 - y1)**2
        )

        if length < 40:
            continue

        parameters = np.polyfit(
            (x1, x2),
            (y1, y2),
            1
        )

        slope = parameters[0]
        intercept = parameters[1]

        if slope < 0 and x1 < mid_x:
            left_fit.append((slope, intercept))

        elif slope > 0 and x1 > mid_x:
            right_fit.append((slope, intercept))

    output = []

    if len(left_fit) > 1:
        prev_left = make_coordinates(
            image,
            np.mean(left_fit, axis=0)
        )

    if len(right_fit) > 1:
        prev_right = make_coordinates(
            image,
            np.mean(right_fit, axis=0)
        )

    if prev_left is not None:
        output.append(prev_left)

    if prev_right is not None:
        output.append(prev_right)

    return output


def draw_lines(image, lines):

    line_image = np.zeros_like(image)

    for line in lines:

        if line is None:
            continue

        x1, y1, x2, y2 = line

        cv2.line(
            line_image,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            10
        )

    return cv2.addWeighted(
        image,
        0.8,
        line_image,
        1,
        1)


while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.flip(frame, 1)

    frame = cv2.resize(frame, (960, 540))

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(
        gray,
        (5, 5),
        0)

    edges = cv2.Canny(
        blur,
        50,
        150)

    cropped_edges = region_of_interest(
        edges)

    kernel = np.ones((5, 5), np.uint8)

    closed = cv2.morphologyEx(
        cropped_edges,
        cv2.MORPH_CLOSE,
        kernel)

    lines = cv2.HoughLinesP(
        closed,
        1,
        np.pi / 180,
        threshold=80,
        minLineLength=30,
        maxLineGap=80)

    averaged_lines = average_slope_intercept(
        frame,
        lines)

    output = draw_lines(
        frame,
        averaged_lines)

    cv2.imshow(
        "Lane Detection",
        output)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()