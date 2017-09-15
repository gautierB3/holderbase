from django.contrib import admin

from .models import Party, Security, Holding

class PartyAdmin(admin.ModelAdmin):
	fields = ('lei', 'name', 'holder_role', 'country', 'sector_industry')
	list_display = ('name', 'lei', 'holder_role', 'country', 'sector_industry', 'last_file_hash')
	list_filter = ('holder_role', 'country')
	search_fields = ('lei', 'name')

class SecurityAdmin(admin.ModelAdmin):
	fields = ('isin', 'issuer', 'depository')
	list_display = ('isin', 'issuer', 'depository', 'created', 'updated',)
	search_fields = ('isin', 'issuer', 'depository')

class HoldingAdmin(admin.ModelAdmin):
	list_display = ('party_from', 'party_to', 'security', 'amount', 'currency', 'relation_type', 'removed','created', 'updated','file_hash')


admin.site.register(Party, PartyAdmin)
admin.site.register(Security, SecurityAdmin)
admin.site.register(Holding, HoldingAdmin)
