#basic data information
url = 'https://www.liquidation.com/c/sony.html'
Margin = .2
ShippingCost = 40.25
BuyerPremium = 1.11

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
from bs4 import BeautifulSoup
import webscrapeTools
import csv
import requests


class Listing:
    def __init__(self, title, link, date, manifest, minbid, totalCost, maxbid, gross, net):
        self.title = title
        self.link = link
        self.date = date
        self.manifest = manifest
        self.minbid = minbid
        self.totalCost = totalCost
        self.maxbid = maxbid
        self.gross = gross
        self.net = net

#url = 'https://www.liquidation.com/c/sony.html'

# Configure Selenium to use headless mode
options = Options()
options.add_argument("--headless")

# Set up the WebDriver
driver = webdriver.Chrome()

def listingLinks(url):
    """returns links of Liqudation listings found on given url"""

    auctionLinks = []
    
    # Open the website
    driver.get(url)

    # Wait for JavaScript to load content (optional wait strategy)
    #driver.implicitly_wait(10)

    # Extract HTML content
    page_source = driver.page_source

    for element in driver.find_elements(By.CLASS_NAME, 'thumbnail'):
        try:
            if element.find_element(By.CLASS_NAME,"closing").text == "CLOSED":
                pass
            else:
                auctionLinks.append(element.find_element(By.CLASS_NAME, "desc").get_attribute('href'))
        except:
            continue

    #for element in driver.find_elements(By.CLASS_NAME, "desc"):
        #auctionLinks.append(element.get_attribute("href"))
    
    return set(auctionLinks)

def manifestRead(manifestlink):
    """Takes in the manifest link of a listing and uses all of the functions from previous manifest reader to return gross profit and costs"""
    

    driver.get(manifestlink)
    
    manifestHTML = BeautifulSoup(driver.page_source, "html.parser")

    table = manifestHTML.find("table")

    # Extract table headers
    headers = [th.text.strip() for th in table.find_all("th")]

    # Extract table rows
    data = []
    for row in table.find_all("tr")[1:]:  # Skip the header row
        cells = row.find_all("td")
        row_data = [cell.text.strip() for cell in cells]
        if row_data:
            data.append(row_data)

    manifest = pd.DataFrame(data)

    #removes bottom row of totals from dataframe
    manifest = manifest.drop(manifest.index[-1])

    soldPrices = []
    allSold = []
    allShipping = []


    report = pd.DataFrame(columns = ['Item', 'Quantity', 'Price', 'Shipping', 'Net'])
    n = 0
    for item in manifest.loc[:,0]:
        #Goes through each item in list and finds quantity, average price, and average shipping, calucating net and adding data to find total value

        quantity = float(manifest.loc[n,1])

        if item in priceData:
            
            avgSold = priceData[item][0]
            avgShip = priceData[item][1]
            print("Skipped eBay research on item" + item)
        else:

            link = f'https://www.ebay.com/sch/i.html?_nkw={item.replace(" ","+")}&LH_Sold=1&LH_Complete=1&rt=nc&LH_ItemCondition=3000'

            soldListings = BeautifulSoup(requests.get(link).text,"html.parser")
            avgSold = float(main.averageSold(soldListings)*quantity)
        
            avgShip, freeShip = main.avgShipping(soldListings)
            priceData[item] = [avgSold, avgShip]
            print("Did not skip eBay research on item" + item)

        allSold.append(avgSold)
        allShipping.append(avgShip)
        
        net = (avgSold*.92) - avgShip
        itemInfo = {'Item': item, 'Quantity': quantity, 'Price': avgSold, 'Shipping': avgShip, 'Net': round(net,2)}
        report.loc[len(report)] = itemInfo

        n = n + 1

    totalFees = round(sum(allSold)*(.08), 2)
    grossProfit = round(sum(allSold) - totalFees - sum(allShipping), 2)
    
    return grossProfit, report




#currently errors on listings with 5 minutes left in the auction as page html changes, can fix by just skipping these in the auction links function
def listScrape(auctionLinks):
    """Creates an object for each listing containing all information about the listing, returning all data in a list of objects"""
    allListings = []

    n = 0

    for listing in auctionLinks:

        print("Reading Data from this link:" + listing)

        driver.get(listing)
        #driver.implicitly_wait(10)
        title = driver.find_element(By.XPATH, '//*[@id="auctionData"]/h1/b').text
        date = driver.find_element(By.XPATH, '//*[@id="auctionData"]/div[2]/div[2]/b').text
        if date[:1] == "$":
            next
        manifestLink = driver.find_element(By.XPATH, '//*[@id="auctionData"]/ul/li[1]/a[1]').get_attribute('href')
        minbid = driver.find_element(By.XPATH, "//*[@id='auctionData']/div[3]/div[2]/b").text

        grossProfit, manifestReport = manifestRead(manifestLink)

        maxbid, totalCost = maxBid(grossProfit, Margin, ShippingCost, BuyerPremium)

        allListings.append(Listing(title = title, link = listing, date = date, manifest = manifestReport, minbid = minbid, totalCost= totalCost, maxbid= maxbid, gross = grossProfit, net = grossProfit-totalCost))
    
    return allListings

def maxBid(gross, margin, shippingCost, premium):
    """returns a total cost and max bid number"""
    maxbid = ((gross*(1-margin))-shippingCost)/premium
    totalCost = maxbid*premium + shippingCost

    return round(maxbid, 2), round(totalCost, 2)

        


#manifestRead('https://www.liquidation.com/aucimg/19707/m19707411.html')

#Dictionary of other price data stored as {Item Name: [avg sold price, avg shipping]}
priceData = {}

auctionData = listScrape(listingLinks(url))
df = pd.DataFrame(Listing.__dict__ for Listing in auctionData)
print(df)

driver.quit()
