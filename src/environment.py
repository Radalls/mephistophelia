import math
import os
import arcade

from src.constants import \
    AGENT_ACTIONS, AGENT_REWARD_DEATH, AGENT_REWARD_GOAL, AGENT_REWARD_STEP, \
    GRAVITY, \
    MAP_LAYER_BACKGROUND, MAP_LAYER_DEATHGROUND, MAP_LAYER_FOREGROUND, MAP_LAYER_GOAL, MAP_LAYER_PLATFORMS, MAP_LAYER_PLAYER, \
    PLAY_MODES,\
    PLAYER_DASH_COOLDOWN, PLAYER_DASH_DURATION, PLAYER_DASH_SPEED, PLAYER_JUMP_SPEED, PLAYER_MOVEMENT_SPEED, \
    SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_WIDTH, \
    TILE_PIXEL_SIZE, TILE_SCALING, \
    VIEW_MODES
from src.agent import Agent
from src.player import Player

class Environment(arcade.Window):

    def __init__(self):
        # Set game window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Set origin path
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Tilemap Object
        self.tile_map = None

        # Game Scene Object
        self.scene = None

        # Physics engine Object
        self.physics_engine = None

        # Camera Object
        self.camera = None
        self.gui_camera = None

        # State machine
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.space_pressed = False
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_direction = (0, 0)
        self.win = False

        # Mode
        self.play_mode = None
        self.view_mode = None

        # Map bounds
        self.map_x_bound = 0
        self.map_y_bound = 0

        # Goal object
        self.goal_x = 0
        self.goal_y = 0

        # Player Object
        self.player = None
        self.player_start_x = 0
        self.player_start_y = 0

        # AI agent
        self.agent = None
        self.agent_reward = 0
        self.agent_action = None
        self.agent_radars = None
        self.agent_hitbox = None
        self.agent_save_path = None

        # Texts
        self.text_quit_action = arcade.Text(
            text='Press ESC to quit',
            start_x=self.width - TILE_PIXEL_SIZE * 3,
            start_y=self.height - 10,
            color=arcade.color.ORANGE,
            font_size=10,
            anchor_x="left",
            anchor_y="top",
        )
        self.text_reset_action = arcade.Text(
            text='Press R to reset',
            start_x=self.width - TILE_PIXEL_SIZE * 3,
            start_y=self.height - 30,
            color=arcade.color.ORANGE,
            font_size=10,
            anchor_x="left",
            anchor_y="top",
        )
        self.text_win = arcade.Text(
            text=f'win: ',
            start_x=TILE_PIXEL_SIZE,
            start_y=self.height - 10,
            color=arcade.color.GREEN,
            anchor_x="left",
            anchor_y="top",
        )
        self.text_agent_action = arcade.Text(
            text=f'action: ',
            start_x=TILE_PIXEL_SIZE,
            start_y=self.height - 30,
            anchor_x="left",
            anchor_y="top",
        )
        self.text_agent_state = arcade.Text(
            text=f'state: ',
            start_x=TILE_PIXEL_SIZE,
            start_y=self.height - 50,
            anchor_x="left",
            anchor_y="top",
        )
        self.text_agent_score = arcade.Text(
            text=f'score: ',
            start_x=TILE_PIXEL_SIZE,
            start_y=self.height - 70,
            anchor_x="left",
            anchor_y="top",
        )
        self.text_agent_noise = arcade.Text(
            text=f'noise: ',
            start_x=TILE_PIXEL_SIZE,
            start_y=self.height - 90,
            anchor_x="left",
            anchor_y="top",
        )
        self.text_agent_noise_action = arcade.Text(
            text='Press N to noise',
            start_x=self.width - TILE_PIXEL_SIZE * 3,
            start_y=self.height - 50,
            color=arcade.color.ORANGE,
            font_size=10,
            anchor_x="left",
            anchor_y="top",
        )
        self.text_agent_save_action = arcade.Text(
            text='Press ENT to save',
            start_x=self.width - TILE_PIXEL_SIZE * 3,
            start_y=self.height - 70,
            color=arcade.color.ORANGE,
            font_size=10,
            anchor_x="left",
            anchor_y="top",
        )
        self.text_human_dash = arcade.Text(
            text=f'dash: ',
            start_x=TILE_PIXEL_SIZE,
            start_y=self.height - 30,
            anchor_x="left",
            anchor_y="top",
        )

    def setup(self, player_path, map_path, save_path, play_mode, view_mode, learning_mode, learning_rate, discount_factor):
        # Set mode
        self.play_mode = play_mode
        self.view_mode = view_mode
        
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
        self.tile_map = arcade.load_tilemap(map_path, TILE_SCALING, map_layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Locate edges of the map
        self.map_x_bound = int(self.tile_map.width * TILE_PIXEL_SIZE)
        self.map_y_bound = int(self.tile_map.height * TILE_PIXEL_SIZE)

        # Load the player layer
        self.scene.add_sprite_list_after(MAP_LAYER_PLAYER, MAP_LAYER_FOREGROUND)

        # Set the player at start position
        self.player = Player(player_path)
        self.player_start_x = int(self.tile_map.get_tilemap_layer("Player").properties["start_x"]) * TILE_PIXEL_SIZE - TILE_PIXEL_SIZE / 2
        self.player_start_y = int(self.tile_map.get_tilemap_layer("Player").properties["start_y"]) * TILE_PIXEL_SIZE - TILE_PIXEL_SIZE / 2
        self.player.center_x = self.player_start_x
        self.player.center_y = self.player_start_y
        self.scene.add_sprite(MAP_LAYER_PLAYER, self.player)

        # Locate goal
        self.goal_x = int(self.tile_map.get_tilemap_layer("Goal").properties["x"]) * TILE_PIXEL_SIZE - TILE_PIXEL_SIZE / 2
        self.goal_y = int(self.tile_map.get_tilemap_layer("Goal").properties["y"]) * TILE_PIXEL_SIZE - TILE_PIXEL_SIZE / 2
        
        # Set the background color
        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        # Set the physics engine
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            gravity_constant=GRAVITY,
            walls=self.scene[MAP_LAYER_PLATFORMS]
        )

        # Set the AI agent
        if self.is_agent_play():
            self.agent = Agent(
                int(self.player_start_x),
                int(self.player_start_y),
                self.map_x_bound,
                self.map_y_bound,
                learning_mode = learning_mode,
                learning_rate = learning_rate,
                discount_factor = discount_factor,
            )

            self.agent_save_path = save_path
            self.agent.load_save(save_path)

            if self.agent.is_learning_radar():
                self.agent_radars = []

                # Set the radars
                # left - right - up - up_left - up_right - down_left - down_right
                for i in range(0, 7):
                    self.agent_radars.append(arcade.Sprite(
                        '../assets/sprites/radar/radar.png',
                        image_height=TILE_PIXEL_SIZE,
                        image_width=TILE_PIXEL_SIZE,
                        center_x=TILE_PIXEL_SIZE / 2,
                        center_y=TILE_PIXEL_SIZE / 2,
                    ))
                    self.scene.add_sprite(MAP_LAYER_PLAYER, self.agent_radars[i])

                # Set the hitbox
                self.agent_hitbox = arcade.Sprite(
                    '../assets/sprites/radar/hitbox.png',
                    center_x=self.player.center_x,
                    center_y=self.player.center_y,
                )
                self.scene.add_sprite(MAP_LAYER_PLAYER, self.agent_hitbox)
                
                # Set radars positions
                self.process_agent_radar()

            self.agent.state = self.update_agent_state()
            if self.agent.is_learning_radar():
                self.agent.add_state(self.agent.state)

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw()

        if self.is_agent_play() and self.agent.is_learning_radar():
            arcade.draw_line(self.player.center_x, self.player.center_y, self.goal_x, self.goal_y, arcade.color.YELLOW, 2)
        
        self.gui_camera.use()

        self.text_quit_action.draw()
        self.text_reset_action.draw()
        
        self.text_win.text = f'win: {self.win}'
        self.text_win.draw()

        if self.is_human_play():
            self.draw_human_gui()
        elif self.is_agent_play():
            self.draw_agent_gui()

    def draw_human_gui(self):
        self.text_human_dash.text = f'dash: {int(self.dash_cooldown)}'
        self.text_human_dash.draw()

    def draw_agent_gui(self):
        self.text_agent_save_action.draw()
        self.text_agent_noise_action.draw()

        self.text_agent_action.text = f'action: {self.agent_action}'
        self.text_agent_state.text = f'state: {self.agent.state}'
        self.text_agent_score.text = f'score: {self.agent.score}'
        self.text_agent_noise.text = f'noise: {self.agent.noise:.2f}'

        self.text_agent_action.draw()
        self.text_agent_state.draw()
        self.text_agent_score.draw()
        self.text_agent_noise.draw()
        

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
            self.reset_player_position(reset_agent=False)
        elif key == arcade.key.N:
            if self.is_agent_play():
                self.agent.noise = 1
                self.reset_player_position()
        elif key == arcade.key.ENTER:
            if self.is_agent_play():
                self.agent.save(self.agent_save_path)
        elif key == arcade.key.ESCAPE:
            if self.is_agent_play():
                print(self.agent.qtable)
            arcade.close_window()

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
            self.left_pressed = True
            self.up_pressed = True
        elif self.agent_action == AGENT_ACTIONS[3]:
            self.right_pressed = True
            self.up_pressed = True

        self.on_key_change()

    def on_key_change(self):
        self.process_movement()
        self.process_jump()
        self.process_dash()

        if self.is_agent_play() and self.agent.is_learning_radar():
            self.process_agent_radar()

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
    
    def process_agent_radar(self):
        # left
        self.agent_radars[0].center_x = self.player.center_x - TILE_PIXEL_SIZE
        self.agent_radars[0].center_y = self.player.center_y - TILE_PIXEL_SIZE / 2
        # right
        self.agent_radars[1].center_x = self.player.center_x + TILE_PIXEL_SIZE
        self.agent_radars[1].center_y = self.player.center_y - TILE_PIXEL_SIZE / 2
        # up
        self.agent_radars[2].center_x = self.player.center_x
        self.agent_radars[2].center_y = self.player.center_y + TILE_PIXEL_SIZE * 1.5
        # up_left
        self.agent_radars[3].center_x = self.player.center_x - TILE_PIXEL_SIZE
        self.agent_radars[3].center_y = self.player.center_y + TILE_PIXEL_SIZE * 1.5
        # up_right
        self.agent_radars[4].center_x = self.player.center_x + TILE_PIXEL_SIZE
        self.agent_radars[4].center_y = self.player.center_y + TILE_PIXEL_SIZE * 1.5
        # down_left
        self.agent_radars[5].center_x = self.player.center_x - TILE_PIXEL_SIZE
        self.agent_radars[5].center_y = self.player.center_y - TILE_PIXEL_SIZE * 1.5
        # down_right
        self.agent_radars[6].center_x = self.player.center_x + TILE_PIXEL_SIZE
        self.agent_radars[6].center_y = self.player.center_y - TILE_PIXEL_SIZE * 1.5
        # hitbox
        self.agent_hitbox.center_x = self.player.center_x
        self.agent_hitbox.center_y = self.player.center_y
    #endregion ACTIONS

    #region COLLISIONS
    def check_out_of_bounds(self):
        if self.player.center_y < -100:
            if self.is_human_play():
                self.reset_player_position()
            elif self.is_agent_play():
                self.agent_reward += AGENT_REWARD_DEATH
                self.reset_player_position(reset_agent=False)

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
                if self.is_human_play():
                    self.reset_player_position()
                elif self.is_agent_play():
                    self.agent_reward += AGENT_REWARD_DEATH
                    self.reset_player_position(reset_agent=False)
            return True
        return False

    def check_collision_with_warps(self, sprite):
        map_left_warp = (sprite.width / 2)  
        map_right_warp = self.map_x_bound - (sprite.width / 2)

        if sprite.center_x > map_right_warp:
            sprite.center_x = map_left_warp
        if sprite.center_x < map_left_warp:
            sprite.center_x = map_right_warp

    def check_collision_with_goal(self, sprite):
        if arcade.check_for_collision_with_list(
            sprite, self.scene[MAP_LAYER_GOAL]
        ):
            if sprite == self.player:
                self.win = True

                if self.is_agent_play():
                    self.agent_reward += AGENT_REWARD_GOAL
            return True
        return False
    #endregion COLLISIONS

    #region CYCLE
    def on_update(self, delta_time):
        if self.win:
            if self.is_analytic_view():
                return
            elif self.is_auto_view():
                self.reset_player_position()
        
        self.physics_engine.update()

        if self.is_agent_play():
            self.update_agent_input()

        self.update_animations(delta_time)
        self.update_camera()
        self.update_dash(delta_time)
        self.check_collision_with_goal(self.player)
        self.check_collision_with_deathground(self.player)
        self.check_collision_with_warps(self.player)
        self.check_out_of_bounds()

        if self.is_agent_play():
            self.update_agent()

    def update_agent_input(self):
        if self.agent.is_learning_random():
            self.agent_action = self.agent.random_action()
        else:
            self.agent_action = self.agent.best_action()
        
        self.reset_inputs()
        self.on_agent_input()

        self.agent_reward += AGENT_REWARD_STEP

    def update_agent(self):
        new_state = self.update_agent_state()
        
        self.agent.update(
            self.agent_action,
            new_state,
            self.agent_reward,
        )
        
        self.agent_reward = 0

    def update_agent_state(self):
        if self.agent.is_learning_radar():
            return self.update_agent_radar_state()
        else:
            return (int(self.player.center_x), int(self.player.center_y))

    def update_agent_radar_state(self):
        radars_state = []
        radars_to_goal = []

        for radar in self.agent_radars:
            collision_platform = self.check_collision_with_platforms(radar)
            collision_deathground = self.check_collision_with_deathground(radar)
            collision_goal = self.check_collision_with_goal(radar)

            if collision_platform:
                radar_state = ('PF', False)
            elif collision_deathground:
                radar_state = ('DG', False)
            elif collision_goal:
                radar_state = ('GO', False)
            else:
                radar_state = ('*', False)

            radar_to_goal = math.sqrt((radar.center_x - self.goal_x) ** 2 + (radar.center_y - self.goal_y) ** 2)
            radars_to_goal.append(radar_to_goal)

            radars_state.append(radar_state)

        closest_radar_index = radars_to_goal.index(min(radars_to_goal))
        radars_state[closest_radar_index] = (radars_state[closest_radar_index][0], True)

        return tuple(radars_state)

    def update_animations(self, delta_time):
        self.scene.update_animation(
            delta_time, [MAP_LAYER_BACKGROUND, MAP_LAYER_PLAYER]
        )

    def update_camera(self):
        camera_x = 0
        camera_y = self.player.center_y - (self.camera.viewport_height / 2)

        if camera_y < 0:
            camera_y = 0
        elif camera_y > self.map_y_bound - self.camera.viewport_height:
            camera_y = self.map_y_bound - self.camera.viewport_height

        self.camera.move_to((camera_x, camera_y), 0.2)

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
    
    def reset_player_position(self, reset_agent=True):
        self.player.change_x = 0
        self.player.change_y = 0
        self.player.center_x = self.player_start_x
        self.player.center_y = self.player_start_y
        self.reset_inputs()
        self.win = False

        if self.is_agent_play() and reset_agent:
            self.agent.state = self.update_agent_state()
            self.agent.reset()
    #endregion CYCLE
        
    #region UTILS
    def is_human_play(self):
        return self.play_mode == PLAY_MODES[0]
    
    def is_agent_play(self):
        return self.play_mode == PLAY_MODES[1]
    
    def is_analytic_view(self):
        return self.view_mode == VIEW_MODES[0]
    
    def is_auto_view(self):
        return self.view_mode == VIEW_MODES[1]
    #endregion UTILS
