from django.db import migrations, models


class Migration(migrations.Migration):
    """Relax the DB-level unique constraint on Environment.name and
    TestfunctionSet.name so a modify PR's proposed draft (published=False) can
    coexist with the still-published object under the same name. Content
    uniqueness is still enforced by the unique sha256hash field, and the
    published object is resolved via published-aware get_object() lookups.
    """

    dependencies = [
        ('experiments', '0011_environment_vm'),
    ]

    operations = [
        migrations.AlterField(
            model_name='environment',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='testfunctionset',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]
