from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from backend.crud.base import make_pagination
from backend.eauth.forms import AuditLogFilterSet
from backend.eauth.models import AuditLog
from backend.globalrules import RP_LIST, RP_VIEW
from backend.utilss import show_results_filter_set


class PesquisarAuditLogView(PermissionRequiredMixin, FilterView):
    model = AuditLog
    filterset_class = AuditLogFilterSet
    paginate_by = 20

    permission_required = ('eauth.list_auditlog',)

    def get_filterset_kwargs(self, filterset_class):
        super(PesquisarAuditLogView, self).get_filterset_kwargs(filterset_class)

        return {
            'data': self.request.GET or None,
            'queryset': self.get_queryset().order_by('-id'),
        }

    def get_context_data(self, **kwargs):
        context = super(PesquisarAuditLogView, self).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''
        context['show_results'] = show_results_filter_set(qr)

        context.update(
            {
                'page_range': make_pagination(page_obj.number, paginator.num_pages),
                'NO_ENTRIES_MSG': 'Nenhum registro de log encontrado!',
                'title': _('Pesquisar Logs de Auditoria'),
            }
        )

        return context

    def get(self, request, *args, **kwargs):
        timefilter = request.GET.get('timestamp', None)

        if not timefilter:
            newgetrequest = request.GET.copy()
            newgetrequest['timestamp'] = 'week'
            request.GET = newgetrequest

        super(PesquisarAuditLogView, self).get(request)

        data = self.filterset.data

        url = ''

        if data:
            url = '&' + str(self.request.META['QUERY_STRING'])
            if url.startswith('&page'):
                url = ''

        resultados = self.object_list
        # if 'page' in self.request.META['QUERY_STRING']:
        #      resultados = self.object_list
        # else:
        #     resultados = []

        context = self.get_context_data(
            filter=self.filterset,
            object_list=resultados,
            filter_url=url,
            numero_res=len(resultados),
        )

        context['show_results'] = show_results_filter_set(self.request.GET.copy())

        return self.render_to_response(context)
