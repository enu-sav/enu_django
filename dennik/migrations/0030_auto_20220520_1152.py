# Generated by Django 3.2.6 on 2022-05-20 11:52

import dennik.models
from django.db import migrations, models
import uctovnictvo.storage


class Migration(migrations.Migration):

    dependencies = [
        ('dennik', '0029_auto_20220519_1354'),
    ]

    operations = [
        migrations.AddField(
            model_name='dokument',
            name='suborposta',
            field=models.FileField(blank=True, help_text='Vložte súbor prijatou / odoslanou poštou (ak nebola súčasťou inej položky)', null=True, storage=uctovnictvo.storage.OverwriteStorage(), upload_to=dennik.models.dennik_file_path, verbose_name='Súbor s poštou'),
        ),
        migrations.AddField(
            model_name='historicaldokument',
            name='suborposta',
            field=models.TextField(blank=True, help_text='Vložte súbor prijatou / odoslanou poštou (ak nebola súčasťou inej položky)', max_length=100, null=True, verbose_name='Súbor s poštou'),
        ),
    ]