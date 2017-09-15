from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    #url(r'^graph/$', TemplateView.as_view(template_name="holderbase/graph.html")),
    url(r'^pivot/$', TemplateView.as_view(template_name="holderbase/pivot.html")),
    url(r'^security/(?P<pk>\d+)/$', views.security_report),#security report view
    # ajax calls
    url(r'^get/party/observations/$', views.party_pivot),# used by pivot
    url(r'^get/graph/security/(?P<pk>\d+)/$', views.get_security_graph),#used in security report for graph
    url(r'^get/holdings/(?P<pk>\d+)/$', views.get_full_data),#used in security report for second and third chart
    url(r'^get/holding/graph/$', views.get_holding_graph),#used by /graph/
    #url(r'^get/masterdata/$', views.get_master_data),#used in security report for first chart
    #url(r'^get/security/(?P<pk>\d+)/$', views.get_security_holdings),
    #url(r'^get/holdings/$', views.get_holdings),
    #url(r'^party/count/$', views.party_count)
]
