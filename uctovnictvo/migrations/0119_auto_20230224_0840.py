# Generated by Django 3.2.6 on 2023-02-24 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uctovnictvo', '0118_auto_20230224_0820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dohoda',
            name='miesto_vykonu',
            field=models.CharField(help_text='Miesto výkonu práce: presná adresa alebo presné adresy, prípadne ak je viac adries, určenie hlavného miesta výkonu práce, <br />alebo znenie: <strong>miesto výkonu práce určuje zamestnanec</strong>', max_length=200, null=True, verbose_name='Miesto výkonu'),
        ),
        migrations.AlterField(
            model_name='dohoda',
            name='pracovny_cas',
            field=models.CharField(help_text='Uviesť jednu z možností:<ul><li>1. znenie: "<strong>zamestnanec si sám rozvrhuje pracovný čas</strong></li> <li>2. znenie: uviesť presnú informáciu o <ul><li>a) dňoch a časových úsekoch, v ktorých môže od zamestnanca vyžadovať vykonávanie práce,</li> <li>b) lehote, v ktorej má byť zamestnanec informovaný o výkone práce pred jej začiatkom, ktorá nesmie byť kratšia ako 24 hodín.</li> </ul> </li></ul>', max_length=200, null=True, verbose_name='Pracovný čas'),
        ),
        migrations.AlterField(
            model_name='historicaldobps',
            name='miesto_vykonu',
            field=models.CharField(help_text='Miesto výkonu práce: presná adresa alebo presné adresy, prípadne ak je viac adries, určenie hlavného miesta výkonu práce, <br />alebo znenie: <strong>miesto výkonu práce určuje zamestnanec</strong>', max_length=200, null=True, verbose_name='Miesto výkonu'),
        ),
        migrations.AlterField(
            model_name='historicaldobps',
            name='pracovny_cas',
            field=models.CharField(help_text='Uviesť jednu z možností:<ul><li>1. znenie: "<strong>zamestnanec si sám rozvrhuje pracovný čas</strong></li> <li>2. znenie: uviesť presnú informáciu o <ul><li>a) dňoch a časových úsekoch, v ktorých môže od zamestnanca vyžadovať vykonávanie práce,</li> <li>b) lehote, v ktorej má byť zamestnanec informovaný o výkone práce pred jej začiatkom, ktorá nesmie byť kratšia ako 24 hodín.</li> </ul> </li></ul>', max_length=200, null=True, verbose_name='Pracovný čas'),
        ),
        migrations.AlterField(
            model_name='historicaldopc',
            name='miesto_vykonu',
            field=models.CharField(help_text='Miesto výkonu práce: presná adresa alebo presné adresy, prípadne ak je viac adries, určenie hlavného miesta výkonu práce, <br />alebo znenie: <strong>miesto výkonu práce určuje zamestnanec</strong>', max_length=200, null=True, verbose_name='Miesto výkonu'),
        ),
        migrations.AlterField(
            model_name='historicaldopc',
            name='pracovny_cas',
            field=models.CharField(help_text='Uviesť jednu z možností:<ul><li>1. znenie: "<strong>zamestnanec si sám rozvrhuje pracovný čas</strong></li> <li>2. znenie: uviesť presnú informáciu o <ul><li>a) dňoch a časových úsekoch, v ktorých môže od zamestnanca vyžadovať vykonávanie práce,</li> <li>b) lehote, v ktorej má byť zamestnanec informovaný o výkone práce pred jej začiatkom, ktorá nesmie byť kratšia ako 24 hodín.</li> </ul> </li></ul>', max_length=200, null=True, verbose_name='Pracovný čas'),
        ),
        migrations.AlterField(
            model_name='historicaldovp',
            name='miesto_vykonu',
            field=models.CharField(help_text='Miesto výkonu práce: presná adresa alebo presné adresy, prípadne ak je viac adries, určenie hlavného miesta výkonu práce, <br />alebo znenie: <strong>miesto výkonu práce určuje zamestnanec</strong>', max_length=200, null=True, verbose_name='Miesto výkonu'),
        ),
        migrations.AlterField(
            model_name='historicaldovp',
            name='pracovny_cas',
            field=models.CharField(help_text='Uviesť jednu z možností:<ul><li>1. znenie: "<strong>zamestnanec si sám rozvrhuje pracovný čas</strong></li> <li>2. znenie: uviesť presnú informáciu o <ul><li>a) dňoch a časových úsekoch, v ktorých môže od zamestnanca vyžadovať vykonávanie práce,</li> <li>b) lehote, v ktorej má byť zamestnanec informovaný o výkone práce pred jej začiatkom, ktorá nesmie byť kratšia ako 24 hodín.</li> </ul> </li></ul>', max_length=200, null=True, verbose_name='Pracovný čas'),
        ),
    ]