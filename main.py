import arcade
import math
import os
import random

#region CONSTANTS
# WINDOW
SCREEN_WIDTH = 1152
SCREEN_HEIGHT = 576
SCREEN_TITLE = "Mephistophelia"

# SCALING
TILE_SCALING = 0.5
CHARACTER_SCALING = TILE_SCALING * 2
SPRITE_PIXEL_SIZE = 128
TILE_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING

# GAME
GRAVITY = 1.5
PLAYER_MOVEMENT_SPEED = 10
PLAYER_JUMP_SPEED = 25
PLAYER_DASH_SPEED = 25
PLAYER_DASH_DURATION = 0.1
PLAYER_DASH_COOLDOWN = 2
INPUT_MODES = ['HUMAN', 'AGENT']

# PLAYER
PLAYER_PATH = "./assets/sprites/player/player"
PLAYER_RIGHT_FACING = 0
PLAYER_LEFT_FACING = 1

# MAP
MAP_PATH = "./assets/maps/test_map.json"
MAP_LAYER_GOAL = "Goal"
MAP_LAYER_FOREGROUND = "Foreground"
MAP_LAYER_PLATFORMS = "Platforms"
MAP_LAYER_PLAYER = "Player"
MAP_LAYER_BACKGROUND = "Background"
MAP_LAYER_DEATHGROUND = "Deathground"

# AGENT
AGENT_REWARD_DEATH = -100
AGENT_REWARD_GOAL = 1000
AGENT_REWARD_STEP = -1
AGENT_ACTIONS = [
    'LEFT', 'RIGHT',
    'JUMP_LEFT', 'JUMP_RIGHT'#, 'JUMP',
    # 'DASH', 'DASH_LEFT', 'DASH_RIGHT', 'DASH_UP', 'DASH_UP_LEFT', 'DASH_UP_RIGHT',
]
AGENT_MODES = ['RANDOM', 'PIXEL', 'TILED', 'RADAR']
#endregion CONSTANTS

#region GAME
# Player class
class Player(arcade.Sprite):

    def __init__(self):
        super().__init__()

        # Set player to face right at start
        self.character_face_direction = PLAYER_RIGHT_FACING

        # Used for flipping between image sequences
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        # Load textures for idle poses
        self.idle_texture_pair = self.load_texture_pair(f"{PLAYER_PATH}_idle.png")
        self.jump_texture_pair = self.load_texture_pair(f"{PLAYER_PATH}_jump.png")
        self.fall_texture_pair = self.load_texture_pair(f"{PLAYER_PATH}_fall.png")

        # Load textures for walking
        self.walk_textures = []
        for i in range(8):
            texture = self.load_texture_pair(f"{PLAYER_PATH}_walk{i}.png")
            self.walk_textures.append(texture)

        # Set player initial texture
        self.texture = self.idle_texture_pair[0]

        # Set player hit box
        self.hit_box = self.texture.hit_box_points

        # Set player radar
        self.radar = None
        self.radar_left = None
        self.radar_right = None
        self.radar_up = None
        self.radar_up_left = None
        self.radar_up_right = None
        self.radar_down = None
        self.radar_down_left = None
        self.radar_down_right = None

    def load_texture_pair(self, filename):
        return [
            arcade.load_texture(filename),
            arcade.load_texture(filename, flipped_horizontally=True),
        ]

    def update_animation(self, delta_time: float = 1 / 60):
        # Animation direction
        if self.change_x < 0 and self.character_face_direction == PLAYER_RIGHT_FACING:
            self.character_face_direction = PLAYER_LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == PLAYER_LEFT_FACING:
            self.character_face_direction = PLAYER_RIGHT_FACING

        # Jumping animation
        if self.change_y > 0:
            self.texture = self.jump_texture_pair[self.character_face_direction]
            return
        elif self.change_y < 0:
            self.texture = self.fall_texture_pair[self.character_face_direction]
            return

        # Idle animation
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # Walking animation
        self.cur_texture += 1
        if self.cur_texture > 7:
            self.cur_texture = 0
        self.texture = self.walk_textures[self.cur_texture][
            self.character_face_direction
        ]

