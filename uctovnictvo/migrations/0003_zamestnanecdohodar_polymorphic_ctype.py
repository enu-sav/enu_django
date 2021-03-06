# Generated by Django 3.2.6 on 2021-10-28 17:11

from django.contrib.contenttypes.models import ContentType
from uctovnictvo.models import ZamestnanecDohodar
from django.db import migrations, models
import django.db.models.deletion

def forwards_func(apps, schema_editor):
    ZamestnanecDohodar = apps.get_model('uctovnictvo', 'ZamestnanecDohodar')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    new_ct = ContentType.objects.get_for_model(ZamestnanecDohodar)
    ZamestnanecDohodar.objects.filter(polymorphic_ctype__isnull=True).update(polymorphic_ctype=new_ct)


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('uctovnictvo', '0002_delete_historicalzamestnanecdohodar'),
    ]

    operations = [
        migrations.AddField(
            model_name='zamestnanecdohodar',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_uctovnictvo.zamestnanecdohodar_set+', to='contenttypes.contenttype'),
        ),
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
    ]
