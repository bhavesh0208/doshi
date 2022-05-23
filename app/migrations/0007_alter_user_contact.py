# Generated by Django 3.2.2 on 2022-05-16 07:39

import app.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_alter_stock_barcode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='contact',
            field=models.CharField(max_length=10, unique=True, validators=[app.validators.validate_contact]),
        ),
    ]