import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import pearsonr
import seaborn as sns
import plotly.express as px

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
                df = pd.read_csv(file_path)
                df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
                df = df[df['DateTime'] >= start_date]
                df['RoundedHour'] = df['DateTime'].apply(time_round)

                # Split the two :30 minutes rounded up and down
                df = df.explode('RoundedHour')

                # Change Column name when the title is a software instead of a game
                if 'Players' not in df.columns and 'Users' in df.columns:
                    df.rename(columns={'Users': 'Players'}, inplace=True)

                # Group the rounded hours together and average
                hour_avg_df = (
                    df.groupby('RoundedHour')['Players']
                    .mean()
                    .reset_index()
                    .rename(columns={'RoundedHour': 'DateTime', 'Players': 'AvgPlayers'})
                )

                # Save the new df to the filtered directory
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
                df = pd.read_csv(file_path)
                if 'DateTime' not in df.columns:
                    print(f'Error! "DateTime" column not found in {filename}. Skipping file...')
                    continue

                # Ensure DateTime column is read appropriately
                df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
                # Make DateTime the index, localize it to UTC, then change time zone appropriately
                df = df.set_index('DateTime')  # Set DateTime as index
                df = df.tz_localize('UTC', ambiguous='NaT')  # Assume timestamps are in UTC
                if timezone != 'UTC':
                    df = df.tz_convert(timezone)

                # Extract hours from DateTime in index, then average them across
                df['Hour'] = df.index.hour
                daily_avg_df = df.groupby('Hour')['AvgPlayers'].mean().reset_index()

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
                df = pd.read_csv(file_path)

                # Remove Hour column, extract statistics, transpose and remove index, then add game name
                df.pop('Hour')
                means.append(df.mean()['AvgPlayers'])
                std_devs.append(df.std()['AvgPlayers'])


            except Exception as e:
                print(f'Error processing {filename} due to: {e}')

    final_stats = pd.df({
        'Game': game_names,
        'Mean': means,
        'SD': std_devs
    })

    final_stats.to_csv(os.path.join(output_dir, 'Descriptives.csv'), index=False)

def data_stats(data_dir):

    """
    This function reads a data file within a directory and generates graphs using various parameters and graph types
    
    :param data_dir: Directory containing the daily-average files.
    """

    # Read the CSV file
    df = pd.read_csv(data_dir)

    # Run Correlation between player averages / year and booleans.
    bool_cols = ['isIndie','hasAchv','hasSteamCloud','accountRequired','hasKernel']
    vars = ['Mean', 'Year', 'Price']
    df[bool_cols] = df[bool_cols].astype(bool)
    # Count the Player columm with hasSteamCloud = True

    df_playertype = (
        df
        .groupby("Player")
        .apply(
            lambda group: group.hasSteamCloud.eq(False).sum()
        )
    )

    print(f'Amount of games without Steam Cloud: \n{df_playertype.to_string()}')


    for var in vars:
        for col in bool_cols:
            y = pearsonr(df[var], df[col])
            if y.pvalue < 0.05:
                sig = '*'
            else:
                sig = ''
            print(f'Correlation between {var} and {col}: r = {y.statistic:.3f}, p = {y.pvalue:.3f} {sig}')
        print('\n')

    print(pearsonr(df['Price'], df['Year']))

def genre_stats(data_dir):
    '''
    Quick genre dummy code followed by correlations
    :param data_dir:
    '''

    # Read the file
    df = pd.read_csv(data_dir)

    # Obtain genres and dummy code
    genres = df[['Genre_1', 'Genre_2', 'Genre_3', 'Genre_4', 'Genre_5']].agg(','.join, axis=1)
    genre_coded = genres.str.get_dummies(sep=',')

    # Combine dummy codes with mean values
    result = pd.concat([df[['Mean']], genre_coded], axis=1)

    # Initialize correlations list to print
    correlation_results = []

    for genre in genre_coded.columns:
        correlation, p_value = pearsonr(result['Mean'], result[genre])

        sig = '*' if p_value < 0.05 else ''
        correlation_results.append((genre, correlation, p_value, sig))

    # Correlation size quick function
    def get_correlation_magnitude(item):
        return abs(item[1])

    # Sort by correlation magnitude
    correlation_results.sort(key=get_correlation_magnitude, reverse=True)

    # Print the sorted results
    for genre, correlation, p_value, sig in correlation_results:
        print(f'Correlation between Mean and {genre}: r = {correlation:.3f}, p = {p_value:.3f} {sig}')


    # Calculate correlation matrix for genres
    correlation_matrix = result.corr(method='pearson')

    # Convert for Plotly
    correlation_long = correlation_matrix.reset_index().melt(id_vars='index')
    correlation_long.columns = ['Variable 1', 'Variable 2', 'Correlation']

    # Initiate plotly
    fig = px.imshow(
        correlation_matrix,
        text_auto=".2f",  # Show values
        color_continuous_scale='RdBu',
        zmin=-1, zmax=1,  # Set the color range
        aspect="auto",
    )

    # Customize hover information
    fig.update_traces(
        hovertemplate='<b>%{x}</b> & <b>%{y}</b><br>Correlation: %{z:.2f}<extra></extra>'
    )

    # Add title and improve layout
    fig.update_layout(
        title='Interactive Genres Matrix',
        xaxis_tickangle=-45,
        width=1000,  # Adjust width for large matrices
        height=1000,  # Adjust height for large matrices
    )

    # Write file
    fig.write_html("interactive_correlation_matrix.html")

    #  Correlation heatmap figure (high res)
    plt.figure(figsize=(90,75), dpi=300)
    sns.heatmap(
        correlation_matrix,
        annot=True,  # Display correlation values
        fmt=".2f",  # Format the correlation values
        cmap='coolwarm',  # Color palette for easy visualization
        center=0,  # Center the color gradient at 0
        square=True,  # Keep the heatmap cells square-shaped
        linewidths=0.5,  # Add lines between cells
        cbar_kws={"shrink": 0.75}  # Adjust color bar size
    )

    # Customize the plot
    plt.title('Correlation Matrix across Genre and Mean', fontsize=16)
    plt.xticks(rotation=90, fontsize=12)
    plt.yticks(rotation=0, fontsize=12)
    plt.savefig('correlation_matrix.png', bbox_inches='tight')

    plt.close()





