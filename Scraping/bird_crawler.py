
# CSV for all species
# CSV for all pictures of each specie


# TODO
#   - Symlink to datafolder
#   - Loop over species
#   - Add random delays?
#   - Hide IP?
#   CODE REORGANIZATION AND ABSTRACTION
#   DOCKER TO FOLDER LINK

import os
import time
import logging
import pandas as pd
import requests
import shutil

from pyvirtualdisplay import Display
from selenium import webdriver

class BirdCrawler():
    """
    This class creates a (gecko) webdriver to navigate and scrape a target webpage.
    It takes as inputs a target url and a csv file containing bird species codes, that 
    can be conbined with base url to access each species page.
    
    For each bird species it provides methods to scrow-down until the end of the page
    to load all avaialbel picture tumbnails, record each picture url and download them 
    all. 
    
    Attributes
    ----------
    
    Methods
    -------
    """
    
    def __init__(self,
                 base_url,
                 species_csv_path):
        """
        Parameters
        ----------
        base_url : A string containing a URL that can be cocatenated with species code
        to load a sepecies page 
        
        species_csv_path : Path to csv file containg species codes and number of pics
        """
        
        self.base_url = base_url        
        self.spc_csv = pd.read_csv(species_csv_path)
        
        # Set up logging
        # logging.basicConfig(filename='app.log', 
        #                     filemode='w', 
        #                     format='%(name)s - %(levelname)s - %(message)s')
        # logging.warning('This will get logged to a file')
        # logging.getLogger().addHandler(logging.StreamHandler())
        logging.getLogger().setLevel(logging.INFO)
        logging.info('Crawler started')
    
    def start_driver(self):
        # Driver and other scrapping settings
        self.display = Display(visible=0, size=(800, 600))
        self.display.start()
        logging.info('Initialized virtual display..')
        
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference('browser.download.folderList', 2)
        firefox_profile.set_preference('browser.download.manager.showWhenStarting', False)
        firefox_profile.set_preference('browser.download.dir', os.getcwd())
        firefox_profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/csv')
        
        logging.info('Prepared firefox profile..')
        
        self.driver = webdriver.Firefox(firefox_profile=firefox_profile)
        logging.info('Initialized firefox browser..')
        
        # return self.driver
    
    def get_base_url(self):
        self.driver.get(self.base_url)
        logging.info('Accessed %s ..', self.base_url)
        logging.info('Page title: %s', self.driver.title)
    
    def load_all_pics(self, species_code):
        
        # species_code = 10001
        self.current_page = self.base_url + str(species_code)
        
        self.driver.get(self.current_page)
        
        # Function to store url attribute of each image into list
        def get_urls(img_list):
            image_urls = []
            for image in img_list:
                url = image.get_attribute('src')
                # Filter only bird pictures out of all the images in the page
                if 's3.amazonaws.' in url:
                    image_urls.append(url)
            return image_urls
        
        # TEMPORARY AD HOC NUMBER OF PICTURES TO TEST SET UP
        n_pictures = 10
        
        # Scroll down until at least the number of pictures in the sheet are loaded
        # and store all image URLs
        while True:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Wait to load page
            time.sleep(2)
            # Compute new image list
            images = self.driver.find_elements_by_tag_name('img')
            url_list = get_urls(images)
            # Create data frame and remove song recordins images
            urls_df = pd.DataFrame(url_list, columns= ['urls'])
            urls_df = urls_df[~urls_df['urls'].str.contains('recordings')]
            
            # Add a dummy if image was downloaded for future reference. For now,
            # when aquiring the list of urls, no image was downloaded
            urls_df['downloaded'] = 0
            
            # Print number of urls stored
            n_urls = len(urls_df.index)
            print('Loading {0} of {total} images'.format(n_urls, total=n_pictures))
            # Stop if number of images the same as number of pictures 
            if n_urls >= n_pictures:
                break
        # Store urls df into attribute
        self.urls_df = urls_df
    
    def download_images(dirname, links_df, column = 'urls'):
        pass
    
    def stop_driver(self):
        self.driver.quit()
        self.display.stop()
        

#-----------------------------------------------
# Load URL from external file
with open('url.txt', 'r') as file:
    BASE_URL = file.read()

crawl = BirdCrawler(BASE_URL, 'Data/all_species.csv')

crawl.start_driver()
# # crawl.get_base_url()
crawl.load_all_pics(10001)

crawl.stop_driver()