# Game class
class Game(arcade.Window):

    def __init__(self):
        # Set game window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Set origin path
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # State machine
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.space_pressed = False
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_direction = (0, 0)

        # Tilemap Object
        self.tile_map = None

        # Game Scene Object
        self.scene = None

        # Player Object
        self.player = None
        self.player_start_x = 0
        self.player_start_y = 0

        # Physics engine Object
        self.physics_engine = None

        # Camera Object
        self.camera = None
        self.gui_camera = None

        # Map bounds
        self.map_x_bound = 0
        self.map_y_bound = 0

        # AI agent
        self.agent = None
        self.agent_reward = 0
        self.agent_action = None

        # Game mode
        self.input_mode = None

        # Goal object
        self.goal_x = 0
        self.goal_y = 0

    def setup(self):
        # Set camera
        self.camera = arcade.Camera(self.width, self.height)
        self.gui_camera = arcade.Camera(self.width, self.height)

        # Set map layers options
        map_layer_options = {
            MAP_LAYER_PLATFORMS: {
                "use_spatial_hash": True,
            },
            MAP_LAYER_DEATHGROUND: {
                "use_spatial_hash": True,
            },
        }

        # Load the map
        self.tile_map = arcade.load_tilemap(MAP_PATH, TILE_SCALING, map_layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Load the player layer
        self.scene.add_sprite_list_after(MAP_LAYER_PLAYER, MAP_LAYER_FOREGROUND)

        # Set the player at start position
        self.player = Player()
        self.player_start_x = int(self.tile_map.get_tilemap_layer("Player").properties["start_x"]) * TILE_PIXEL_SIZE - TILE_PIXEL_SIZE / 2
        self.player_start_y = int(self.tile_map.get_tilemap_layer("Player").properties["start_y"]) * TILE_PIXEL_SIZE - TILE_PIXEL_SIZE / 2
        self.player.center_x = self.player_start_x
        self.player.center_y = self.player_start_y
        self.scene.add_sprite(MAP_LAYER_PLAYER, self.player)

        # Locate edges of the map
        self.map_x_bound = int(self.tile_map.width * TILE_PIXEL_SIZE)
        self.map_y_bound = int(self.tile_map.height * TILE_PIXEL_SIZE)

        # Set the background color
        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        # Set the physics engine
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            gravity_constant=GRAVITY,
            walls=self.scene[MAP_LAYER_PLATFORMS]
        )

        # Set game mode
        self.input_mode = INPUT_MODES[1]

        if self.input_mode == INPUT_MODES[1]:
            # Set the AI agent
            self.agent = Agent(
                int(self.player_start_x),
                int(self.player_start_y),
                self.map_x_bound,
                self.map_y_bound,
                learning_mode = AGENT_MODES[2],
                learning_rate = 0.9,
                discount_factor = 0.5,
            )

            # Set player radar sprites
            self.player.radar_left = arcade.SpriteSolidColor(5, 5, arcade.color.RED)
            self.player.radar_right = arcade.SpriteSolidColor(5, 5, arcade.color.RED)
            self.player.radar_up = arcade.SpriteSolidColor(5, 5, arcade.color.RED)
            self.player.radar_up_left = arcade.SpriteSolidColor(5, 5, arcade.color.RED)
            self.player.radar_up_right = arcade.SpriteSolidColor(5, 5, arcade.color.RED)
            self.player.radar_down = arcade.SpriteSolidColor(5, 5, arcade.color.RED)
            self.player.radar_down_left = arcade.SpriteSolidColor(5, 5, arcade.color.RED)
            self.player.radar_down_right = arcade.SpriteSolidColor(5, 5, arcade.color.RED)
            
            # Set player radar object
            self.player.radar = [
                self.player.radar_left,
                self.player.radar_right,
                self.player.radar_up,
                self.player.radar_up_left,
                self.player.radar_up_right,
                self.player.radar_down,
                self.player.radar_down_left,
                self.player.radar_down_right,
            ]

            # Set the player radar sprites positions
            self.scene.add_sprite(MAP_LAYER_PLAYER, self.player.radar_left)
            self.player.radar_left.center_x = self.player.center_x - TILE_PIXEL_SIZE
            self.player.radar_left.center_y = self.player.center_y

            self.scene.add_sprite(MAP_LAYER_PLAYER, self.player.radar_right)
            self.player.radar_right.center_x = self.player.center_x + TILE_PIXEL_SIZE
            self.player.radar_right.center_y = self.player.center_y

            self.scene.add_sprite(MAP_LAYER_PLAYER, self.player.radar_up)
            self.player.radar_up.center_x = self.player.center_x
            self.player.radar_up.center_y = self.player.center_y + TILE_PIXEL_SIZE * 3

            self.scene.add_sprite(MAP_LAYER_PLAYER, self.player.radar_up_left)
            self.player.radar_up_left.center_x = self.player.center_x - TILE_PIXEL_SIZE
            self.player.radar_up_left.center_y = self.player.center_y + TILE_PIXEL_SIZE * 3

            self.scene.add_sprite(MAP_LAYER_PLAYER, self.player.radar_up_right)
            self.player.radar_up_right.center_x = self.player.center_x + TILE_PIXEL_SIZE
            self.player.radar_up_right.center_y = self.player.center_y + TILE_PIXEL_SIZE * 3

            self.scene.add_sprite(MAP_LAYER_PLAYER, self.player.radar_down)
            self.player.radar_down.center_x = self.player.center_x
            self.player.radar_down.center_y = self.player.center_y - TILE_PIXEL_SIZE

            self.scene.add_sprite(MAP_LAYER_PLAYER, self.player.radar_down_left)
            self.player.radar_down_left.center_x = self.player.center_x - TILE_PIXEL_SIZE
            self.player.radar_down_left.center_y = self.player.center_y - TILE_PIXEL_SIZE

            self.scene.add_sprite(MAP_LAYER_PLAYER, self.player.radar_down_right)
            self.player.radar_down_right.center_x = self.player.center_x + TILE_PIXEL_SIZE
            self.player.radar_down_right.center_y = self.player.center_y - TILE_PIXEL_SIZE

            # Locate goal
            self.goal_x = int(self.tile_map.get_tilemap_layer("Goal").properties["x"]) * TILE_PIXEL_SIZE - TILE_PIXEL_SIZE / 2
            self.goal_y = int(self.tile_map.get_tilemap_layer("Goal").properties["y"]) * TILE_PIXEL_SIZE - TILE_PIXEL_SIZE / 2

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw()

        if self.input_mode == INPUT_MODES[1]:
            arcade.draw_line(self.player.center_x, self.player.center_y, self.goal_x, self.goal_y, arcade.color.YELLOW, 2)
        
        self.gui_camera.use()

        arcade.draw_text(
            f'dash: {int(self.dash_cooldown)}',
            10, self.height - 70, anchor_x="left", anchor_y="top",
        )
        arcade.draw_text(
            f'win: {self.agent.win}',
            10, self.height - 90, anchor_x="left", anchor_y="top",
        )
        arcade.draw_text(
            'Press R to reset',
            self.width -110, self.height - 10, color=arcade.color.ORANGE, font_size=10,anchor_x="left", anchor_y="top",
        )

        if self.input_mode == INPUT_MODES[1]:
            arcade.draw_text(
                f'state: {self.agent.state}',
                10, self.height - 10, anchor_x="left", anchor_y="top",
            )
            arcade.draw_text(
                f'score: {self.agent.score}',
                10, self.height - 30, anchor_x="left", anchor_y="top",
            )
            arcade.draw_text(
                f'action: {self.agent_action}',
                10, self.height - 50, anchor_x="left", anchor_y="top",
            )
            

    #region INPUTS
    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.Z:
            self.up_pressed = True
        elif key == arcade.key.LEFT or key == arcade.key.Q:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
        elif key == arcade.key.SPACE:
            self.space_pressed = True
        elif key == arcade.key.R:
            self.reset_player_position()
            
            if self.input_mode == INPUT_MODES[1]:
                self.agent.reset()

        self.on_key_change()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.Z:
            self.up_pressed = False
        elif key == arcade.key.LEFT or key == arcade.key.Q:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False
        elif key == arcade.key.SPACE:
            self.space_pressed = False

        self.on_key_change()

    def on_agent_input(self):
        if self.agent_action == AGENT_ACTIONS[0]:
            self.left_pressed = True
        elif self.agent_action == AGENT_ACTIONS[1]:
            self.right_pressed = True
        elif self.agent_action == AGENT_ACTIONS[2]:
            self.up_pressed = True
        elif self.agent_action == AGENT_ACTIONS[3]:
            self.left_pressed = True
            self.up_pressed = True
        elif self.agent_action == AGENT_ACTIONS[4]:
            self.right_pressed = True
            self.up_pressed = True
        elif self.agent_action == AGENT_ACTIONS[5]:
            self.space_pressed = True
        elif self.agent_action == AGENT_ACTIONS[6]:
            self.left_pressed = True
            self.space_pressed = True
        elif self.agent_action == AGENT_ACTIONS[7]:
            self.right_pressed = True
            self.space_pressed = True
        elif self.agent_action == AGENT_ACTIONS[8]:
            self.up_pressed = True
            self.space_pressed = True
        elif self.agent_action == AGENT_ACTIONS[9]:
            self.left_pressed = True
            self.up_pressed = True
            self.space_pressed = True
        elif self.agent_action == AGENT_ACTIONS[10]:
            self.right_pressed = True
            self.up_pressed = True
            self.space_pressed = True

        self.on_key_change()

    def on_key_change(self):
        self.process_movement()
        self.process_jump()
        self.process_dash()

        if self.input_mode == INPUT_MODES[1]:
            self.process_radar()

    def reset_inputs(self):
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.space_pressed = False
    #endregion INPUTS
        
    #region ACTIONS    
    def can_jump(self):
        return self.up_pressed and self.physics_engine.can_jump()
    
    def can_dash(self):
        return self.space_pressed \
            and self.dash_timer == 0 \
            and self.dash_cooldown == 0

    def process_movement(self):
        if self.right_pressed and not self.left_pressed:
            self.player.change_x = PLAYER_MOVEMENT_SPEED
        elif self.left_pressed and not self.right_pressed:
            self.player.change_x = -PLAYER_MOVEMENT_SPEED
        else:
            self.player.change_x = 0

    def process_jump(self):
        if self.can_jump():
            self.player.change_y = PLAYER_JUMP_SPEED

    def process_dash(self):
        if self.can_dash():
            self.dash_timer = PLAYER_DASH_DURATION
            self.dash_direction = (
                int(self.right_pressed) - int(self.left_pressed),
                int(self.up_pressed),
            )
    
    def process_radar(self):
        self.player.radar_left.center_x = self.player.center_x - TILE_PIXEL_SIZE
        self.player.radar_left.center_y = self.player.center_y

        self.player.radar_right.center_x = self.player.center_x + TILE_PIXEL_SIZE
        self.player.radar_right.center_y = self.player.center_y

        self.player.radar_up.center_x = self.player.center_x
        self.player.radar_up.center_y = self.player.center_y + TILE_PIXEL_SIZE * 3

        self.player.radar_up_left.center_x = self.player.center_x - TILE_PIXEL_SIZE
        self.player.radar_up_left.center_y = self.player.center_y + TILE_PIXEL_SIZE * 3

        self.player.radar_up_right.center_x = self.player.center_x + TILE_PIXEL_SIZE
        self.player.radar_up_right.center_y = self.player.center_y + TILE_PIXEL_SIZE * 3

        self.player.radar_down.center_x = self.player.center_x
        self.player.radar_down.center_y = self.player.center_y - TILE_PIXEL_SIZE

        self.player.radar_down_left.center_x = self.player.center_x - TILE_PIXEL_SIZE
        self.player.radar_down_left.center_y = self.player.center_y - TILE_PIXEL_SIZE

        self.player.radar_down_right.center_x = self.player.center_x + TILE_PIXEL_SIZE
        self.player.radar_down_right.center_y = self.player.center_y - TILE_PIXEL_SIZE
    #endregion ACTIONS

    #region COLLISIONS
    def check_out_of_bounds(self):
        if self.player.center_y < -100:
            self.agent_reward += AGENT_REWARD_DEATH
            self.reset_player_position()

    def check_collision_with_platforms(self, sprite):
        if arcade.check_for_collision_with_list(
            sprite, self.scene[MAP_LAYER_PLATFORMS]
        ):
            return True
        return False

    def check_collision_with_deathground(self, sprite):
        if arcade.check_for_collision_with_list(
            sprite, self.scene[MAP_LAYER_DEATHGROUND]
        ):
            if sprite == self.player:
                self.agent_reward += AGENT_REWARD_DEATH
                self.reset_player_position()
            return True
        return False

    def check_collision_with_warps(self):
        map_left_warp = (self.player.width / 2)  
        map_right_warp = self.map_x_bound - (self.player.width / 2)

        if self.player.center_x > map_right_warp:
            self.player.center_x = map_left_warp
        if self.player.center_x < map_left_warp:
            self.player.center_x = map_right_warp

    def check_collision_with_goal(self, sprite):
        if arcade.check_for_collision_with_list(
            sprite, self.scene[MAP_LAYER_GOAL]
        ):
            if sprite == self.player:
                if self.input_mode == INPUT_MODES[0]:
                    self.reset_player_position()
                else:
                    self.agent_reward += AGENT_REWARD_GOAL
                    self.agent.win = True
            return True
        return False
    
    def check_collision_with_goal_line(self, sprite):
        goal_line_start_x = self.player.center_x
        goal_line_start_y = self.player.center_y
        goal_line_end_x = self.goal_x
        goal_line_end_y = self.goal_y

        if arcade.geometry.check_for_collision_with_line(
            sprite,
            (goal_line_start_x, goal_line_start_y),
            (goal_line_end_x, goal_line_end_y),
        ):
            return True
        return False

    def check_collision_with_radar(self):
        radar_collisions = []
        for sprite in self.player.radar:
            collision_platform = self.check_collision_with_platforms(sprite)
            collision_deathground = self.check_collision_with_deathground(sprite)
            collision_goal = self.check_collision_with_goal(sprite)
            collision_goal_line = self.check_collision_with_goal_line(sprite)
            sprite_collisions = [collision_platform, collision_deathground, collision_goal, collision_goal_line]
            
            radar_collisions.append(sprite_collisions)
        
        return radar_collisions
    #endregion COLLISIONS

    #region CYCLE
    def on_update(self, delta_time):
        if self.input_mode == INPUT_MODES[1]:
            if self.agent.win:
                return
        
        self.physics_engine.update()

        if self.input_mode == INPUT_MODES[1]:
            self.update_agent_input()

        self.update_animations(delta_time)
        self.update_camera()
        self.update_dash(delta_time)
        self.check_collision_with_goal(self.player)
        self.check_collision_with_deathground(self.player)
        self.check_collision_with_warps()
        self.check_out_of_bounds()

        if self.input_mode == INPUT_MODES[1]:
            self.update_agent()

    def update_agent_input(self):
        if self.agent.learning_mode == AGENT_MODES[0]:
            self.agent_action = self.agent.random_action()
        else:
            self.agent_action = self.agent.best_action()
        
        self.reset_inputs()
        self.on_agent_input()

        self.agent_reward += AGENT_REWARD_STEP

    def update_agent(self):
        new_state = None

        if self.agent.learning_mode == AGENT_MODES[3]:
            new_state = self.check_collision_with_radar()
        else:
            new_state = (int(self.player.center_x), int(self.player.center_y))
            # new_state = self.player.center_x, self.player.center_y
        
        self.agent.update(
            self.agent_action,
            new_state,
            self.agent_reward,
        )
        
        self.agent_reward = 0

    def update_animations(self, delta_time):
        self.scene.update_animation(
            delta_time, [MAP_LAYER_BACKGROUND, MAP_LAYER_PLAYER]
        )

    def update_camera(self):
            screen_center_x = 0
            screen_center_y = self.player.center_y - (
                self.camera.viewport_height / 2
            )
            
            if screen_center_x < 0:
                screen_center_x = 0
            if screen_center_y < 0:
                screen_center_y = 0
            
            player_centered = screen_center_x, screen_center_y
            self.camera.move_to(player_centered, 0.2)

    def update_dash(self, delta_time):
        if self.dash_timer > 0:
            self.dash_timer -= delta_time
            dash_length = math.sqrt(self.dash_direction[0] ** 2 + self.dash_direction[1] ** 2)
            
            if dash_length > 0:
                self.dash_direction = (
                    self.dash_direction[0] / dash_length,
                    self.dash_direction[1] / dash_length,
                )
            
            self.player.change_x = self.dash_direction[0] * PLAYER_DASH_SPEED
            self.player.change_y = self.dash_direction[1] * PLAYER_DASH_SPEED
            
            self.dashing = True
        else:
            if self.dashing:
                self.player.change_x = PLAYER_MOVEMENT_SPEED * self.dash_direction[0]
                self.player.change_y = PLAYER_MOVEMENT_SPEED * self.dash_direction[1]
                self.dashing = False
                self.dash_cooldown = PLAYER_DASH_COOLDOWN
            
            if self.dash_cooldown > 0:
                self.dash_cooldown = max(0, self.dash_cooldown - delta_time)
            
            self.dash_timer = 0
            self.dash_direction = (0, 0)
    
    def reset_player_position(self):
        self.player.change_x = 0
        self.player.change_y = 0
        self.player.center_x = self.player_start_x
        self.player.center_y = self.player_start_y
    #endregion CYCLE
