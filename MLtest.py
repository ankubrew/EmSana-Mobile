import cv2
from ultralytics import YOLO

model = YOLO("emotionsbest.pt")

# Загружаем встроенный в OpenCV быстрый детектор лиц (Haar Cascade)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

cap = cv2.VideoCapture(0)
print("Камера запущена! Чтобы выйти, нажми 'q'.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Переводим кадр в ЧБ для поиска лица
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # ШАГ 1: Ищем все лица в кадре (работает на любом расстоянии)
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

    # Перебираем найденные лица
    for (x, y, w, h) in faces:
        # Немного расширяем рамку захвата, чтобы лицо влезло целиком
        margin = int(h * 0.1)
        y1, y2 = max(0, y - margin), min(frame.shape[0], y + h + margin)
        x1, x2 = max(0, x - margin), min(frame.shape[1], x + w + margin)

        # Вырезаем лицо из кадра
        face_crop = frame[y1:y2, x1:x2]
        if face_crop.size == 0:
            continue

        # Делаем вырезанное лицо черно-белым (как в датасете)
        face_gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        face_gray_3c = cv2.cvtColor(face_gray, cv2.COLOR_GRAY2BGR)

        # ШАГ 2: Отправляем в YOLO ТОЛЬКО вырезанное лицо
        # verbose=False отключает спам в консоль
        results = model.predict(source=face_gray_3c, conf=0.45, device='cpu', verbose=False)

        # Если YOLO нашла эмоцию, достаем её название
        if len(results[0].boxes) > 0:
            # Берем самую уверенную эмоцию
            best_box = results[0].boxes[0] 
            class_id = int(best_box.cls[0])
            conf = float(best_box.conf[0])
            emotion_name = model.names[class_id]

            # Рисуем красивую рамку и подписываем эмоцию на оригинальном видео
            label = f"{emotion_name} {conf:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    cv2.imshow("EmSana Pro Emotion Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()