import Subu
from machine import Pin
import time

IR1_PIN = Subu.IO2 
IR2_PIN = Subu.IO3  

DISTANCE = 0.5

start_time_us = 0
end_time_us = 0
timing_active = False


IR1 = Pin(IR1_PIN, Pin.IN)
IR2 = Pin(IR2_PIN, Pin.IN)

# --- Interrupt Handler Functions ---

def start_gate_handler(pin):
    """Called instantly when the object is detected at IR1 (Start Gate)."""
    global start_time_us, timing_active
    
    # 1. Simple software debouncing
    time.sleep_ms(5)
    if pin.value() == 0:
        return # Ignore if signal bounced back

    # 2. Check if timing is already running (ignore if still waiting for finish)
    if not timing_active:
        start_time_us = time.ticks_us()
        timing_active = True
        print("\nSTART: Timing commenced.")


def finish_gate_handler(pin):
    """Called instantly when the object is detected at IR2 (Finish Gate)."""
    global end_time_us, timing_active
    
    # 1. Simple software debouncing
    time.sleep_ms(5)
    if pin.value() == 0:
        return # Ignore if signal bounced back

    # 2. Check if timing is active (ignore if IR1 wasn't hit first)
    if timing_active:
        end_time_us = time.ticks_us()
        timing_active = False # Stop the timing flag

        print("FINISH: Timing complete, calculating speed...")

IR1.irq(trigger=Pin.IRQ_RISING, handler=start_gate_handler)
IR2.irq(trigger=Pin.IRQ_RISING, handler=finish_gate_handler)

print("Interrupt-Based Speed Trap Ready. DISTANCE =", DISTANCE, "meters.")
print("Waiting for IR1 (Start Gate)...")

# --- Main Logic ---

while True:
    
    # Check if the finish interrupt has fired and timing is complete
    if not timing_active and start_time_us > 0 and end_time_us > start_time_us:
        
        # Calculate time and speed using microsecond precision
        time_taken_us = time.ticks_diff(end_time_us, start_time_us)
        time_taken_s = time_taken_us / 1_000_000.0 # Convert microseconds to seconds

        if time_taken_s > 0:
            speed_mps = DISTANCE / time_taken_s
            
            print("------------------------")
            print(f"Time taken (µs): {time_taken_us}")
            print(f"Time taken (s): {time_taken_s:.6f}")
            print(f"Speed (m/s): {speed_mps:.3f}")
            print("------------------------")

        # Reset variables for the next measurement
        start_time_us = 0
        end_time_us = 0
        print("Waiting for new object...")

    time.sleep_ms(50) # small delay to avoid false triggering