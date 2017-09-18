import decimal
import json
import math
import statistics

from pandas import DataFrame

from django.core import serializers
from django.db import models
from django.utils import timezone

from django_countries.fields import CountryField

#TODO define validator for LEI field and add validators=[validate_lei] to related field
# Docs: https://docs.djangoproject.com/fr/1.11/ref/validators/
# LEI Schema: https://en.wikipedia.org/wiki/Legal_Entity_Identifier
# ISIN Schema: https://en.wikipedia.org/wiki/International_Securities_Identification_Number

# from django.core.exceptions import ValidationError

# def validate_lei(value):
#     if value not correct:
#         # check
#         raise ValidationError(
#             'LEI provided do not meet the requirements', 
#             params={'value':value},
#         )

# def validate_isin(value):
#     if value not correct:
#         # check
#         raise ValidationError(
#             'isin provided do not meet the requirements', 
#             params={'value':value},
#         )



class Party(models.Model):

    PARTY_TYPES = (
        ('ISS', 'Issuer'),
        ('CSD', 'Depository'),
        ('CUS', 'Custodian'),
        ('PPP', 'Physical Private Person'),
    )

    lei = models.CharField(
        max_length=20, 
        blank=True,
        null=True,
        help_text="A 20-character alphanumeric code.", 
        verbose_name="Legal Entity Identifier"
    )
    name = models.CharField(
        max_length=200, 
        blank=False, 
        help_text="The full name."
    )
    holder_role = models.CharField(
        max_length=3,
        choices=PARTY_TYPES,
        blank=True,
        null=True

    )
    original_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    country = CountryField(blank_label='(select country)')
    sector_industry = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    created = models.DateField(
        auto_now = False,
        auto_now_add = True
    )
    updated = models.DateField(
        auto_now = True
    )
    last_file_hash = models.CharField(
        max_length=40,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name_plural = "parties"

    def __str__(self):
        return self.name

    #Used for the pivot
    @classmethod
    def get_json_obs(cls):
        # TODO not to serialize then load. Create specific queryset instead.
        data = serializers.serialize("json", cls.objects.all(), fields=('name','holder_role','country', 'sector_industry'))
        objs = json.loads(data)
        data = []
        for item in objs:
            data.append(item['fields'])
        return data

    @classmethod
    def dump_obs_json(cls, path): 
        with open(path, "w") as f:
            json.dump(cls.get_json_obs(), f)

    @classmethod
    def get_data_frame(cls):
        parties = cls.objects.all()
        data = []
        for party in parties:
            data.append({
                'lei':party.lei,
                'name':party.name,
                'role':party.holder_role,
                'country':party.country,
                'sector':party.sector_industry
            })
        return DataFrame(data)

class Security(models.Model):

    isin = models.CharField(
        max_length=12, 
        blank=False, 
        help_text="A 12-character alphanumeric code.", 
        verbose_name="International Security Identification Number", 
        unique=True
    )
    issuer = models.ForeignKey(
        'Party',
        on_delete=models.PROTECT,
        related_name='security_issuer',
        blank=True,
        null=True,
    )
    depository = models.ForeignKey(
        'Party',
        on_delete=models.PROTECT,
        related_name='security_depository',
        blank=True,
        null=True,
    )
    NOMINAL_UNIT = (
        ('N', 'Nominal'),
        ('U', 'Unit'),
    )
    nominal_unit = models.CharField(
        max_length=1,
        choices=NOMINAL_UNIT,
        blank=True,
        null=True
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    currency = models.CharField(
        max_length=3,
        blank=True,
        null=True
    )
    created = models.DateField(
        auto_now = False,
        auto_now_add = True
    )
    updated = models.DateField(
        auto_now = True
    )

    class Meta:
        verbose_name_plural = "securities"

    def __str__(self):
        return self.isin


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError    

class Holding(models.Model):
    """
    Security that relates two parties.
    """

    party_from = models.ForeignKey(
        'Party',
        on_delete=models.CASCADE,
        related_name='holding_from',
    )
    party_to = models.ForeignKey(
        'Party',
        on_delete=models.CASCADE,
        related_name='holding_to',
    )
    security = models.ForeignKey(
        'Security',
        on_delete=models.CASCADE,
        related_name='holding_security',
    )
    account_ref = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    NOMINAL_UNIT = (
        ('N', 'Nominal'),
        ('U', 'Unit'),
    )
    nominal_unit = models.CharField(
        max_length=1,
        choices=NOMINAL_UNIT,
        blank=False
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    currency = models.CharField(
        max_length=3,
        blank=True,
        null=True
    )
    created = models.DateTimeField(
        default=timezone.now
    )
    updated = models.DateTimeField(
        default=timezone.now
    )
    removed = models.DateTimeField(
        blank = True,
        null = True
    )
    RELATION_TYPES = (
        ('200', '200'),
        ('300', '300'),
        ('350', '350'),
        ('400', '400'),
        ('800', '800'),
    )
    relation_type = models.CharField(
        max_length=3,
        choices=RELATION_TYPES,
        blank=False
    )
    file_hash = models.CharField(
        max_length=40
    )

    def __str__(self):
        return '%s - %s' % (self.party_from, self.party_to)


    def is_active(self):
        return self.removed == None

    def get_amount_in_eur(self):
        if self.currency == "EUR":
            return self.amount.quantize(decimal.Decimal("0.01"))
        if self.currency == "USD":
            return self.amount * decimal.Decimal(0.841601).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)

    def get_amount_in_usd(self):
        if self.currency == "USD":
            return self.amount.quantize(decimal.Decimal("0.01"))
        if self.currency == "EUR":
            return  self.amount * decimal.Decimal(1.18821).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)

    # @classmethod
    # def total_holdings(cls, security):
    #     return decimal.Decimal(cls.objects.filter(security=security).aggregate(models.Sum('amount'))["amount__sum"])

    # @classmethod
    # def count_holdings(cls, security):
    #     return decimal.Decimal(cls.objects.filter(security=security).aggregate(models.Count('amount'))["amount__count"])

    # @classmethod
    # def avg_holdings(cls, security):
    #     return decimal.Decimal(cls.objects.filter(security=security).aggregate(models.Avg('amount'))["amount__avg"])

    # @classmethod
    # def max_holdings(cls, security):
    #     return decimal.Decimal(cls.objects.filter(security=security).aggregate(models.Max('amount'))["amount__max"])

    # @classmethod
    # def min_holdings(cls, security):
    #     return decimal.Decimal(cls.objects.filter(security=security).aggregate(models.Min('amount'))["amount__min"])

    # @classmethod
    # def var_holdings(cls, security):
    #     try:
    #         return decimal.Decimal(cls.objects.filter(security=security).aggregate(models.Variance('amount'))["amount__variance"])
    #     except:
    #         amount_array = [obj.amount for obj in cls.objects.filter(security=security)]
    #         return statistics.pvariance(amount_array)

    # @classmethod
    # def stddev_holdings(cls, security):
    #     try:
    #         return decimal.Decimal(cls.objects.filter(security=security).aggregate(models.StdDev('amount'))["amount__stddev"])
    #     except:
    #         amount_array = [obj.amount for obj in cls.objects.filter(security=security)]
    #         return statistics.pstdev(amount_array)

    # @classmethod
    # def percentile(cls, security, percent, key=lambda x:x):
    #     """
    #     Find the percentile from db based on currency and percentile given.

    #     @parameter N - is a list of values. Note N MUST BE already sorted.
    #     @parameter percent - a float value from 0.0 to 1.0.
    #     @parameter key - optional key function to compute value from each element of N.

    #     @return - the percentile of the values
    #     """
    #     # Order all the values in the data set from smallest to largest.
    #     N = sorted([obj.amount for obj in cls.objects.filter(security=security)])
    #     if not N:
    #         return None
    #     # Multiply k percent by the total number of values, n, + 1.
    #     k = decimal.Decimal((len(N)+1) * percent)
    #     # math floor returns the largest integer less than or equal to k
    #     f = decimal.Decimal(math.floor(k))
    #     #  math ceil returns the smallest integer greater than or equal to k
    #     c = decimal.Decimal(math.ceil(k))
    #     # check if we have a round number
    #     if f == c:
    #         return key(N[int(k)])
    #     d0 = key(N[int(f)]) * (c-k)
    #     d1 = key(N[int(c)]) * (k-f)
    #     return d0+d1

    @classmethod
    def check_for_updates(cls, sender, hash, timestamp):
        """ 
        Check which holdings have been updated and if not
        set a removed date. Return Created, Updated and Removed objects.
        """
        sender_holdings = cls.objects.filter(party_from=sender, removed=None)
        created = []
        updated = []
        removed = []
        for obj in sender_holdings:
            if obj.file_hash != hash:
                obj.removed = timestamp
                obj.save()
                removed.append(obj)
            elif obj.updated == obj.created:
                created.append(obj)
            else:
                updated.append(obj)
        return created, updated, removed

    @classmethod
    def dump_data(cls, path="media/dumps/holdings.json"):
        """
        Dumps data to file
        """
        fields=('party_to','removed', 'created','nominal_unit', 'amount', 'party_from', 'security', 'currency', 'relation_type', 'updated')
        data = serializers.serialize("json", cls.objects.all(), fields=fields)
        data = json.loads(data)
        with open(path, "w") as f:
            json.dump(data, f, default=decimal_default)

    # used for the global graph: /graph/
    # used in security report for graph
    @classmethod
    def get_graph_dict(cls, security=None):
        """ 
        Get graph data from db
        """
        if security:
            holdings = cls.objects.filter(removed=None, security=security)
        else:
            holdings = cls.objects.filter(removed=None)
        #parties = Party.objects.all()
        parties = []
        graphdata = dict({'links':[],'nodes':[]})
        for obj in holdings:
            parties.append(obj.party_from.id)
            parties.append(obj.party_to.id)
            if obj.relation_type == '200' or '800':
                graphdata['links'].append({
                    "source":obj.party_to.id, 
                    "target":obj.party_from.id, 
                    "security":obj.security.isin,
                    "relationship":obj.relation_type, 
                    "nom_unit":obj.nominal_unit,
                    "amount":float(obj.amount),
                    "currency":obj.currency})
            else:
                graphdata['links'].append({
                    "source":obj.party_from.id, 
                    "target":obj.party_to.id, 
                    "security":obj.security.isin,
                    "relationship":obj.relation_type, 
                    "nom_unit":obj.nominal_unit,
                    "amount":float(obj.amount),
                    "currency":obj.currency})
        print(set(parties))
        for party in set(parties):
            obj = Party.objects.get(pk=party)
            graphdata['nodes'].append({'id':obj.id, 'name':obj.name,'group':obj.holder_role or "Other"})
        return graphdata

    # used for the global graph: /graph/
    @classmethod
    def get_indexed_graph_dict(cls, security=None):
        """
        Get graph data from db
        """
        holdings = cls.get_graph_dict(security)
        nodes = holdings['nodes']
        links = holdings['links']
        for link in links:
            for node in nodes:
                if node['id'] == link['target']:
                    link['target'] = nodes.index(node)
                if node['id'] == link['source']:
                    link['source'] = nodes.index(node)
        return dict({"nodes":nodes,"links":links})


    @classmethod
    def dump_graph_json(cls, path="media/dumps/grap.json"):
        """
        Dumps data to file
        """
        with open(path, "w") as f:
            json.dump(cls.get_graph_dict(), f, default=decimal_default)

    #used in security report for second and third chart
    @classmethod
    def get_full_table(cls, security=None):
        if security:
            holdings = cls.objects.filter(removed=None, security=security)
        else:
            holdings = cls.objects.filter(removed=None)
        data = []
        for holding in holdings:
            if holding.relation_type == '200' or holding.relation_type == '800':
                data.append({
                    'source':holding.party_to.name,
                    'target':holding.party_from.name,
                    'security':holding.security.isin,
                    'role_source':holding.party_to.holder_role or "Other",
                    'role_target':holding.party_from.holder_role or "Other",
                    'country_source':holding.party_to.country.name or "Other",
                    'country_target':holding.party_from.country.name or "Other",
                    'currency':holding.currency,
                    'amount':float(holding.amount),
                    'sector_source':holding.party_to.sector_industry or "Other",
                    'sector_target':holding.party_from.sector_industry or "Other",
                    'relationship':holding.relation_type,
                    'created':holding.created,
                    'removed':holding.removed

                })
            else:
                data.append({
                    'source':holding.party_from.name,
                    'target':holding.party_to.name,
                    'security':holding.security.isin,
                    'role_source':holding.party_from.holder_role or "Other",
                    'role_target':holding.party_to.holder_role or "Other",
                    'country_source':holding.party_from.country.name or "Other",
                    'country_target':holding.party_to.country.name or "Other",
                    'currency':holding.currency,
                    'amount':float(holding.amount),
                    'sector_source':holding.party_from.sector_industry or "Other",
                    'sector_target':holding.party_to.sector_industry or "Other",
                    'relationship':holding.relation_type,
                    'created':holding.created,
                    'removed':holding.removed

                })

        return data
