import requests
from bs4 import BeautifulSoup
import csv
import html
import re

def averageSold(website):
        """organizes sold prices into a list and returns average"""
        soldPrices = []
        for i in website.find_all("span", class_="s-item__price"):
            price = i.find('span', class_="POSITIVE")
            if price == None:
                soldPrices.append(0)
            
            else:
                priceText = price.get_text()
                if priceText == "See price":
                    next
                else:
                    priceText = priceText.replace(",", "")
                    soldPrices.append(float(priceText[1:]))
        if len(soldPrices) == 0:
            return "No Sold Listings Found"
        else:
            avgSold = round(sum(soldPrices)/len(soldPrices), 2)
            return avgSold
        
def avgShipping(website):
    """Finds average shipping prices on sold listings"""
    shippingData = []
    shippingPrices = []
    n = 0

    for i in website.find_all("span", class_="s-item__shipping s-item__logisticsCost"):
        shipping = i.get_text()
        shippingData.append(shipping)
        if shipping[0] == "+":
            shippingPrice = re.findall(r"[-+]?\d*\.\d+", shipping)
            shippingPrices.append(float(shippingPrice[0]))
        elif shipping == "Free shipping":
            n = n + 1

    if len(shippingData) == 0:
        return 0, "No Data"
    elif len(shippingPrices) == 0:
        return 0, 1
    else:
        avgShipping = round(sum(shippingPrices)/len(shippingPrices), 2)
        totalFree = round(n/len(shippingData), 2)
        return avgShipping, totalFree

def conditionType():
    print("1 = New")
    print("2 = Open Box")
    print("3 = Used")
    condition = int(input("Enter Condition: "))

    if condition == 1:
        return 1000
    elif condition == 2:
        return 1500
    else:
        return 3000

def costTotals():
    """opens Auction Cost csv and saves values and total cost"""
    auctionCosts = open('Auction Lot Costs.csv', 'r')

    costs = []
    for i in csv.reader(auctionCosts):
        costs.append(float(i[1]))
    

    totalCost = round(((costs[0]*costs[2]) + costs[1]), 2)
    return totalCost
    



def main():

    """reads and opens all csv files invloved"""
    manifest = open('manifest.csv', 'r')
    report = open('manifestReport.csv', 'w', newline='')



    itemList = []
    itemQuantity = []
    
    allSold = []
    allShipping = []


    for i in csv.reader(manifest):
        if i[0] == "Description" or i[0] == " " or i[0] == "" or i[0] == "Product":
            """won't be added to the list"""
        else:
            itemList.append(i[0])
            itemQuantity.append(i[2])
    


    csv.writer(report).writerow(["Item", "Quantity", "Avg Sold","avg Shipping", "% Free Shipping", "Link"])

    conNum = conditionType()
    totalCost = costTotals()

    n = 0
    for item in itemList:
        
        link = f'https://www.ebay.com/sch/i.html?_nkw={item.replace(" ","+")}&LH_Sold=1&LH_Complete=1&rt=nc&LH_ItemCondition={conNum}'

        soldListings = BeautifulSoup(requests.get(link).text,"html.parser")

        avgSold = float(averageSold(soldListings)) * float(itemQuantity[n])
        allSold.append(avgSold)

        avgShip, freeShip = avgShipping(soldListings)
        allShipping.append(avgShip)

        csv.writer(report).writerow([item, itemQuantity[n], avgSold,avgShip, freeShip, link])
        n = n + 1
    print("Done")

    totalFees = round(sum(allSold)*(.1325), 2)
    grossProfit = round(sum(allSold) - totalFees - sum(allShipping), 2)

    csv.writer(report).writerow(["Total", round(sum(allSold), 2), round(sum(allShipping), 2)])
    csv.writer(report).writerow(["Total Fees:", totalFees])
    csv.writer(report).writerow(["Est. Gross Profit:", grossProfit])

    print("Total Cost:", totalCost)
    print("Gross Pofit:", grossProfit)
    print("Net Profit:", grossProfit - totalCost)

        
main()