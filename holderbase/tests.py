import os
import time

from pandas import DataFrame

from django.conf import settings
from django.test import TestCase
from django.utils.dateparse import parse_datetime

from .processors import Dataset




class DatasetProcessorTest(TestCase):

    def setUp(self):
        self.name = os.path.join(settings.FIXTURE_ROOT, 'e0e126cb2902fade6d38fe15a9b0ab52.csv')
        self.file = open(self.name)
        self.dataset = Dataset(self.file, name=os.path.join(settings.FIXTURE_ROOT, 'e0e126cb2902fade6d38fe15a9b0ab52.csv'))
        self.file.close()
        self.data = self.dataset.read_data()
        self.header = [e.lower() for e in self.data[0]]
        self.df = self.dataset.get_data_frame(self.data)


    def test_dataset_methods(self):
        self.assertEqual(self.dataset.name, os.path.join(settings.FIXTURE_ROOT, 'e0e126cb2902fade6d38fe15a9b0ab52.csv'))
        self.assertEqual(self.dataset.ext, ".csv")
        self.assertEqual(self.dataset.size, 598)

    def test_dataset_read_data(self):
        self.assertEqual(self.data, [
            ['Record type', 'Timestamp', 'LEI', 'Account', 'ISIN', 'Nom/Unit', 'Amount', 'Currency', 'Country', 'Type', 'Name', 'ID'], 
            ['100', '1504175027', 'MMYX0N4ZEZ13Z4XCG897', '', '', '', '', '', 'BE', 'Custodian', 'The Bank of New York Mellon SA/NV', ''], 
            ['200', '', '549300OZ46BRLZ8Y6F65', '12345', 'XS0342489316', 'Nominal', '49,200,000', 'USD', '', '', 'Euroclear Bank SA/NV', ''], 
            ['300', '', '549300ZFEEJ2IP5VME73', '4567G89', 'XS0342489316', 'Nominal', '40,000,000', 'USD', 'US', '', 'State Street Corporation', ''], 
            ['350', '', '', '8529FFT', 'XS0342489316', 'Nominal', '1,200,000', 'USD', 'IT', '', 'Mario Milano', '521458-IL8966'], 
            ['400', '', 'MMYX0N4ZEZ13Z4XCG897', '9999TTT', 'XS0342489316', 'Nominal', '8,000,000', 'USD', 'BE', '', 'The Bank of New York Mellon SA/NV', '']
        ])
        self.assertEqual(self.dataset.check_header(self.data), True)

    def test_dataset_dataframe(self):
        self.assertEqual(list(self.df.columns.values), self.header)
        self.assertEqual(self.dataset.get_timestamp(self.df), parse_datetime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(1504175027))))

    def test_dataset_get_sender_and_holdings(self):
        self.assertEqual(self.dataset.get_sender_row(self.df), {'currency': '', 'country': 'BE', 'account': '', 'record type': '100', 'type': 'Custodian', 'id': '', 'isin': '', 'amount': '', 'nom/unit': '', 'name': 'The Bank of New York Mellon SA/NV', 'lei': 'MMYX0N4ZEZ13Z4XCG897', 'timestamp': '1504175027'})
        self.assertEqual(self.dataset.get_holdings_list(self.df), [
            {'currency': 'USD', 'country': '', 'account': '12345', 'record type': '200', 'type': '', 'id': '', 'isin': 'XS0342489316', 'amount': '49,200,000', 'nom/unit': 'Nominal', 'name': 'Euroclear Bank SA/NV', 'lei': '549300OZ46BRLZ8Y6F65', 'timestamp': ''}, 
            {'currency': 'USD', 'country': 'US', 'account': '4567G89', 'record type': '300', 'type': '', 'id': '', 'isin': 'XS0342489316', 'amount': '40,000,000', 'nom/unit': 'Nominal', 'name': 'State Street Corporation', 'lei': '549300ZFEEJ2IP5VME73', 'timestamp': ''}, 
            {'currency': 'USD', 'country': 'IT', 'account': '8529FFT', 'record type': '350', 'type': '', 'id': '521458-IL8966', 'isin': 'XS0342489316', 'amount': '1,200,000', 'nom/unit': 'Nominal', 'name': 'Mario Milano', 'lei': '', 'timestamp': ''}, 
            {'currency': 'USD', 'country': 'BE', 'account': '9999TTT', 'record type': '400', 'type': '', 'id': '', 'isin': 'XS0342489316', 'amount': '8,000,000', 'nom/unit': 'Nominal', 'name': 'The Bank of New York Mellon SA/NV', 'lei': 'MMYX0N4ZEZ13Z4XCG897', 'timestamp': ''}
        ]
)


    # def test_csv_read_get_100_record(self):
    #     self.assertEqual(read_data(self.data)[1][0], '100')

    # def test_csv_read_data_timestamp(self):
    #     self.assertEqual(read_data(self.data)[1][1], '1504175027')

    # def test_get_sender_from_csv(self):
    #     ext = '.csv'
    #     parsed_data = [
    #         ['record type', 'timestamp', 'lei', 'account', 'isin', 'nom/unit', 'amount', 'currency', 'country', 'type', 'name', 'id'], 
    #         ['100', '1504175027', 'mmyx0n4zez13z4xcg897', '', '', '', '', '', 'be', 'custodian', 'the bank of new york mellon sa/nv', ''], 
    #         ['200', '', '549300oz46brlz8y6f65', '12345', 'xs0342489316', 'nominal', '49,200,000', 'usd', '', '', 'euroclear bank sa/nv', ''], 
    #         ['300', '', '549300zfeej2ip5vme73', '4567g89', 'xs0342489316', 'nominal', '40,000,000', 'usd', 'us', '', 'state street corporation', ''], 
    #         ['350', '', '', '8529fft', 'xs0342489316', 'nominal', '1,200,000', 'usd', 'it', '', 'mario milano', '521458-il8966'], 
    #         ['400', '', 'mmyx0n4zez13z4xcg897', '9999ttt', 'xs0342489316', 'nominal', '8,000,000', 'usd', 'be', '', 'the bank of new york mellon sa/nv', '']
    #     ]
    #     self.assertEqual(get_sender_row(parsed_data, ext), True)



