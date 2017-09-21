import json
import os

from django.conf import settings
from django.contrib import messages
from django.core import serializers
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from .constants import FileExtension
from .models import Party, Security, Holding
from .processors import (Dataset,
                        hash_file,
                        create_or_update_sender,
                        create_or_update_holdings,
                        create_or_update_securities, 
                        create_or_update_issuers,
                        file_contains_sender_info, 
                        get_file_extension)

from django.core.files.storage import FileSystemStorage

def index(request):
    """
    The index page. 
    A GET request returns the index page with all Party, Security and Holding models in context.
    A POST request expects a file.
    The file is stored using the FileSystemStorage, ref: https://docs.djangoproject.com/en/1.11/ref/files/storage/#the-filesystemstorage-class
    """
    
    if request.method == 'POST' and request.FILES['myfile']:
        #TODO check sender
        myfile = request.FILES['myfile']
        # check extension
        ext, verified = get_file_extension(myfile.name)
        if not verified:     
            messages.add_message(request, messages.INFO, 'File extension not accepted.', extra_tags='danger')
            return redirect(reverse('index'))
        else:
            # create FileSystem instance
            fs = FileSystemStorage()
            # temporarily stores the file
            file = fs.save(os.path.join("uploads/",myfile.name), myfile)
            # create hash from file
            hash = hash_file(fs.path(file))
            # check if same file already exists
            if fs.exists(os.path.join("uploads/",hash + ext)):
                messages.add_message(request, messages.INFO, 'File already exists.', extra_tags='warning')
                fs.delete(file)
                ## Message sender that file already exist
                return redirect(reverse('index'))
            

            # create dataset object with the file
            ######TODOOOOOO################
            dataset = Dataset(file, fs.path(file))
            data = dataset.read_data()
            if not dataset.check_header(data):
                messages.add_message(request, messages.INFO, 'Header not verified.', extra_tags='danger')
                fs.delete(file)
                return redirect(reverse('index'))
            if not file_contains_sender_info(fs.path(file)):
                messages.add_message(request, messages.INFO, 'File is missing sender info (record type 100).', extra_tags='danger')
                fs.delete(file)
                return redirect(reverse('index'))
            # if file with the same hash name does not already exist, stores it
            hashfile = fs.save(os.path.join("uploads/",hash + ext), myfile)   
            messages.add_message(request, messages.INFO, 'File stored.', extra_tags='success')
            # delete temp file
            fs.delete(file)


        df = dataset.get_data_frame(data)

        timestamp = dataset.get_timestamp(df)
        sender = dataset.get_sender_row(df)
        holdings = dataset.get_holdings_list(df)
        sender = create_or_update_sender(sender, hash)
        holdings = create_or_update_holdings(sender, timestamp, holdings, hash)
        securities = create_or_update_securities(sender, timestamp, dataset.get_securities_list(df), hash)
        issuers = create_or_update_issuers(dataset.get_issuers_list(df))

        if sender:
            if timestamp:
                messages.add_message(request, messages.INFO, 'Sender and timestamp succesfully updated.', extra_tags='success')
        created, updated, removed = Holding.check_for_updates(sender, hash, timestamp)
        return render(request, 'holderbase/success.html', {"created":created, "updated":updated, "removed":removed})
    context = {"parties":Party.objects.all(), "securities":Security.objects.all(), "holdings":Holding.objects.filter(removed=None)}
    return render(request, 'index.html', context)


# Used on the index
# def party_count(request):
#     parties = Party.objects.all()
#     party_types = ['PPP', 'ISS','CSD', 'CUS']
#     dataset = []
#     for typ in party_types:
#         dataset.append({'label': typ, 'count': Party.objects.filter(company_type=typ).count()})
#     return JsonResponse(dataset, safe=False)

# Used for the pivot: /pivot/
def party_pivot(request):
    return JsonResponse(Party.get_json_obs(), safe=False)

# used for the global graph: /graph/
def get_holding_graph(request):
    return JsonResponse(Holding.get_indexed_graph_dict(), safe=False)

