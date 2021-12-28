import requests
from dotenv.main import dotenv_values
import csv

class GetTickers:
    def __init__(self, exchange):
        self.exchange = exchange.upper()
        self.token = dotenv_values('.env')['API_TOKEN']
    
    def getTickers(self):
        download = requests.get(f'https://eodhistoricaldata.com/api/exchange-symbol-list/{self.exchange}?api_token={self.token}')
        content = download.content.decode('utf-8')
        cr = csv.reader(content.splitlines(), delimiter=',')
        my_list = list(cr)
        with open(f'{self.exchange}.txt', 'w') as myfile:
            for line in my_list:
                if 'Common Stock' in line and line[6] != '':
                    myfile.write(f'{line[0]},{line[3]},{line[4]}\n')
                    