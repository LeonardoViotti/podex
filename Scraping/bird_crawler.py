# TODO
#   - Loop over species
#   - Add random delays?
#   - Hide IP?
#   CODE REORGANIZATION AND ABSTRACTION
#   DOCKER TO FOLDER LINK

#--------------------------------------------------------------------------------
import os
import sys
import time
from datetime import date

import logging
import pandas as pd
import requests
import json
import shutil
import random
from time import sleep

#--------------------------------------------------------------------------------
# Set up logging
today = date.today().strftime("%d-%m-%Y")
logging.basicConfig(filename='logs/crawler-' + today + '.log', 
                    filemode='w', 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    # level = logging.DEBUG,
                    level = logging.INFO)
# Add handlder to also print on terminal
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logging.info('Bird Crawler %s', date.today().strftime("%d-%m-%Y"))

#--------------------------------------------------------------------------------
class BirdCrawler():
    """
    
    Attributes
    ----------
    
    Methods
    -------
    """
    
    def __init__(self,
                 request_base_url,
                 create_progress_df = False,
                 data_path = '../data/scraping/',
                 species_csv_path = '../data/scraping/all_species.csv'):
        """
        Parameters
        ----------
        request_base_url : A string containing an http request URL that can be formated with params for species code
        and page number.
        
        species_csv_path : Path to csv file containg all species codes and number of pics
        """
        
        self.request_base_url = request_base_url        
        self.data_path = data_path
        
        # Make sure dir to store results exists
        self.save_dir = os.path.join(self.data_path + 'pictures')
        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)
        
        if create_progress_df:
            self.spc_df = pd.read_csv(species_csv_path)
            self.create_progress_df()
        else:
            self.spc_df = pd.read_csv(os.path.join(self.save_dir, 'all_species_progress.csv'))
        
    def create_progress_df(self):
        self.spc_df['downloaded'] = 0
        self.spc_df.to_csv(os.path.join(self.save_dir, 'all_species_progress.csv'), index = False)
    
    def http_request(self, code, page):
        """
        Sends an hhtp request to get a JSON response that cotains pic links
        """
        request_str = self.request_base_url
        
        request_str_ij = request_str.format(code = code, page = page)
        res_ij = requests.get(request_str_ij,  verify=False)
        logging.info('Accessed %s ..', request_str_ij)
        return res_ij
    
    def process_request(self, request):
        """
        Processes received JSON to create a pic URL data frame
        """
        json_data = json.loads(request.text)
        # Pretty JSON for printiting
        # json_formatted_str = json.dumps(json_data, indent=2)
        # # print(json_formatted_str)
        
        # Num fotos
        # int(json_data['registros']['total'])
        
        # Get Json items
        items = json_data['registros']['itens']
        
        # If there are any items convert to df
        if bool(items):
            # Convert to df
            df = pd.DataFrame.from_dict(items).T
            # Keep fewer columns
            df = df[['id', 'local', 'idMunicipio', 'coms', 'likes', 'vis', 'grande', 'link']]
            # Process links to remove character 
            df['link'] = df['link'].str.replace('#','')
            # Add download progress columns
            df['downloaded'] = 0
            df['filename'] = ""
            return df
        else:
            return None
    
    def download_images(self, dirname, urls_df, max_pictures, start_index = 0):
        """
        Downloads images from a DataFrame of URLs and returns a CSV
        with a record of which URLs where downloaded
        
        Parameters
        ----------
        dirname : path to save images
        urls_df : padas.DataFrame with a str 'urls' column
        """
        
        # Set saving function
        def save_image_to_file(image, dirname, suffix):
            with open('{dirname}/{suffix}.jpg'.format(dirname=dirname, suffix=suffix), 'wb') as out_file:
                shutil.copyfileobj(image.raw, out_file)
        
        # Downloaded flag
        to_download = urls_df[urls_df['downloaded'] == 0].index
        
        # Loop through dataframe
        length = len(to_download)
        for idx in to_download:
            # Set index in relation to all the pictures
            global_index = start_index + int(idx)
            print('Downloading {0} of {1} images'.format(global_index, max_pictures))
            # Select which url to downlaod
            url = urls_df['link'].loc[idx]
            # Add filename column to df
            urls_df['filename'].loc[idx] = global_index
            # Get image
            response = requests.get(url, stream=True)
            # Save image to folder
            save_image_to_file(response, dirname, global_index) # save it to folder
            # Mark that url as already downloaded
            urls_df['downloaded'].loc[idx] = 1
            
            del response
        # Retrun records of what was downloaded
        return urls_df
        
        # # Save csv with species urls
        # if replace_urls_csv:
        #     urls_df.to_csv(os.path.join(dirname, 'species_df.csv'))
    
    def request_n_download(self, species_code, replace = False):
        """
        Sends a request to get pic links and download all pics from species in a loop.
        
        Parameters
        ----------
        """
        self.current_save_dir = os.path.join(self.save_dir, str(species_code))
        # Only run if directory doesnt' exist or overwrite is on
        if replace | (not os.path.exists(self.current_save_dir)):
            # Create directory to save pictures and data
            if not os.path.exists(self.current_save_dir):
                os.mkdir(self.current_save_dir)
            
            #-------------------------------
            # Loop parameters
            
            # Set a limit based on species df
            max_pics = self.spc_df['pic'][self.spc_df['code'] == int(species_code)].item()
            
            # Create empty df
            df_s = pd.DataFrame(columns = ['id', 'local', 'idMunicipio', 'coms', 'likes', 'vis', 'grande', 'link', 'downloaded', 'filename'])
            
            # Keep track of how many pictures where downloaded for file names and printing
            pic_start_idx = 0
            page = 1
            
            while len(df_s) < max_pics:
                print('Sending request for page {0}...'.format(page))
                # Request pic URLs and process it
                res = self.http_request(species_code, page)
                df_si = self.process_request(res)
                
                # Stop if page is empty
                if df_si is None:
                    print('Page {0} is empty! Stopping...'.format(page))
                    break
                else:
                    print('Page {0} URLs loaded'.format(page))
                    
                # Download pictures and replace df with anotated version
                df_si_results = self.download_images(self.current_save_dir, df_si, max_pics, pic_start_idx)
                
                # Create all records df
                df_s = df_s.append(df_si_results)
                
                # Save df as a backup
                df_s.to_csv(os.path.join(self.current_save_dir, 'pics_df.csv'))
                
                # Loop parameters
                pic_start_idx = pic_start_idx + len(df_si)
                page = page + 1
                
                # Wait a random interval before sentind new request
                sleep(round(random.uniform(.3, 3),3))
            
            # Anotate all species DF to keep track of what as been downloaded
            self.spc_df['downloaded'].loc[self.spc_df['code'] == species_code] = len(df_s)
            
            # Replace existing file with anotaded version
            self.spc_df.to_csv(os.path.join(self.save_dir, 'all_species_progress.csv'), index = False)
        
        else:
            print('Species already downloaded. Skipping {0}...'.format(species_code))
        
    def download_species_images(self, codes, overwrite = False):
        # print('Species already downloaded. Skipping {0}...'.format(species_code))
        pass



#--------------------------------------------------------------------------------
# Run BirdCrawler!

# if __name__ == "__main__":
with open('../data/scraping/get_request.txt', 'r') as file:
    REQUEST_URL = file.read()


# crawl = BirdCrawler(REQUEST_URL, create_progress_df = True)
crawl = BirdCrawler(REQUEST_URL)

# crawl.request_n_download(10004, replace = True)
