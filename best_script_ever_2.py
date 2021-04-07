from ReadWriteMemory import ReadWriteMemory
import pydirectinput
import time
import pygame
import win32api
import win32con
import win32gui
import win32process
import GetBaseAddr as BA

PROCESS_NAME = 'retroarch.exe'
BASE_ADDRESS_DLL = BA.GetRetroArc_DLL_Address() 
RING_ADDRESS_OFFSET = 2887296
MILLS_ADDRESS_OFFSET = 2887299
LEVEL_ADDRESS_OFFSET = 2887268

RING_ADDRESS_POINTER =  BASE_ADDRESS_DLL+RING_ADDRESS_OFFSET
MILLS_ADDRESS_POINTER = BASE_ADDRESS_DLL+MILLS_ADDRESS_OFFSET
LEVEL_TICK_POINTER = BASE_ADDRESS_DLL+LEVEL_ADDRESS_OFFSET
AMMOUNT_TIME = 3 #secs

# SECS_ADDRESS_POINTER = 0x16380E85
# MIN_ADDRESS_POINTER = 0x16380E82

# Overlay Init ---------------
pygame.init()
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE) # For borderless, use pygame.NOFRAME
# Set Window to always be top
hwnd = win32gui.GetForegroundWindow()
win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 600, 300, 0, 0, win32con.SWP_NOSIZE)
# Set window transparency color
fuchsia = (115, 115, 115)  
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*fuchsia), 0, win32con.LWA_COLORKEY)

# Text Outline Code ---------

_circle_cache = {}
def _circlepoints(r):
    r = int(round(r))
    if r in _circle_cache:
        return _circle_cache[r]
    x, y, e = r, 0, 1 - r
    _circle_cache[r] = points = []
    while x >= y:
        points.append((x, y))
        y += 1
        if e < 0:
            e += 2 * y - 1
        else:
            x -= 1
            e += 2 * (y - x) - 1
    points += [(y, x) for x, y in points if x > y]
    points += [(-x, y) for x, y in points if x]
    points += [(x, -y) for x, y in points if y]
    points.sort()
    return points

def render(text, font, gfcolor=(239, 239, 0), ocolor=(0, 0, 0), opx=4):
    textsurface = font.render(text, True, gfcolor).convert_alpha()
    w = textsurface.get_width() + 2 * opx
    h = font.get_height()

    osurf = pygame.Surface((w, h + 2 * opx)).convert_alpha()
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(font.render(text, True, ocolor).convert_alpha(), (0, 0))

    for dx, dy in _circlepoints(opx):
        surf.blit(osurf, (dx + opx, dy + opx))

    surf.blit(textsurface, (opx, opx))
    return surf

# Read Game Memory Init ----------------
rwm = ReadWriteMemory()
process = rwm.get_process_by_name(PROCESS_NAME)

process.open()
rings_pointer = process.get_pointer(RING_ADDRESS_POINTER)
# sec_pointer = process.get_pointer(SECS_ADDRESS_POINTER)
# min_pointer = process.get_pointer(MIN_ADDRESS_POINTER)
mills_pointer = process.get_pointer(MILLS_ADDRESS_POINTER)
level_tick_pointer = process.get_pointer(LEVEL_TICK_POINTER)
levelStartFlagSet = False

rings = process.read(rings_pointer)
pre_value_rings = rings
print("Rings: " + str(rings))

# Game Logic ----------
def resetlevel():
    time.sleep(0.2)
    pydirectinput.press('f4')
    print("Reset Level")

def levelStart():
    pydirectinput.press('f2')
    levelStartFlagSet = True
    print("Level Start")

# def gameTimeTick():    
#     g_min = process.read(sec_pointer)
#     g_sec = process.read(min_pointer)
#     return g_min + g_sec

def gameTimeTickInMills():
    return process.read(mills_pointer)

class TimeLeft:
    def __init__(self):
        self.reset_time()
        self.ammount_of_time = AMMOUNT_TIME
        self.ammount_left = 0
        self.pre_game_time_mills = 0;


    def reset_time(self):
        self.last_reset_time = time.time()
    
    def tick_time(self):
        #Level Start
        if process.read(level_tick_pointer) == 1: 
            levelStart()
        # Time Left Tick
        if gameTimeTickInMills() != self.pre_game_time_mills:
            self.ammount_left = (time.time() - self.last_reset_time)
            if  self.ammount_left > self.ammount_of_time:
                self.ammount_left = self.ammount_of_time
                self.reset_time()
                resetlevel()
        else:
            self.reset_time()
        self.pre_game_time_mills = gameTimeTickInMills()
        return self.ammount_left

time_left = 0.0
time_tracker = TimeLeft()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            break

    screen.fill(fuchsia)  # Transparent background

    pre_value_rings = rings
    rings = process.read(rings_pointer)

    if rings != pre_value_rings:
        print("Rings: " + str(rings))

    if rings > pre_value_rings:
        time_tracker.reset_time()
    
    preTime_left = time_left
    time_left = time_tracker.tick_time()

    t = 0.0
    if preTime_left != time_left:
        t = round(AMMOUNT_TIME - time_left, 1)

    font = pygame.font.SysFont(None, 50)
    # img = font.render("Time Left: " + str(t), True, white_colour)
    screen.blit(render("Time Left: " + str(t), font), (860, 90))

    # pygame.display.update()
    time.sleep(0.02) # magic number to sync with the MILLS_ADDRESS update speed
    pygame.display.flip()

#65536 //vlaue when nothing is happening


