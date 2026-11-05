from django.utils.translation import gettext_lazy as _

from backend.utilss import dict2attr

default_app_config = 'backend.globalrules.apps.AppConfig'


RP_LIST, RP_VIEW, RP_ADD, RP_CHANGE, RP_DELETE = (
    '.list_',
    '.view_',
    '.add_',
    '.change_',
    '.delete_',
)


GROUP_ADM_ADMIN = _('Administrador do Sistema')

GROUP_VISITANTE = ''

BACKEND_GROUPS = [
    GROUP_ADM_ADMIN,
]

menu_administracao = 'menu_1'

action_1 = 'orcamento_1'

PERMS_FOR_USERS = (
    (menu_administracao, _('Mostrar Menu 1')),

    (action_1, _('Ação 1')),
)

VARS = {
    k: v for k, v in locals().items() \
        if k.startswith('GROUP_') or \
        k.startswith('action_') or \
        k.startswith('menu_')
}

PERMS_FOR_USERS_DICT = dict(PERMS_FOR_USERS)
PERMS_FOR_USERS_DICT.update(VARS)

MAP_GROUPS_AND_PERMS = dict2attr(PERMS_FOR_USERS_DICT)
