import csv
import datetime
import decimal
import hashlib
import json
import pandas
import time

from django.conf import settings
from django.core.files import File
from django.utils.dateparse import parse_datetime

from .constants import FileExtension
from .models import Party, Security, Holding


def hash_file(path):
    """ Calculates the MD5 digest of the file. Currently assumes small file. 
    Check ref: http://pythoncentral.io/hashing-files-with-python/ for managing bigger files.
    """
    hasher = hashlib.md5()
    with open(path, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    return hasher.hexdigest()


class Dataset(File):

    def __init__(self, file, name):
        self.file = file
        self.name = name
        self.ext, self.ext_verified = self.get_file_extension()
        self.hash = self.get_hash_from_name()
        self.header = ['record type' ,'timestamp','lei' ,'account' ,'isin' ,'nom/unit' ,'amount' ,'currency' ,'country' ,'type' ,'name' ,'id', 'sector/industry']

    def clean_row(self, row):
        return [e.strip() for e in row]

    def clean_data(self, data):
        return [self.clean_row(row) for row in data]

    def read_data(self):
        """
        Parse data. Calls on self.clean_data() which in turn calls slef.clean_row().
        Returns data cleaned from blanks and capital letters.
        """
        with open(self.name, 'r') as f:
            parsed_data = [row for row in csv.reader(f.read().splitlines())]
        return self.clean_data(parsed_data)

    def get_file_extension(self):
        """
        Ensures file extension is accepted. (.csv) 
        Returns a tuple with True or False and the extension itself.
        """
        ext = self.name.split('.')[-1]
        if "." + ext in FileExtension.dataset():
            return "." + ext, True
        else:
            return None, False

    def get_hash_from_name(self):
        """
        Get hash from file name transmited upon creation.
        """
        return self.name.split('/')[-1].split('.')[0]

    # @classmethod ?
    # change self to cls
    def check_header(self, cleaned_data):
        """
        Check if all columns are present in file. Expects the header to be the first row in file.
        """
        header = [e.lower() for e in cleaned_data[0]]
        return set(header) == set(self.header)

    def get_data_frame(self, cleaned_data):
        """
        Get dataframe object from data.
        Expects the header to be the first row in file.
        """
        header = [e.lower() for e in cleaned_data[0]]
        only_data = cleaned_data[1:]
        df = pandas.DataFrame(only_data)
        df.columns = header
        return df

    def get_timestamp(self, df, record_type=settings.SENDER_RECORD_TYPE):
        """
        Returns a datetime object from epoch time.
        TODO: accept other time representation, check timezone acceptance.
        """
        return parse_datetime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(df.loc[df['record type']==record_type]['timestamp'][0]))))
        

    def get_holdings(self, df, record_types=settings.HOLDING_RECORD_TYPES):
        return df[df['record type'].isin(record_types)]

    def get_row_dict_from_tuple(self, row_tuple, header):
        row = {}
        for col in header:
            row[col] = row_tuple[header.index(col)+1]
        return row

    def get_securities(self, df, record_type=settings.SECURITY_RECORD_TYPE):
        return df.loc[df['record type']==record_type]

    def get_sender(self, df, record_type=settings.SENDER_RECORD_TYPE):
        sender = df.loc[df['record type']==record_type]
        return sender

    def get_sender_row(self, df):
        sender = self.get_sender(df)
        header = list(sender.columns.values)
        row = {}
        for col in header:
            row[col] = sender[col][0]
        return row

    def get_securities_list(self, df):
        securities = self.get_securities(df)
        header = list(securities.columns.values)
        securities_list = []
        for row in securities.itertuples():
            securities_list.append(self.get_row_dict_from_tuple(row, header))
        return securities_list

    def get_issuers_list(self, df):
        issuers = df.loc[df['record type']=='900']
        header = list(issuers.columns.values)
        issuers_list = []
        for row in issuers.itertuples():
            issuers_list.append(self.get_row_dict_from_tuple(row, header))
        return issuers_list

    def get_holdings_list(self, df):
        holdings = self.get_holdings(df)
        header = list(holdings.columns.values)
        holdings_list = []
        for row in holdings.itertuples():
            holdings_list.append(self.get_row_dict_from_tuple(row, header))
        return holdings_list