# Security report view
def security_report(request, pk):
    template = "holderbase/security_report.html"
    # security = {
    #     'count':Holding.count_holdings(security=pk),
    #     'total':Holding.total_holdings(security=pk),
    #     'mean':Holding.avg_holdings(security=pk),
    #     'var':Holding.var_holdings(security=pk),
    #     'stdev':Holding.stddev_holdings(security=pk)
    # }
    obj = Security.objects.get(pk=pk)
    context = {'pk':pk, 'obj':obj}
    return render(request, template, context)

def issuer_report(request, pk):
    template = "holderbase/issuer_report.html"
    # security = {
    #     'count':Holding.count_holdings(security=pk),
    #     'total':Holding.total_holdings(security=pk),
    #     'mean':Holding.avg_holdings(security=pk),
    #     'var':Holding.var_holdings(security=pk),
    #     'stdev':Holding.stddev_holdings(security=pk)
    # }
    obj = Security.objects.get(pk=pk)
    context = {'pk':pk, 'obj':obj}
    return render(request, template, context)


def get_indexed_graph(request, pk):
    return JsonResponse(Holding.get_indexed_graph_dict(security=pk), safe=False)


def get_sankey(request, pk):
    data = Holding.get_indexed_graph_dict(security=pk)
    # for node in data['nodes']:
    #     if node['group'] == 'ISS':
    #         node['xPos'] = 0
    #     elif node['group'] == 'CSD':
    #         node['xPos'] = .5
    #     elif node['group'] == 'CUS':
    #         node['xPos'] = 1
    #     elif node['group'] == 'OWN':
    #         node['xPos'] = 2
    for item in data['links']:
        item['value'] = item['amount']
        if item['source'] == item['target']:
            data['links'].remove(item)
    return JsonResponse(data, safe=False)

def get_full_sankey(request):
    data = Holding.get_indexed_graph_dict()
    #for node in data['nodes']:
        # if node['group'] == 'ISS':
        #     node['xPos'] = 0
        # elif node['group'] == 'CSD':
        #     node['xPos'] = 0.5
        # elif node['group'] == 'CUS':
        #     node['xPos'] = 1
        # elif node['group'] == 'OWN':
        #     node['xPos'] = 1
    for item in data['links']:
        item['value'] = item['amount']
        if item['source'] == item['target']:
            data['links'].remove(item)
    return JsonResponse(data, safe=False)


# def get_security_holdings(request, pk):
#     fields=('party_to','removed', 'created','nominal_unit', 'amount', 'party_from', 'security', 'currency', 'relation_type', 'updated')
#     data = serializers.serialize("json", Holding.objects.filter(security=pk), fields=fields)
#     data = json.loads(data)
#     return JsonResponse(data, safe=False)

#used in security report for graph
def get_security_graph(request, pk):
    return JsonResponse(Holding.get_graph_dict(security=pk), safe=False)


# def get_holdings(request):
#     fields=('party_to','removed', 'created','nominal_unit', 'amount', 'party_from', 'security', 'currency', 'relation_type', 'updated')
#     data = serializers.serialize("json", Holding.objects.all(), fields=fields)
#     data = json.loads(data)
#     return JsonResponse(data, safe=False)



    # def get_master_data(request):
    # holdings = Holding.objects.all()
    # master_data = {'links':[],'nodes':[]}
    # for holding in holdings:
    #     l = {}
    #     if holding.relation_type == '200':
    #         l['source'] = holding.party_to.name
    #         l['target'] = holding.party_from.name
    #     else:
    #         l['source'] = holding.party_from.name
    #         l['target'] = holding.party_to.name
    #     l['security'] = holding.security.isin
    #     l['amount'] = float(holding.amount)
    #     l['currency'] = holding.currency
    #     l['created'] = holding.created
    #     l['removed'] = holding.removed
    #     master_data['links'].append(l)
    # parties = Party.objects.all()
    # for party in parties:
    #     p = {}
    #     p['lei'] = party.lei
    #     p['name'] = party.name
    #     p['role'] = party.holder_role
    #     p['country'] = party.country.name
    #     p['sector'] = party.sector_industry
    #     master_data['nodes'].append(p)
    # return JsonResponse(master_data, safe=False)

#used in security report for second and third chart
def get_full_data(request, pk):
    data = Holding.get_full_table(security=pk)
    return JsonResponse(data, safe=False)