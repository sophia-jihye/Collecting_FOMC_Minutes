import time, os, re, pickle, argparse
from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import datetime
from glob import glob
from tqdm import tqdm
tqdm.pandas()
import pandas as pd
import requests

parser = argparse.ArgumentParser()
parser.add_argument('--start_mmddyyyy', type=str, default="01/01/1990")
parser.add_argument('--end_mmddyyyy', type=str, default="01/25/2023")
args = parser.parse_args()

start_mmddyyyy = args.start_mmddyyyy
end_mmddyyyy = args.end_mmddyyyy

selenium_filepath = "C:\GIT\SELENIUM_DRIVERS\chromedriver_win32\chromedriver.exe"
save_root_dir = './Minutes'

url = "https://www.federalreserve.gov/monetarypolicy/materials/"

def prepare_resources_for_scraping(selenium_filepath, url, start_mmddyyyy, end_mmddyyyy, scrape_target='minutes'):
    driver = webdriver.Chrome(selenium_filepath)
    driver.get(url)
    time.sleep(5)
    
    # set start date
    start_date = driver.find_element_by_name("startmodel")
    start_date.clear()
    start_date.send_keys(start_mmddyyyy)

    # set end date
    end_date = driver.find_element_by_name("endmodel")
    end_date.clear()
    end_date.send_keys(end_mmddyyyy)

    # select items
    if scrape_target == 'minutes':
        xpath_strings = "//label/input[contains(..,'Minutes (1993-Present)')]"
    elif scrape_target == 'statements':
        xpath_strings = "//label/input[contains(..,'Policy Statements')]"
    statement_checkbox = driver.find_element_by_xpath(xpath_strings)
    statement_checkbox.click()

    # apply filter
    submit = driver.find_element_by_css_selector(".btn.btn-primary")
    submit.click()
    
    # get the page control row
    pagination = driver.find_element_by_class_name('pagination')

    # go to the last page to find the largest page number
    last_page = pagination.find_element_by_link_text('Last')
    last_page.click()
    pages = pagination.text.split('\n')
    largest_page = int(pages[-3])
    
    return driver, pagination, largest_page

def scrape_URLs_and_meeting_dates_and_document_dates(driver, pagination, largest_page, scrape_target='minutes'):
    statement_url_list, meeting_date_list, document_date_list = [], [], []
    # go back to first page and start the loop
    first_page = pagination.find_element_by_link_text('First')
    first_page.click()
    next_page = pagination.find_element_by_link_text('Next')
    for i in range(largest_page):
        # now to get the items inside
        main = driver.find_element_by_css_selector(".panel.panel-default") # get the app panel
        material_types = main.find_elements_by_css_selector(".fomc-meeting__month.col-xs-5.col-sm-3.col-md-4") # get the 2nd col
        material_types = [element.text for element in material_types] # to get the words
        material_links = main.find_elements_by_css_selector(".fomc-meeting__month.col-xs-5.col-sm-3.col-md-2") # get the 3rd col
        
        meeting_dates = main.find_elements_by_css_selector(".fomc-meeting__month.col-xs-5.col-sm-3.col-md-3 > strong")
        meeting_dates = [element.text for element in meeting_dates] # to get the words
        meeting_dates = meeting_dates[2:] # First two items correspond to table headings (i.e.,"Meeting date", "Document date")
        
        document_dates = main.find_elements_by_css_selector(".fomc-meeting__month.col-xs-5.col-sm-3.col-md-3 > em")
        document_dates = [element.text for element in document_dates] # to get the words
        
        # add url to statement_url_list if it is a target item
        if scrape_target == 'minutes':
            target_strings = 'Minutes'
            html_elements = []
            for element in material_links:
                try: html_elements.append(element.find_element_by_link_text('HTML'))
                except: continue
        elif scrape_target == 'statements':
            target_strings = 'Statement'
            html_elements = [element.find_element_by_link_text('HTML') for element in material_links] # get the html ones
        
        meeting_date_list.extend([meeting_dates[i] for i, j in enumerate(material_types) if j==target_strings])
        statement_url_list.extend([html_elements[i].get_attribute('href') for i, j in enumerate(material_types) if j==target_strings])
        document_date_list.extend([document_dates[i] for i, j in enumerate(material_types) if j==target_strings])
        
        next_page.click()
    print('Number of URLs: {}'.format(len(statement_url_list)))
    
    return statement_url_list, meeting_date_list, document_date_list

def get_text_for_a_statement_from_201201_to_202209(soup):
    return soup.find('div', class_ = 'col-xs-12 col-sm-8 col-md-9').text.strip()

def get_text_for_a_statement_from_200710_to_201112(soup):
    return soup.find('div', id="leftText").text.strip()

def get_text_for_a_statement_from_199601_to_200709(soup):
    return '\n'.join([item.text.strip() for item in soup.select('table td')])

def get_text_for_a_statement_from_199401_to_199512(soup):
    return soup.find('div', id="content").text.strip()

doublespace_pattern = re.compile('\s+')
def remove_doublespaces(document):
    return doublespace_pattern.sub(' ', document).strip()

if __name__ == '__main__':
    
    driver, pagination, largest_page = prepare_resources_for_scraping(selenium_filepath, url, start_mmddyyyy, end_mmddyyyy)
    statement_url_list, meeting_date_list, document_date_list = scrape_URLs_and_meeting_dates_and_document_dates(driver, pagination, largest_page)
        
    doc_count = 0
    error_list = []
    for statement_url, meeting_date, document_date in tqdm(zip(statement_url_list, meeting_date_list, document_date_list)):
        
        # Scrape statements
        statement_resp = requests.get(statement_url)
        statement_soup = BeautifulSoup(statement_resp.content, 'lxml')

        document_date_yyyymmdd = datetime.strftime(datetime.strptime(document_date, "%B %d, %Y"), "%Y%m%d")
        yearmonth = int(document_date_yyyymmdd[:6])
        try:
            if yearmonth >= 201201:
                doc = get_text_for_a_statement_from_201201_to_202209(statement_soup)
            elif yearmonth >= 200710:
                doc = get_text_for_a_statement_from_200710_to_201112(statement_soup)
            elif yearmonth >= 199601:
                doc = get_text_for_a_statement_from_199601_to_200709(statement_soup)    
            else:
                doc = get_text_for_a_statement_from_199401_to_199512(statement_soup)
        except:
            error_list.append((statement_url, meeting_date, document_date))
            continue
        
        # Clean
        doc = remove_doublespaces(doc)
        
        # Save data
        save_dir = os.path.join(save_root_dir, 'raw', document_date_yyyymmdd[:4])
        if not os.path.exists(save_dir): os.makedirs(save_dir)
        save_filepath = os.path.join(save_dir, '{}.txt'.format(document_date_yyyymmdd))
        with open(save_filepath, "w", encoding='utf-8-sig') as file:
            file.write("MEETING_DATE: {}\n".format(meeting_date))
            file.write(doc)
            doc_count += 1 
            
    save_dir = '{}/{}'.format(save_root_dir, 'raw')
    print('Saved {} unique documents under {}'.format(len(glob('{}/*/*.txt'.format(save_dir))), save_dir)) 
    
    # Save errors
    if len(error_list) > 0:
        save_filepath = os.path.join(save_root_dir, 'raw', 'errors.csv')
        pd.DataFrame(error_list, columns=['url', 'meeting_date', 'document_date']).to_csv(save_filepath, index=False)
        print('Created {}'.format(save_filepath))