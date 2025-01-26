# Generated by Django 3.2.4 on 2025-01-26 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zmluvy', '0055_auto_20240725_1546'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalosobaautor',
            name='adresa_mesto',
            field=models.CharField(blank=True, help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='historicalosobaautor',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='historicalosobaautor',
            name='koresp_adresa_mesto',
            field=models.CharField(blank=True, help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Korešpondenčná adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='historicalosobaautor',
            name='koresp_adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Korešpondenčná adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='historicalosobagrafik',
            name='adresa_mesto',
            field=models.CharField(blank=True, help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='historicalosobagrafik',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='historicalosobagrafik',
            name='koresp_adresa_mesto',
            field=models.CharField(blank=True, help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Korešpondenčná adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='historicalosobagrafik',
            name='koresp_adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Korešpondenčná adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='osobaautor',
            name='adresa_mesto',
            field=models.CharField(blank=True, help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='osobaautor',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='osobaautor',
            name='koresp_adresa_mesto',
            field=models.CharField(blank=True, help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Korešpondenčná adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='osobaautor',
            name='koresp_adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Korešpondenčná adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='osobagrafik',
            name='adresa_mesto',
            field=models.CharField(blank=True, help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='osobagrafik',
            name='adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Adresa – ulica a číslo domu'),
        ),
        migrations.AlterField(
            model_name='osobagrafik',
            name='koresp_adresa_mesto',
            field=models.CharField(blank=True, help_text='Ak obec <strong>nemá ulice</strong>, zadajte aj číslo domu, napr. <em>059 60 Tatranská Lomnica 135</em>', max_length=200, null=True, verbose_name='Korešpondenčná adresa – PSČ a obec'),
        ),
        migrations.AlterField(
            model_name='osobagrafik',
            name='koresp_adresa_ulica',
            field=models.CharField(blank=True, help_text='Vyplňte, len ak obec <strong>má ulice</strong>, inak nechajte prázdne', max_length=200, null=True, verbose_name='Korešpondenčná adresa – ulica a číslo domu'),
        ),
    ]