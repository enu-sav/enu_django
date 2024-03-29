# Generated by Django 3.2.4 on 2023-12-12 08:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dennik', '0041_auto_20231210_1505'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dokument',
            name='sposob',
            field=models.CharField(choices=[('posta', 'Pošta'), ('iposta', 'Interná pošta'), ('ipostamail', 'Interná pošta + E-mail'), ('mail', 'E-mail'), ('osobne', 'Osobne'), ('web', 'Web rozhranie')], help_text='Zvoľte spôsob, akým bol dokument prijatý/doručený', max_length=20, null=True, verbose_name='Spôsob doručenia'),
        ),
        migrations.AlterField(
            model_name='historicaldokument',
            name='sposob',
            field=models.CharField(choices=[('posta', 'Pošta'), ('iposta', 'Interná pošta'), ('ipostamail', 'Interná pošta + E-mail'), ('mail', 'E-mail'), ('osobne', 'Osobne'), ('web', 'Web rozhranie')], help_text='Zvoľte spôsob, akým bol dokument prijatý/doručený', max_length=20, null=True, verbose_name='Spôsob doručenia'),
        ),
    ]
