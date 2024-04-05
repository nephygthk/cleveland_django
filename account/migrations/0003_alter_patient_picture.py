# Generated by Django 5.0.3 on 2024-04-05 16:22

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_alter_payment_receipt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='picture',
            field=cloudinary.models.CloudinaryField(max_length=255, verbose_name='image'),
        ),
    ]