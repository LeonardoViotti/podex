load_log_df = False

if load_log_df:
    log_df = pd.read_csv('log_df')
# Take original species data set as a new log_df
else:
    # Create a logging data_frame
    log_df = crawl.spc_df
    log_df = log_df[['code', 'name', 'pic']]
    
    # Add column that has number of pictures already downloaded. At the start zero
    log_df['downloaded_pics'] = 0


n = 3
# codes_list = [10001]
codes_list = None

# If a list isn't provided choose a random sample that hasn't yet been scraped
if codes_list is None:
    # Filter only species that haven't yet been scraped yet
    codes = log_df[log_df['downloaded_pics'] == 0]['code'].unique()
    
    # Randomly select species code to scrape
    def scrambled(orig):
        dest = orig[:]
        random.shuffle(dest)
        return dest
    codes = scrambled(codes)
else:
    codes = codes_list



# Restrict the number of pages done this session
codes = codes[0:n]
codes = [11913, 11116, 11581] 


# code = 10005
for code in codes:
    # Print for which species it is running!
    print(code)
    crawl.load_all_pics(code, limit = 10)
    crawl.download_images()
    log_df.loc[log_df['code'] == code, 'downloaded_pics'] = crawl.current_urls_df['downloaded'].sum()

# After session save log csv
# log_df.to_csv('log_df.csv', index = False)