from django.contrib.auth import get_user_model

from backend.globalrules import (
    MAP_GROUPS_AND_PERMS,
    RP_ADD,
    RP_CHANGE,
    RP_DELETE,
    RP_LIST,
    RP_VIEW,
)
from backend.utils.models import (
    Metadata,
    Teste,
)

__base__ = [RP_LIST, RP_VIEW, RP_ADD, RP_CHANGE, RP_DELETE]
__base_view__ = [RP_LIST, RP_VIEW]
__base_change__ = [RP_LIST, RP_VIEW, RP_CHANGE]

__perms_publicas__ = {}


rules_group_adm_admin = {
    "group": MAP_GROUPS_AND_PERMS.GROUP_ADM_ADMIN,
    "rules": [
        # (model, perms que o user do grupo terá , perms_publicas para a api)
        (
            get_user_model(),
            __base__
            + [
                MAP_GROUPS_AND_PERMS.menu_administracao,
            ],
            set(),
        ),
        (Teste, __base__, set(__base_view__)),
        (Metadata, __base__, set()),
    ],
}


rules_group_visitante = {"group": MAP_GROUPS_AND_PERMS.GROUP_VISITANTE, "rules": []}

rules_patterns = [
    rules_group_adm_admin,
    rules_group_visitante,
]


rules_patterns_public = {}


def _get_registration_key(model):
    return "%s:%s" % (model._meta.app_label, model._meta.model_name)


for rules_group in rules_patterns:
    # print(rules_group['group'])
    for rules in rules_group["rules"]:
        # print(rules)
        key = _get_registration_key(rules[0])
        if key not in rules_patterns_public:
            rules_patterns_public[key] = set()

        r = set(
            map(
                lambda x, m=rules[0]: "{}{}{}".format(
                    m._meta.app_label, x, m._meta.model_name
                ),
                rules[2],
            )
        )
        rules_patterns_public[key] = rules_patterns_public[key] | r