#endregion GAME

#region AGENT
class Agent:

    def __init__(self, x, y, x_bound, y_bound, learning_mode, learning_rate, discount_factor):
        self.start_x = x
        self.start_y = y
        self.state = self.start_x, self.start_y
        self.score = 0
        self.win = False
        
        self.learning_mode = learning_mode
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.qtable = {}

        if self.learning_mode == AGENT_MODES[2]:
            self.init_qtable_tiled(x_bound, y_bound)
            self.state = self.get_closest_state_tiled(*self.state)
        else:
            self.init_qtable_pixel(x_bound, y_bound)

    def init_qtable_pixel(self, x_bound, y_bound):
        for state in self.get_all_states_pixel(x_bound, y_bound):
            self.qtable[state] = {}
            for action in self.get_all_actions():
                self.qtable[state][action] = 0.0

    def init_qtable_tiled(self, x_bound, y_bound):
        for state in self.get_all_states_tiled(x_bound, y_bound):
            self.qtable[state] = {}
            for action in self.get_all_actions():
                self.qtable[state][action] = 0.0

    def get_all_states_pixel(self, x_bound, y_bound):
        return [
            (x, y) for x in range(0, x_bound + 1)
            for y in range(0, y_bound + 1)
        ]

    def get_all_states_tiled(self, x_bound, y_bound):
        return [
            (x, y) for x in range(0, x_bound + 1, int(TILE_PIXEL_SIZE))
            for y in range(0, y_bound + 1, int(TILE_PIXEL_SIZE))
        ]
    
    def get_closest_state_tiled(self, x, y):
        return (int((x // TILE_PIXEL_SIZE) * TILE_PIXEL_SIZE), int((y // TILE_PIXEL_SIZE) * TILE_PIXEL_SIZE))

    def get_all_actions(self):
        return AGENT_ACTIONS

    def best_action(self):
        return max(self.qtable[self.state], key=self.qtable[self.state].get)
    
    def random_action(self):
        return random.choice(AGENT_ACTIONS)
    
    def update(self, action, new_state, reward):
        if self.learning_mode == AGENT_MODES[2]:
            new_state = self.get_closest_state_tiled(*new_state)
        
        self.score += reward
        self.qtable[self.state][action] += reward
        maxQ = max(self.qtable[new_state].values())
        delta = self.learning_rate * (reward + self.discount_factor * maxQ - self.qtable[self.state][action])
        self.qtable[self.state][action] += delta
        self.state = new_state
    
    def reset(self):
        if self.learning_mode == AGENT_MODES[2]:
            self.state = self.get_closest_state_tiled(self.start_x, self.start_y)
        else:
            self.state = self.start_x, self.start_y

        self.score = 0
        self.win = False
#endregion AGENT

# Main function
def main():
    window = Game()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
