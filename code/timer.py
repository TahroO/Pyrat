import pygame


class Timer:
    def __init__(self, duration):
        self.duration = duration
        self.active = False
        self.start_time = 0

    def activate(self):
        self.active = True
        # gets the current time once when timer is started
        self.start_time = pygame.time.get_ticks()

    def deactivate(self):
        self.active = False
        self.start_time = 0

    def update(self):
        # gets the current time constantly
        current_time = pygame.time.get_ticks()
        # timer runs till duration ends, is deactivated afterwards
        if current_time - self.start_time >= self.duration:
            self.deactivate()
