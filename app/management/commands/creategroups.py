from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = "The command is used to generate user groups/ role after project setup"

    group_permissions = [
        {
            "name": "admin",
            "perms": [
                "view_stockitem",
                "change_stockitem",
                "view_invoicetest",
                # "override_invoicetest",
                "view_bypassmodel",
                "view_activity",
                "view_company",
            ],
        },
        {
            "name": "operator",
            "perms": [
                "view_stockitem",
                "view_invoicetest",
                # "override_invoicetest",
                "view_bypassmodel",
                "view_activity",
                "view_company",
            ],
        },
        {
            "name": "warehouse_manager",
            "perms": [
                "view_stockitem",
                "view_invoicetest",
                "view_bypassmodel",
                "view_activity",
            ],
        },
        {
            "name": "client",
            "perms": ["view_stockitem", "view_activity"],
        },
    ]
    group_list = ["admin", "operator", "warehouse_manager", "client"]  # dispatcher
    # permissions = ["view_stockitem", "view_stockitem", "view_invoicetest"]

    def handle(self, *args, **kwargs):
        for grp in self.group_permissions:
            group, created = Group.objects.get_or_create(name=grp.get("name"))
            grp_perms = grp.get("perms")
            grp_perms = list(
                map(lambda i: Permission.objects.get(codename=i), grp_perms)
            )
            group.permissions.set(grp_perms)
        self.stdout.write(f"This Group created: {self.group_list}.")
