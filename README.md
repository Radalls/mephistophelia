# Mephistophelia

2D platformer Q-learning AI using Python Arcade

## How to

### In terminal

- `pip install arcade`
- `py ./main.py`

### In Game

- press `ESCAPE` during play to close the game (does not save on quit!)
- press `ENTER` during play to save the progress of the AI (existing save is auto-loaded)
- press `R` during play to reset and watch the learning occur
- press `N` during play to temporarily add noise to the AI actions (avoid local optima)
- press `F` during play to alternate between regular or ultra fast speed (speed up learning)

### In Code

In `main()`:
- change `map_path` to try out different environments (maps can be found in `/assets/maps/`)
- change `play_mode` to play yourself or let the AI train
- change `view_mode` to view state or to auto-reset on win
- change `learning_mode`, `learning_rate` and `discount_factor` to change learning strategies

### In Files

- `t1`, `t2` or `t3` stands for each training session, where the agent was trained in each map with a specific strategy in mind
    + `t2` was the most successful attempt, using the strategy of quickly lowering the `learning_rate` param.
- You can review all graphs results for each training session in `plots`
    + Graphs display the score of the agent when touching the goal, it does not account for the delay between attempts
- You can load one of our qtables by placing it at root folder and renaming it `agent.qtable`
- unless you know how to use the `Tiled` software, don't touch the maps.


Have fun with this project !