# Mephistophelia

2D platformer Q-learning AI using Python Arcade

## How to

### In terminal

- `pip install arcade`
- `py ./main.py`

### In Game

- press `R` during play to reset and watch the learning occur
- press `ENTER` during play to save the progress of the AI (existing save is auto-loaded)
- press `ESCAPE` during play to close the game (does not save on quit!)

### In Code

In `main()`:
- change `map_path` to try out different environments (maps can be found in `/assets/maps/`)
- change `play_mode` to play yourself or let the AI train
- change `view_mode` to view state or to auto-reset on win
- change `learning_mode`, `learning_rate` and `discount_factor` to change learning strategies
