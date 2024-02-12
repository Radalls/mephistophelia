import arcade

from src.constants import CHARACTER_SCALING, PLAYER_LEFT_FACING, PLAYER_RIGHT_FACING

class Player(arcade.Sprite):

    def __init__(self, player_path):
        super().__init__()

        # Set player to face right at start
        self.character_face_direction = PLAYER_RIGHT_FACING

        # Used for flipping between image sequences
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        # Load textures for idle poses
        self.idle_texture_pair = self.load_texture_pair(f"{player_path}_idle.png")
        self.jump_texture_pair = self.load_texture_pair(f"{player_path}_jump.png")
        self.fall_texture_pair = self.load_texture_pair(f"{player_path}_fall.png")

        # Load textures for walking
        self.walk_textures = []
        for i in range(8):
            texture = self.load_texture_pair(f"{player_path}_walk{i}.png")
            self.walk_textures.append(texture)

        # Set player initial texture
        self.texture = self.idle_texture_pair[0]

        # Set player hit box
        self.hit_box = self.texture.hit_box_points

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
