# Generated by Django 3.2.4 on 2025-01-26 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0215_auto_20250116_1515'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dodavatel',
            name='adresa_mesto',
            field=models.CharField(help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='dodavatel',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='historicaldodavatel',
            name='adresa_mesto',
            field=models.CharField(help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='historicaldodavatel',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='historicaldohodar',
            name='adresa_mesto',
            field=models.CharField(help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='historicaldohodar',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='historicalinternypartner',
            name='adresa_mesto',
            field=models.CharField(help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='historicalinternypartner',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='historicalnajomnik',
            name='adresa_mesto',
            field=models.CharField(help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='historicalnajomnik',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='historicalzamestnanec',
            name='adresa_mesto',
            field=models.CharField(help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='historicalzamestnanec',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='internypartner',
            name='adresa_mesto',
            field=models.CharField(help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='internypartner',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='najomnik',
            name='adresa_mesto',
            field=models.CharField(help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='najomnik',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='zamestnanecdohodar',
            name='adresa_mesto',
            field=models.CharField(help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='zamestnanecdohodar',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
    ]