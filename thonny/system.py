import time
import psutil
import tkinter as tk

# GUI window
root = tk.Tk()
root.title("System Live Monitor")
root.overrideredirect(True)

# Window dimensions
window_width = 350
window_height = 200

# Get screen dimensions and calculate position for bottom left
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_position = 0
y_position = screen_height - window_height
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
root.config(bg="#1E1E1E")
root.wm_attributes('-transparentcolor', '#1E1E1E')

label_fps = tk.Label(root, text="FPS: Calculating...", font=("Arial", 14), fg="white", bg="#1E1E1E")
label_cpu = tk.Label(root, text="CPU Usage: ...", font=("Arial", 14), fg="white", bg="#1E1E1E")
label_ram = tk.Label(root, text="RAM Usage: ...", font=("Arial", 14), fg="white", bg="#1E1E1E")

label_fps.pack(pady=5)
label_cpu.pack(pady=5)
label_ram.pack(pady=5)

prev_time = time.time()
fps_count = 0

def update_stats():
    global prev_time, fps_count
    fps_count += 1
    current_time = time.time()
    elapsed = current_time - prev_time

    if elapsed >= 1.0:
        fps = fps_count / elapsed
        fps_count = 0
        prev_time = current_time

        label_fps.config(text=f"FPS: {fps:.2f}")

        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        label_cpu.config(text=f"CPU Usage: {cpu_usage}%")
        label_ram.config(text=f"RAM Usage: {ram_usage}%")

    root.after(10, update_stats)

update_stats()
root.mainloop()
