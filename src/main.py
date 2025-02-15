from config import SOURCE_DIR, FILTERED_DIR, AVERAGED_DIR, OUTPUT_DIR, START_DATE, TIMEZONE, DATA_DIR
from steamstats import csv_processor, daily_avg, desc_stats, data_stats, genre_stats

# Run csv_processor
# csv_processor(SOURCE_DIR, FILTERED_DIR, START_DATE)

# Run daily_avg
# daily_avg(SOURCE_DIR, AVERAGED_DIR, TIMEZONE)

# Run desc_stats
# desc_stats(AVERAGED_DIR, OUTPUT_DIR)

# Run graph
# data_stats(DATA_DIR)

# Run Genre Stats
genre_stats(DATA_DIR)
