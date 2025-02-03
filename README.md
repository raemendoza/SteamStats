# Steam Stats Project
An exploratory analysis on popular games in Steam.

## Navigation
You can find all the data files used in `GameData`. Data was obtained publicly through SteamDB and Steam's store page.
You can find the processing code and a WIP analysis code in `src` >>>
- `config.py` contains the directories to run all code
- `main.py` contains the execution for the functions
- `steamstats.py` contains the functions

You can find the required dependencies in `requirements.txt`

Within GameData, you can find:
- `Raw Data`: The raw summarized average players from SteamDB per game. Runs back for years and only begins to provide hour-by-hour on mid-December (about 2 weeks prior to extraction)
- `Filtered Data`: The raw data is cropped to only include days with hourly data. Minute-specific data is rounded to the nearest hour and averaged (:30 minute marks are put in both hour marks)
- `Averaged Data/UTC`: The filtered data is aggregated across 24-hours and compiled to provide a daily average of game activity. Meant to investigate for circadian patterns, although there are geographical limitations.
- `Stat Data`: Contains a generated descriptive file with mean and standard deviations of Averaged Data. The `_edited` version was manually curated using Steam store page and includes various parameters for analyses:

## To-Do List
- Visualize the rest of the data

## Paramaters in Data
  * **Genre_1 to 5**: Five common tags used for the game within the Steam store
  * **Player**: The amount of players possible in a session (Singleplayer, Multiplayer or Hybrid). Does not disambiguate between PvP, PvE, and Co-Op
  * **Developer**: uses 'hasMultiple' if there is more than one
  * **Publisher**: same exception as Developer
  * **isIndie**: a dichotomous variable for whether the game is independently created and published (may be fallible)
  * **hasAchv**: a dichotomous variable for whether the game has Steam Achievements (may be fallible or incorrectly checked)
  * **hasSteamCloud**: a dichotomous variable for whether the game has Steam Cloud features (may be fallible or incorrectly checked)
  * **controllerSupport**: a numerical variable denoting the type of controller support (0 = none, 1 = partial, 2 = full); (may be fallible or incorrectly checked)
  * **accountRequired**: a dichotomous variable for whether the game requires the creation of another account outside of Steam
  * **hasKernel**: a dichotomous variable for whether the game required a kernel-level antichea
