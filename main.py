import cv2
import os
import sys
import time
# Імпортуємо вашу функцію з іншого файлу
from display_image import display_opencv_on_framebuffer

# --- Налаштування ---
FB_DEVICE = "/dev/fb0"       # Шлях до вашого фреймбуфера
VIDEO_SOURCE = 0             # Джерело відео (0 - зазвичай перша веб-камера)
ROTATE_FRAME = cv2.ROTATE_180 # Поворот кадру (як у вашому прикладі)
# --- --- --- --- ---

def main():
    # --- Підготовка терміналу ---
    # (Вимикаємо курсор та очищуємо екран)
    print("Запуск відеопотоку на фреймбуфер...")
    os.system("setterm -cursor off")
    os.system("clear")

    # --- Відкриття відеоджерела ---
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print(f"Помилка: Неможливо відкрити відеоджерело {VIDEO_SOURCE}", file=sys.stderr)
        os.system("setterm -cursor on") # Відновлюємо курсор
        os.system("clear")
        sys.exit(1)
    
    print(f"Відеопотік з {VIDEO_SOURCE} відкрито.")
    print(f"Виведення на {FB_DEVICE}. Натисніть Ctrl+C для виходу.")

    try:
        while True:
            # --- Читання кадру ---
            ret, frame = cap.read()
            if not ret:
                print("Помилка: Неможливо отримати кадр (кінець потоку?).", file=sys.stderr)
                break
            
            # --- Обробка кадру ---
            # Я помітив, що у вашому прикладі ви повертали зображення.
            # Якщо це не потрібно, закоментуйте або видаліть наступний рядок.
            if ROTATE_FRAME is not None:
                frame_processed = cv2.rotate(frame, ROTATE_FRAME)
            else:
                frame_processed = frame

            # --- Відображення кадру ---
            if not display_opencv_on_framebuffer(frame_processed, FB_DEVICE):
                print("Помилка: Не вдалося записати у фреймбуфер. Вихід...", file=sys.stderr)
                break
    
    except KeyboardInterrupt:
        # Обробка Ctrl+C для чистого виходу
        print("\nЗупинка відеопотоку...")
    
    except Exception as e:
        print(f"Сталася неочікувана помилка: {e}", file=sys.stderr)

    finally:
        # --- Очищення ---
        print("Відновлення терміналу та звільнення пристроїв...")
        if cap.isOpened():
            cap.release()
        # Повертаємо курсор та очищуємо екран
        os.system("setterm -cursor on")
        os.system("clear")
        print("Роботу завершено.")

if __name__ == "__main__":
    main()