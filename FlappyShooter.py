import pygame
import random
import math

pygame.init()

# Resolution
width = 864 
height = 936

# Set screen resolution and window title
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Flappy Shooter")


# Variables for gameplay 
gravity = False
gameOver = False
shooting = False
shootingPreviously = False
pipeGap = 150 # How much gap the pipes have
pipeFrequency = 1500 # How often the pipe spawns in milliseconds
lastPipeTime = pygame.time.get_ticks() - pipeFrequency # The time when the last pipe was spawned in
enemyFrequency = 2000 # How often the enemy birds spawn in milliseconds
lastEnemyTime = pygame.time.get_ticks()
score = 0
passedPipe = False # Indicates if the player has passed a pipe

# FPS
clock = pygame.time.Clock()
fps = 60

# Function for loading different bird sprites with different colors
def loadBirdFrames():
    birdColors = ["yellow", "red", "blue"]
    birdFrames = {} # Dictionary of color (string) to frames (list)

    # Iterate through each color and create a list of frames
    for color in birdColors:
        frames = [pygame.image.load(f"images/birds/{color}bird{num}.png").convert_alpha() for num in range(3)]
        birdFrames[color] = frames 

    return birdFrames

# Function for displaying numbers using images
def displayNum(num, startX = 0, startY = 0, centerHorizontal = True, centerVertical = True):
    # Calculate the total width of the number string
    numStr = str(num)
    digits = [numbers[int(char)] for char in numStr]
    totalWidth = sum(image.get_width() for image in digits) 

    if centerHorizontal:
        # Adjust the starting x position to offset half the total width
        startX = (width // 2) - (totalWidth // 2)

    if centerVertical:
        # Center Y position 
        imageHeight = numbers[0].get_height()
        startY = (height // 2) - (imageHeight // 2)

    # Initialize current x positions for rendering numbers
    currentX = startX
    # Draw the numbers
    for image in digits:
        screen.blit(image, (currentX, startY))

        # Increment x position for the next digit
        currentX += image.get_width()

# Restarts the game by resetting variables
def restart():
    # Reset sprite groups
    pipeGroup.empty()
    enemyGroup.empty()
    bulletGroup.empty()

    # Reset Player 
    player.rect.x = 100
    player.rect.y = int(height / 2)

    # Make sure passed pipe is false so that the first pipe is counted in score
    global passedPipe, gravity, lastEnemyTime
    passedPipe = False
    gravity = False

    # Rest enemy spawn timer
    lastEnemyTime = pygame.time.get_ticks()

    score = 0
    return score

# Load Images
bgUpper = pygame.image.load("images/bgupper.png").convert()
bgMidUpper = pygame.image.load("images/bgmidupper.png").convert()
bgMidLower = pygame.image.load("images/bgmidlower.png").convert()
groundBG = pygame.image.load("images/ground.png").convert()
button = pygame.image.load("images/restart.png").convert_alpha()
gameOverText = pygame.image.load("images/gameover.png").convert_alpha()
pipeImage = pygame.image.load("images/pipe.png").convert_alpha()

numbers = [pygame.image.load(f"images/numbers/{num}.png").convert_alpha() for num in range(10)]
allBirdFrames = loadBirdFrames()
bulletFrames = [pygame.image.load(f"images/projectile/fire{num}.png").convert_alpha() for num in range(5)]

# Load SFX
flapSound = pygame.mixer.Sound("sounds/wing.wav")
scoreSound = pygame.mixer.Sound("sounds/point.wav")
playerHitSound = pygame.mixer.Sound("sounds/hit.wav") 
projectileSound = pygame.mixer.Sound("sounds/flame.ogg")

# Variables for bg scrolling
upBGX = 0
midUpperBGX = 0
midUpperBGY = bgUpper.get_height()
midLowerBGX = 0
midLowerBGY = bgUpper.get_height() + bgMidUpper.get_height()
groundBGX = 0
groundBGY = bgUpper.get_height() + bgMidUpper.get_height() + bgMidLower.get_height()
upScrollSpeed = 0.5 
midUpperScrollSpeed = 1
midLowerScrollSpeed = 2
groundScrollSpeed = 4
extraBGSpace = 35 # Leeway for the ground bg that is wider than the BG

# Sprite class for the bird
class Bird(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = allBirdFrames["yellow"] 
        self.index = 0 # Starting index for the sprite animation
        self.counter = 0 # Controls the speed of the animation
        self.image = self.images[self.index] # Current image of the bird
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.velocity = 0 
        self.acceleration = 0.5
        self.maxSpeed = 8
        self.jumpForce = 10
        self.jumpPressed = False
    
    def update(self):
        # -- Gravity -- #
        if gravity == True:
            self.velocity += self.acceleration 

            # Clamp velocity
            if self.velocity > self.maxSpeed:
                self.velocity = self.maxSpeed

            # Only apply gravity if the bird is above ground
            if self.rect.bottom < groundBGY:
                self.rect.y += int(self.velocity)

        if gameOver == False:
            # -- Player input -- #
            keys = pygame.key.get_pressed()
            mouseClick = pygame.mouse.get_pressed()
            jumpButton = keys[pygame.K_SPACE] or (mouseClick[0] == 1) 

            # Check if the player presses the jump button
            if jumpButton and self.jumpPressed == False:
                self.velocity = -self.jumpForce # Apply upward velocity
                self.jumpPressed = True
                flapSound.play()

            if not keys[pygame.K_SPACE] and (mouseClick[0] == 0):
                self.jumpPressed = False

            # -- Animation -- #
            # Go to the next frame of the animation
            self.counter += 1
            frameTickLength = 5 # How many ticks/amount the counter should have before moving to the next frame 

            # Check counter and frame tick length before moving on to the next frame
            if self.counter > frameTickLength:
                self.counter = 0
                self.index += 1

                # Reset index of animation when it goes to the last index
                if self.index >= len(self.images):
                    self.index = 0

                self.image = self.images[self.index]

            if gravity:
                # Bird Rotation depending on its velocity
                self.image = pygame.transform.rotate(self.images[self.index], -self.velocity * 2.5)
        else: # If the game is over, make it so that the bird is rotated 90 degrees
            self.image = pygame.transform.rotate(self.images[self.index], -90)

# Sprite class for the enemy birds
class EnemyBird(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        pygame.sprite.Sprite.__init__(self) 
        self.images = [pygame.transform.flip(bird, True, False) for bird in allBirdFrames[color]] 
        self.index = 0 # Starting index for the sprite animation
        self.counter = 0 # Controls the speed of the animation
        self.image = self.images[self.index] # Current image of the bird
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speedX = -2
        self.speedY = 0
        self.amplitude = 10 # How high the wave motion is
        self.waveMotionTimer = 0

    def update(self):
        if gameOver == False:
            # -- Enemy Movement -- #
            self.rect.x += -groundScrollSpeed + self.speedX
            self.waveMotionTimer += 0.05

            # Only go down until you reach the ground 
            if self.rect.bottom < groundBGY:
                self.rect.y += int(self.amplitude * math.sin(self.waveMotionTimer))
            else:
                self.rect.y -= 1

            # -- Animation -- #
            # Go to the next frame of the animation
            self.counter += 1
            frameTickLength = 5 # How many ticks/amount the counter should have before moving to the next frame 

            # Check counter and frame tick length before moving on to the next frame
            if self.counter > frameTickLength:
                self.counter = 0
                self.index += 1

                # Reset index of animation when it goes to the last index
                if self.index >= len(self.images):
                    self.index = 0

                self.image = self.images[self.index]

            # Remove off screen
            if self.rect.right < 0:
                self.kill()

# Sprite class for the pipe
class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, flipped = False):
        pygame.sprite.Sprite.__init__(self)
        self.image = pipeImage
        self.rect = self.image.get_rect()

        # If flipped is true, pipe is spawned from the top
        if flipped:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect.bottomleft = [x, y - int(pipeGap / 2)]
        else:
            self.rect.topleft = [x, y + int(pipeGap / 2)]

    def update(self):
        if gravity == True and gameOver == False:
            self.rect.move_ip(-groundScrollSpeed, 0)  # Move pipe to the left using scroll speed

        # Remove pipe when they go off screen
        if self.rect.right < 0:
            self.kill()

# Class for the button in game
class Button():
    def __init__(self, x, y, image):
        self.image = image 
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self):
        screen.blit(self.image, (self.rect.x, self.rect.y))

    def update(self):
        action = False

        # Get the mouse position
        position = pygame.mouse.get_pos()

        # Check if mouse is over the button
        if self.rect.collidepoint(position) and pygame.mouse.get_pressed()[0] == 1:
            action = True

        return action

# Class for the bullet sprite
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.images = bulletFrames
        self.index = 0 # Starting index for the sprite animation
        self.counter = 0 # Controls the speed of the animation
        self.image = self.images[self.index] # Current image of the bird
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
    
    def update(self):
        if gameOver == False:
            # -- Movement -- #
            self.rect.x += self.speed * self.direction

            if self.rect.left > width or self.rect.right < 0:
                self.kill()

            # -- Animation -- #
            # Go to the next frame of the animation
            self.counter += 1
            frameTickLength = 3 # How many ticks/amount the counter should have before moving to the next frame 

            # Check counter and frame tick length before moving on to the next frame
            if self.counter > frameTickLength:
                self.counter = 0
                self.index += 1

                # Reset index of animation when it goes to the last index
                if self.index >= len(self.images):
                    self.index = 1

                self.image = self.images[self.index]

            # -- Animation -- #
            # Go to the next frame of the animation
            self.counter += 1
            frameTickLength = 5 # How many ticks/amount the counter should have before moving to the next frame 

            # Check counter and frame tick length before moving on to the next frame
            if self.counter > frameTickLength:
                self.counter = 0
                self.index += 1

                # Reset index of animation when it goes to the last index
                if self.index >= len(self.images):
                    self.index = 0

                self.image = self.images[self.index]

            # Remove when it reaches off screen
            if self.rect.right < 0 or self.rect.left > width:
                self.kill()

birdGroup = pygame.sprite.Group() # List of bird sprites inside the game
enemyGroup = pygame.sprite.Group() # List of enemy bird sprites inside the game
pipeGroup = pygame.sprite.Group() # List of pipe sprites inside the game
bulletGroup = pygame.sprite.Group() # List of bullet sprites inside the game

button = Button(width // 2 - 50, height // 2, button) # Button for restarting
player = Bird(100, int(height / 2))

birdGroup.add(player)

running = True
while running:
    for event in pygame.event.get():
        keys = pygame.key.get_pressed()
        mouseClick = pygame.mouse.get_pressed()

        if event.type == pygame.QUIT:
            running = False

        # Start the game if the player presses the jump button
        startPressed = event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN)
        if startPressed and gravity == False and not gameOver:
            gravity = True

    # -- Update -- #
    # Check the score
    if pipeGroup:
        bird = player
        pipe = pipeGroup.sprites()[0]

        # If the player is within the pipe gap and hasn't passed it yet
        if bird.rect.left > pipe.rect.left and \
           bird.rect.right < pipe.rect.right and not passedPipe:
            score += 1
            passedPipe = True
            scoreSound.play()

        # If the player goes beyond the pipes, add score
        if passedPipe and bird.rect.left > pipe.rect.right:
            passedPipe = False

        # If the player has killed an enemy, add score
        if pygame.sprite.groupcollide(bulletGroup, enemyGroup, True, True):
            score += 1
            scoreSound.play()

    # Check for game over collisions
    if pygame.sprite.groupcollide(birdGroup, pipeGroup, False, False) or pygame.sprite.groupcollide(birdGroup, enemyGroup, False, False) or player.rect.top < 0:
        if not gameOver:
            playerHitSound.play()

        gameOver = True

    # Check if the player has hit the ground
    if player.rect.bottom >= groundBGY:
        if not gameOver:
            playerHitSound.play()
        gameOver = True
        flying = False

    if gameOver == False and gravity == True:
        # -- Shooting -- #
        shootButton = keys[pygame.K_j] or (mouseClick[2] == 1) 
        shootingNow = shootButton and not shootingPreviously

        # Check if the player presses the jump button
        if shootingNow:
            shooting = True
            bullet = Bullet(player.rect.centerx + player.rect.size[0] - 30, player.rect.centery, 1)
            bulletGroup.add(bullet)
            projectileSound.play()

        shootingPreviously = shootButton # Update the previous shooting state

        # -- Pipe Spawner -- # 
        currentTime = pygame.time.get_ticks()

        # If pipeFrequency time has passed, create pipes off screen
        if currentTime - lastPipeTime >= pipeFrequency: 
            # Randomize pipe height
            pipeHeight = random.randint(-100, 100)
            bottomPipe = Pipe(width, int(height / 2) + pipeHeight)
            topPipe = Pipe(width, int(height / 2) + pipeHeight, True)
            pipeGroup.add(bottomPipe)
            pipeGroup.add(topPipe)
            lastPipeTime = currentTime # Set the lastPipeTime to the currentTime

        # -- Enemy Spawner -- #
        # If enemyFrequency time has passed, create enemies off screen
        if currentTime - lastEnemyTime >= enemyFrequency:
            # Randomize enemy height and color 
            enemyHeight = random.randint(100, 500)
            enemyColor = random.choice(["red", "blue"])
            enemy = EnemyBird(width, enemyHeight, enemyColor)
            enemyGroup.add(enemy)
            lastEnemyTime = currentTime

        # -- Parallax Effect -- #
        # Scroll bg layers to the left and reset their positions accordingly
        upBGX -= upScrollSpeed
        if upBGX <= -extraBGSpace:
            upBGX = 0

        midUpperBGX -= midUpperScrollSpeed
        if midUpperBGX <= -extraBGSpace:
            midUpperBGX = 0

        midLowerBGX -= midLowerScrollSpeed
        if midLowerBGX <= -extraBGSpace:
            midLowerBGX = 0

        groundBGX -= groundScrollSpeed
        if groundBGX <= -extraBGSpace:
            groundBGX = 0

        pipeGroup.update()
        bulletGroup.update()

    # Update logic for sprites
    birdGroup.update()
    enemyGroup.update()

    # Game over updates
    if gameOver and button.update():
        # When retry button is clicked, restart the game
        gameOver = False
        score = restart()

    # -- Draw / Render --#
    # Draw the background
    screen.blit(bgUpper, (upBGX, 0))
    screen.blit(bgMidUpper, (midUpperBGX, midUpperBGY))
    screen.blit(bgMidLower, (midLowerBGX, midLowerBGY))

    # Draw the in-game sprites
    pipeGroup.draw(screen)
    birdGroup.draw(screen)
    enemyGroup.draw(screen)
    bulletGroup.draw(screen)

    screen.blit(groundBG, (groundBGX, groundBGY))

    # Display the score
    displayNum(score, width // 2, 100, True, False)

    # Draw game over button
    if gameOver == True:
        screen.blit(gameOverText, (width // 2 - 200, height // 2 - button.image.get_height() - 100))
        button.draw()

    # flip() the display to put the renders on the screen
    pygame.display.flip()

    clock.tick(fps) # Limits fps to the given value 

pygame.quit()
