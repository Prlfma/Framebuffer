import cv2
import numpy as np
import sdl2
import sdl2.ext

def frame_to_texture(renderer, frame):
    """Конвертація OpenCV BGR кадру в SDL текстуру."""
    h, w, _ = frame.shape

    # Конвертація BGR → RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Створення поверхні з масиву
    surface = sdl2.SDL_CreateRGBSurfaceFrom(
        rgb.ctypes.data,
        w, h, 24,
        w * 3,
        0x0000FF,  # Rmask
        0x00FF00,  # Gmask
        0xFF0000,  # Bmask
        0
    )

    texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
    sdl2.SDL_FreeSurface(surface)

    return texture, w, h


def main():
    # --------------------
    # 1. Відкриваємо камери
    # --------------------
    cam1 = cv2.VideoCapture(0)
    cam2 = cv2.VideoCapture(1)

    if not cam1.isOpened() or not cam2.isOpened():
        print("Не можу відкрити одну з камер")
        return

    # Можна задати розмір кадру:
    WIDTH = 640
    HEIGHT = 480
    cam1.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cam1.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cam2.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cam2.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    # --------------------
    # 2. SDL вікно й рендер
    # --------------------
    sdl2.ext.init()

    window = sdl2.ext.Window("Two Cameras", size=(WIDTH * 2, HEIGHT))
    window.show()

    renderer = sdl2.SDL_CreateRenderer(window.window, -1, 0)

    running = True
    while running:
        # Події SDL → дозволяють закривати вікно
        for e in sdl2.ext.get_events():
            if e.type == sdl2.SDL_QUIT:
                running = False

        # --------------------
        # 3. Читаємо кадри з камер
        # --------------------
        ret1, frame1 = cam1.read()
        ret2, frame2 = cam2.read()

        if not ret1 or not ret2:
            continue

        # --------------------
        # 4. Створюємо SDL texture з кадрів
        # --------------------
        tex1, w1, h1 = frame_to_texture(renderer, frame1)
        tex2, w2, h2 = frame_to_texture(renderer, frame2)

        # --------------------
        # 5. Малюємо
        # --------------------
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(renderer)

        # Ліва камера
        dst1 = sdl2.SDL_Rect(0, 0, w1, h1)
        sdl2.SDL_RenderCopy(renderer, tex1, None, dst1)

        # Права камера
        dst2 = sdl2.SDL_Rect(w1, 0, w2, h2)
        sdl2.SDL_RenderCopy(renderer, tex2, None, dst2)

        sdl2.SDL_RenderPresent(renderer)

        # Звільняємо тимчасові текстури
        sdl2.SDL_DestroyTexture(tex1)
        sdl2.SDL_DestroyTexture(tex2)

    # --------------------
    # 6. Чистимо ресурси
    # --------------------
    cam1.release()
    cam2.release()
    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.ext.quit()


if __name__ == "__main__":
    main()
