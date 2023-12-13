from django.core.management.base import BaseCommand, CommandParser
from app.models import Invoice, InvoiceTest, InvoiceStockItem, StockItem, Company
import json


class Command(BaseCommand):
    help = "The command is used for loading and tranformaing data of `Invoice model` to new Invoice ie `InvoiceTest`model and migrate into the database"
    invoice_model = InvoiceTest
    sku_model = StockItem
    invoice_item_model = InvoiceStockItem
    company_model = Company

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "-f", "--filename", type=str, help="please provide json files"
        )

    def handle(self, *args, **kwargs):
        filename = kwargs.get("filename")
        fp = open(filename)
        invoice_objs_list = json.load(fp)

        for inv in invoice_objs_list:
            company = self.company_model.objects.get(
                company_name=inv.get("invoice_company_name")
            )
            context = {
                "invoice_no": inv.get("invoice_no"),
                "invoice_party_name": inv.get("invoice_party_name"),
                "invoice_sales_ledger": inv.get("invoice_sales_ledger"),
                "invoice_date": inv.get("invoice_date"),
                "total_qty": inv.get("invoice_total_qty"),
                "total_amount": inv.get("invoice_total_amount"),
                "last_interacting_user": None,
                "is_pi_invoice": False,
                "invoice_company": company,
            }
            try:
                if inv.get("invoice_no") != "PI":
                    invoice, created = self.invoice_model.objects.get_or_create(
                        invoice_no=inv.get("invoice_no"), defaults=context
                    )
                    if not created:
                        self.stdout.write(
                            self.style.WARNING(
                                f"duplicate invoice no {inv['invoice_no']} and not a PI invoice."
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f"Invoice created {inv['invoice_no']}.")
                        )
                        stock_items = list(
                            filter(
                                lambda a: a.get("invoice_no")
                                == context.get("invoice_no"),
                                invoice_objs_list,
                            )
                        )

                        context_sku = {
                            "item_qty": stk.get("invoice_item_qty"),
                            "item_rate": stk.get("invoice_item_rate"),
                            "item_amount": stk.get("invoice_item_amount"),
                            "item_total_scan": stk.get("invoice_item_total_scan"),
                            "item_scanned_status": stk.get(
                                "invoice_item_scanned_status"
                            ),
                        }

                        for stk in stock_items:
                            sku = self.sku_model.get_stock_item(
                                stk.get("invoice_item_sku_name")
                            )
                            if sku:
                                context_sku.update({"stock_item": sku})
                                inv_sku = self.invoice_item_model.objects.create(
                                    **context_sku
                                )
                                invoice.invoice_items.add(inv_sku)
                            else:
                                self.style.WARNING(
                                    f"SKU not found with a name {stk['invoice_item_sku_name']}."
                                )
                                continue

                else:
                    context.update({"is_pi_invoice": True})

                    invoice, created = self.invoice_model.objects.get_or_create(
                        invoice_party_name=context.get("invoice_party_name"),
                        defaults=context,
                    )
                    if created:
                        stock_items = list(
                            filter(
                                lambda a: a.get("invoice_no")
                                == context.get("invoice_no")
                                and a.get("invoice_party_name")
                                == context.get("invoice_party_name"),
                                invoice_objs_list,
                            )
                        )

                        context_sku = {
                            "item_qty": stk.get("invoice_item_qty"),
                            "item_rate": stk.get("invoice_item_rate"),
                            "item_amount": stk.get("invoice_item_amount"),
                            "item_total_scan": stk.get("invoice_item_total_scan"),
                            "item_scanned_status": stk.get(
                                "invoice_item_scanned_status"
                            ),
                        }

                        for stk in stock_items:
                            sku = self.sku_model.get_stock_item(
                                stk.get("invoice_item_sku_name")
                            )
                            if sku:
                                context_sku.update({"stock_item": sku})
                                inv_sku = self.invoice_item_model.objects.create(
                                    **context_sku
                                )
                                invoice.invoice_items.add(inv_sku)
                            else:
                                self.style.WARNING(
                                    f"SKU not found with a name {stk['invoice_item_sku_name']}."
                                )
                                continue

                        self.stdout.write(
                            self.style.SUCCESS(f"Invoice created {inv['invoice_no']}.")
                        )

            except Exception as e:
                print(str(e))
                self.stdout.write(self.style.WARNING(f"Error: {e}."))