def get_file_extension(filename):
    """
    Ensures file extension is accepted. 
    Returns a tuple with True or False and the extension itself.
    """
    ext = filename.split('.')[-1]
    if "." + ext in FileExtension.dataset():
        return "." + ext, True
    else:
        return None, False








def translate_type(holder_type):
    """
    Ensures type mentionned in file corresponds to type expected in database.
    """
    if holder_type == 'custodian':
        return 'CUS'
    elif holder_type == 'issuer':
        return 'ISS'
    elif holder_type == 'depository' or 'csd':
        return 'CSD'
    else:
        return None

def create_or_update_sender(row, hash):
    sender, created = Party.objects.update_or_create(
        lei__exact = row['lei'],
        defaults = {
            'lei': row['lei'], 
            "name":row['name'], 
            "holder_role":translate_type(row['type']), 
            "country":row['country'], 
            "sector_industry":row['sector/industry'],
            "last_file_hash":hash}
    )
    return sender

def create_or_update_holdings(sender, timestamp, holdings_list, hash):
    decimal.setcontext(decimal.ExtendedContext)
    for row in holdings_list:
        security, created = Security.objects.update_or_create(
            isin__exact=row['isin'],
            defaults = {'isin': row['isin']}
        )
        party, created = Party.objects.update_or_create(
            lei__exact = row['lei'],
            name__exact = row['name'],
            defaults = {
                'lei': row['lei'], 
                "name":row['name'], 
                "country":row['country'],
                "original_id":row['id']
            }
        )

        holding, created = Holding.objects.update_or_create(
            party_from__exact=sender, 
            party_to__exact=party,
            account_ref__exact=row['account'],
            security__exact=security,
            defaults = {
                "party_from":sender,
                "party_to": party,
                "security": security,
                "account_ref": row['account'],
                "nominal_unit": row['nom/unit'],
                "amount": decimal.Decimal("".join(row['amount'].split(','))),
                "currency": row['currency'],
                "relation_type":row['record type'],
                "updated":timestamp,
                "file_hash":hash
            }
        )
        if created:
            holding.file_hash = hash
            holding.created = timestamp
            holding.save()
    return holdings_list

def create_or_update_securities(sender, timestamp, securities_list, hash):
    decimal.setcontext(decimal.ExtendedContext)
    for row in securities_list:
        party, created = Party.objects.update_or_create(
            lei__exact = row['lei'],
            name__exact = row['name'],
            defaults = {
                'lei': row['lei'], 
                "name":row['name'],
                'country':row['country']
            }
        )
        security, created = Security.objects.update_or_create(
            isin__exact=row['isin'],
            defaults = {
                'isin': row['isin'],
                'issuer': party,
                "nominal_unit": row['nom/unit'],
                "amount": decimal.Decimal("".join(row['amount'].split(','))),
                "currency": row['currency']
                }
        )
        holding, created = Holding.objects.update_or_create(
            party_from__exact=sender, 
            party_to__exact=party,
            account_ref__exact=row['account'],
            security__exact=security,
            defaults = {
                "party_from":sender,
                "party_to": party,
                "security": security,
                "account_ref": row['account'],
                "nominal_unit": row['nom/unit'],
                "amount": decimal.Decimal("".join(row['amount'].split(','))),
                "currency": row['currency'],
                "relation_type":row['record type'],
                "updated":timestamp,
                "file_hash":hash
            }
        )
        if created:
            holding.file_hash = hash
            holding.created = timestamp
            holding.save()

def create_or_update_issuers(issuers_list):
    for row in issuers_list:
        issuer, created = Party.objects.update_or_create(
            lei__exact = row['lei'],
            name__exact = row['name'],
            defaults = {
                'lei': row['lei'], 
                "name":row['name'], 
                "holder_role":'ISS', 
                "country":row['country'], 
                "sector_industry":row['sector/industry'], 
            }
        )

def file_contains_sender_info(path):
    """
    Check if the file contains a 100 record type.
    """
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f, delimiter=",")
        reader.fieldnames = [name.strip(' ').lower() for name in reader.fieldnames]
        for row in reader:
            if row['record type'] == '100':
                return True
    return False
    




