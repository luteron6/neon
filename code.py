import time
import board
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
import rgbmatrix
import framebufferio
import requests

font = bitmap_font.load_font("5x5FontMonospaced-5.bdf", displayio.Bitmap)
print("Loaded fonts!")

# SpaceX API endpoint for upcoming launches. To disable only SpaceX launches, change "next/5" to "next/1". 
ROCKETLAUNCH_API_URL = "https://fdo.rocketlaunch.live/json/launches/next/5"

# Alternative fallback API URL
NEXTLAUNCH_API_URL = "https://fdo.rocketlaunch.live/json/launches/next/1"

# Initialize the RGB matrix
matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=32,
    bit_depth=6,
    rgb_pins=[
        board.MTX_R1, board.MTX_G1, board.MTX_B1,
        board.MTX_R2, board.MTX_G2, board.MTX_B2,
    ],
    addr_pins=[
        board.MTX_ADDRA, board.MTX_ADDRB, board.MTX_ADDRC, board.MTX_ADDRD,
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE,
)
display = framebufferio.FramebufferDisplay(matrix, auto_refresh=False)
display.auto_refresh=True

# Colors
WHITE = 0xFFFFFF
RED = 0xFF0000
BLACK = 0x000000


print("Attempting to pull data from the API.")
def fetch_next_launch():
    """Fetches the next SpaceX rocket launch data."""
    try:
        response = requests.get(ROCKETLAUNCH_API_URL)
        response.raise_for_status()
        data = response.json()

        # Filter the launches to only include SpaceX launches
        for launch in data["result"]:
            if "spacex" in launch["provider"]["name"].lower():  # Check if provider is SpaceX. Change the name if you wish to see a different launch provider (ie. Blue Origin)
                # Extract time and name
                t0_iso = launch["t0"]
                mission_name = launch["launch_description"]
                

                # Parse ISO 8601 datetime string to Unix timestamp
                launch_time_struct = time.strptime(t0_iso, "%Y-%m-%dT%H:%MZ")
                launch_time_unix = time.mktime(launch_time_struct)
                print(f"Data Fetched! {mission_name} (SpaceX) will launch at: {t0_iso}")
                return launch_time_unix, mission_name

        # If no SpaceX launches found
        print("No SpaceX launches found.")
        raise Exception()

# If the SpaceX API fails, just default to the next availiable launch.
    except Exception as e:
        response = requests.get(NEXTLAUNCH_API_URL)
        response.raise_for_status()
        data = response.json()

        # Extract ISO 8601 and t0 string and mission name
        t0_iso = data["result"][0]["t0"]
        mission_name = data["result"][0]["name"]

        # Parse ISO 8601 datetime string to Unix timestamp
        launch_time_struct = time.strptime(t0_iso, "%Y-%m-%dT%H:%MZ")
        launch_time_unix = time.mktime(launch_time_struct)
        print("Data Fetched! " + mission_name + " will launch at:" + t0_iso)
        return launch_time_unix, mission_name
        #print(f"Error fetching launch data: {e}")
        #return None, "Launch Data Unavailable"

# Fetch the next launch details
next_launch_time, mission_name = fetch_next_launch()
print (next_launch_time)

# Create display group
group = displayio.Group()
display.root_group = group

# Display background image
bmp_file = "man2.bmp"
try:
     bitmap = displayio.OnDiskBitmap(open(bmp_file, "rb"))
     tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader, x=0, y=0)
     group.append(tile_grid)
except Exception as e:
     print(f"Error loading image: {e}")


# Create labels
countdown_label = label.Label(font, text="", color=WHITE, x=2, y=29)
mission_label = label.Label(font, text=mission_name, color=RED, x=0, y=22)

group.append(countdown_label)
group.append(mission_label)

def scroll_text(label_obj, speed=1):
    """Scrolls the text of a label object from right to left."""
    label_obj.x -= speed
    # Reset position if the text scrolls completely off-screen
    if label_obj.x + len(label_obj.text) * 5 < 0:  # Adjust based on font size (6 is approximate width of small font)
        label_obj.x = 20
        #label_obj.x = display.width

def update_countdown():
    """Updates the countdown timer."""
    # print(next_launch_time)
    if time.time() >= next_launch_time:
        current_time = time.time()
        time_since_launch = (current_time - next_launch_time)
        hours, remainder = divmod(time_since_launch, 3600)
        minutes, seconds = divmod(remainder, 60)
        countdown_label.text = f"T+{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        # countdown_label.text = "T-:--:--"
        return

    current_time = time.time()
    time_left = max(0, next_launch_time - current_time)
    hours, remainder = divmod(time_left, 3600)
    minutes, seconds = divmod(remainder, 60)
    countdown_label.text = f"T-{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

# Main loop
while True:
    try:
        # Update the countdown
        update_countdown()

        # Scroll the mission name
        scroll_text(mission_label, speed=30)
        
        # Pause briefly before the next frame
        time.sleep(0.5)
        # print(countdown_label.text)

    except Exception as e:
        print(f"Error during display update: {e}")
        time.sleep(1)  # Wait a bit before retrying