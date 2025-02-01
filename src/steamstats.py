import os
import pandas as pd
import matplotlib.pyplot as plt

def csv_processor(source_dir, filtered_dir, start_date):
    """
    This function takes all CSV files in a provided directory, identifies the DateTime column,
    filters the data to start at a specified date, then rounds minute data to the closest hour mark.
    These data are then averaged and returned as a new timeline with hour-by-hour data across the timeline filter.
    Logistically, :30 minute marked data are duplicated and put on both hour marks to retain uniformity.

    :param source_dir: Directory containing the original CSV files
    :param filtered_dir: Directory where processed files are saved
    :param start_date: The date to filter data from
    :return: Processed files with filtered dates, and averaged data onto the closest hour mark.
    """

    # Create filtered directory if it does not exist
    os.makedirs(filtered_dir, exist_ok=True)

    # Quick function to round timestamps
    def time_round(dt):
        minute = dt.minute

        # Define lookup dictionary for 10-minute marker time data [Note: SteamDB uses 10-minute marks up to two weeks
        rounding_map = {
            0:  [dt],
            10: [dt.replace(minute=0, second=0)], # Round down
            20: [dt.replace(minute=0, second=0)], # Round down
            30: [dt.replace(minute=0, second=0), (dt + pd.Timedelta(hours=1)).replace(minute=0, second=0)], # Round both
            40: [(dt + pd.Timedelta(hours=1)).replace(minute=0, second=0)], # Round up
            50: [(dt + pd.Timedelta(hours=1)).replace(minute=0, second=0)] # Round up
        }
        return rounding_map[minute]

    for filename in os.listdir(source_dir):
        if filename.endswith(".csv"):
            file_path = os.path.join(source_dir, filename)
            print(f'Processing {filename}...')

            try:
                # Read file, ensure column match, filter date from parameter, & apply time round function
                dataframe = pd.read_csv(file_path)
                dataframe['DateTime'] = pd.to_datetime(dataframe['DateTime'], errors='coerce')
                dataframe = dataframe[dataframe['DateTime'] >= start_date]
                dataframe['RoundedHour'] = dataframe['DateTime'].apply(time_round)

                # Split the two :30 minutes rounded up and down
                dataframe = dataframe.explode('RoundedHour')

                # Change Column name when the title is a software instead of a game
                if 'Players' not in dataframe.columns and 'Users' in dataframe.columns:
                    dataframe.rename(columns={'Users': 'Players'}, inplace=True)

                # Group the rounded hours together and average
                hour_avg_df = (
                    dataframe.groupby('RoundedHour')['Players']
                    .mean()
                    .reset_index()
                    .rename(columns={'RoundedHour': 'DateTime', 'Players': 'AvgPlayers'})
                )

                # Save the new dataframe to the filtered directory
                output_file_path = os.path.join(filtered_dir, f"filtered_{filename}")
                hour_avg_df.to_csv(output_file_path, index=False)
                print(f'Processed file saved in {output_file_path}')

            except Exception as e:
                print(f'Error with processing {filename} due to: {e}')

        print("Finished :)")

def daily_avg(filtered_dir, averaged_dir, timezone = 'UTC'):
    """
    This function processes the filtered CSV files in a specified filtered file directory,
    changes the time stamps to match a specified timezone offset,
    averages the data across each of the 24-hour marks,
    and returns a daily average timeline to the specified output directory.

    :param filtered_dir: Directory containing the filtered CSV files (ran through csv_processor)
    :param averaged_dir: Directory where the daily-average files are saved
    :param timezone: Timezone to offset the timeline to (see pytz.all_timezones for a list) ; default is UTC
    :return: Timelines as a 24-hour day average across the filtered period (most likely two weeks post-extraction)
    """

    # Create filtered directroy if it does not exist
    os.makedirs(averaged_dir, exist_ok=True)

    for filename in os.listdir(filtered_dir):
        if filename.endswith(".csv"):
            file_path = os.path.join(filtered_dir, filename)
            print(f'Processing {filename}...')

            try:
                # Read file and ensure valid columns
                dataframe = pd.read_csv(file_path)
                if 'DateTime' not in dataframe.columns:
                    print(f'Error! "DateTime" column not found in {filename}. Skipping file...')
                    continue

                # Ensure DateTime column is read appropriately
                dataframe['DateTime'] = pd.to_datetime(dataframe['DateTime'], errors='coerce')
                # Make DateTime the index, localize it to UTC, then change time zone appropriately
                dataframe = dataframe.set_index('DateTime')  # Set DateTime as index
                dataframe = dataframe.tz_localize('UTC', ambiguous='NaT')  # Assume timestamps are in UTC
                if timezone != 'UTC':
                    dataframe = dataframe.tz_convert(timezone)

                # Extract hours from DateTime in index, then average them across
                dataframe['Hour'] = dataframe.index.hour
                daily_avg_df = dataframe.groupby('Hour')['AvgPlayers'].mean().reset_index()

                # Save file
                output_file_path = os.path.join(averaged_dir, f"daily_avg_{filename}")
                daily_avg_df.to_csv(output_file_path, index=False)

                print(f'Processed file saved in {output_file_path}')

            except Exception as e:
                print(f'Error processing {filename} due to: {e}')


    print('Finished :)')

def desc_stats(averaged_dir, output_dir):
    """
    This function takes the daily averaged files and calculates descriptive statistics. It reads files
    from a specified averaged file directory and returns a single file with the descriptive statistics for all files onto
    a specified output directory.

    :param averaged_dir: The directory containing the daily-average files.
    :param output_dir: The directory where the descriptive statistics for all files will be saved.
    :return: Descriptive statistics for all daily-average files onto a singular file.
    """

    # Check if output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Initiate master lists
    game_names = []
    means = []
    std_devs = []

    for filename in os.listdir(averaged_dir):
        if filename.endswith(".csv"):
            file_path = os.path.join(averaged_dir, filename)
            print(f'Processing {filename}...')

            try:
                # Extract game name and append to list
                game_name = filename.replace('daily_avg_filtered_',"").replace(".csv","")
                game_names.append(game_name)

                # Read csv file
                dataframe = pd.read_csv(file_path)

                # Remove Hour column, extract statistics, transpose and remove index, then add game name
                dataframe.pop('Hour')
                means.append(dataframe.mean()['AvgPlayers'])
                std_devs.append(dataframe.std()['AvgPlayers'])


            except Exception as e:
                print(f'Error processing {filename} due to: {e}')

    final_stats = pd.DataFrame({
        'Game': game_names,
        'Mean': means,
        'SD': std_devs
    })

    final_stats.to_csv(os.path.join(output_dir, 'Descriptives.csv'), index=False)

def graph_stats(data_dir):
    """
    This function reads a data file within a directory and generates graphs using various parameters and graph types
    
    :param data_dir: Directory containing the daily-average files.
    :return: 
    """

    # Read the CSV file
    df = pd.read_csv(data_dir)