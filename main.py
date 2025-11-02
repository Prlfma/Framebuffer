import cv2
import os
import sys
import time
# Import your function from the other file
from display_image import display_opencv_on_framebuffer

# --- Settings ---
FB_DEVICE = "/dev/fb0"       # Path to your framebuffer
VIDEO_SOURCE = 0             # Video source (0 is usually the first webcam)
ROTATE_FRAME = cv2.ROTATE_180 # Frame rotation (as in your example)
# --- --- --- --- ---

def main():
    # --- Prepare terminal ---
    # (Disable cursor and clear screen)
    print("Starting video stream to framebuffer...")
    os.system("setterm -cursor off")
    os.system("clear")

    # --- Open video source ---
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print(f"Error: Could not open video source {VIDEO_SOURCE}", file=sys.stderr)
        os.system("setterm -cursor on") # Restore cursor
        os.system("clear")
        sys.exit(1)
    
    print(f"Video stream from {VIDEO_SOURCE} opened.")
    print(f"Outputting to {FB_DEVICE}. Press Ctrl+C to exit.")

    try:
        while True:
            # --- Read frame ---
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not retrieve frame (end of stream?).", file=sys.stderr)
                break
            
            # --- Process frame ---
            # I noticed you were rotating the image in your example.
            # If this is not needed, comment out or remove the next line.
            if ROTATE_FRAME is not None:
                frame_processed = cv2.rotate(frame, ROTATE_FRAME)
            else:
                frame_processed = frame

            # --- Display frame ---
            if not display_opencv_on_framebuffer(frame_processed):
                print("Error: Failed to write to framebuffer. Exiting...", file=sys.stderr)
                break
    
    except KeyboardInterrupt:
        # Handle Ctrl+C for a clean exit
        print("\nStopping video stream...")
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

    finally:
        # --- Cleanup ---
        print("Restoring terminal and releasing devices...")
        if cap.isOpened():
            cap.release()
        # Restore cursor and clear screen
        os.system("setterm -cursor on")
        os.system("clear")
        print("Finished.")

if __name__ == "__main__":
    main()

