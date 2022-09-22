# Generated by Django 3.2.6 on 2022-09-16 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0085_auto_20220915_1054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalplatovyvymer',
            name='uvazok',
            field=models.DecimalField(decimal_places=2, help_text='Zadajte týždenný pracovný úväzok. Napríklad, pri plnom úväzku 37,5 hod, pri polovičnom 18,75 hod', max_digits=8, verbose_name='Úväzok týždenne'),
        ),
        migrations.AlterField(
            model_name='historicalplatovyvymer',
            name='uvazok_denne',
            field=models.DecimalField(decimal_places=2, help_text='Zadajte denný pracovný úväzok. Napríklad, pri plnom úväzku 7,5 hod, pri polovičnom úväzku a dohodnutých 3 prac. dňoch týždenne 6,25 hod (3*6,25= 18,75)', max_digits=8, verbose_name='Úväzok denne'),
        ),
        migrations.AlterField(
            model_name='platovyvymer',
            name='uvazok',
            field=models.DecimalField(decimal_places=2, help_text='Zadajte týždenný pracovný úväzok. Napríklad, pri plnom úväzku 37,5 hod, pri polovičnom 18,75 hod', max_digits=8, verbose_name='Úväzok týždenne'),
        ),
        migrations.AlterField(
            model_name='platovyvymer',
            name='uvazok_denne',
            field=models.DecimalField(decimal_places=2, help_text='Zadajte denný pracovný úväzok. Napríklad, pri plnom úväzku 7,5 hod, pri polovičnom úväzku a dohodnutých 3 prac. dňoch týždenne 6,25 hod (3*6,25= 18,75)', max_digits=8, verbose_name='Úväzok denne'),
        ),
    ]