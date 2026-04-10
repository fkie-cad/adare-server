# Migration for scoped tags and tags on TestfunctionSet

from django.db import migrations, models
import django.db.models.deletion


def split_existing_tags(apps, schema_editor):
    """Split existing tags containing ':' into scope + value, seed predefined scopes."""
    TagScope = apps.get_model('experiments', 'TagScope')
    Tag = apps.get_model('experiments', 'Tag')

    # Seed predefined scopes
    predefined_scopes = {
        'tool': '#1e40af',
        'artifact': '#166534',
        'goal': '#6b21a8',
    }
    scope_objects = {}
    for scope_name, color in predefined_scopes.items():
        scope_obj, _ = TagScope.objects.get_or_create(
            name=scope_name,
            defaults={'is_predefined': True, 'color': color},
        )
        scope_objects[scope_name] = scope_obj

    # Process existing tags
    for tag in Tag.objects.all():
        if ':' in tag.name:
            parts = tag.name.split(':', 1)
            scope_name = parts[0]
            value = parts[1]
            # Get or create the scope
            if scope_name not in scope_objects:
                scope_obj, _ = TagScope.objects.get_or_create(
                    name=scope_name,
                    defaults={'is_predefined': False, 'color': ''},
                )
                scope_objects[scope_name] = scope_obj
            tag.scope = scope_objects[scope_name]
            tag.value = value
        else:
            tag.value = tag.name
        tag.save()


def reverse_split(apps, schema_editor):
    """Reverse: set value back to name for all tags."""
    Tag = apps.get_model('experiments', 'Tag')
    for tag in Tag.objects.all():
        tag.value = tag.name
        tag.scope = None
        tag.save()


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0004_remove_testfunctionset_unique_tf_version_and_more'),
    ]

    operations = [
        # Create TagScope model
        migrations.CreateModel(
            name='TagScope',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('is_predefined', models.BooleanField(default=False)),
                ('color', models.CharField(blank=True, max_length=7)),
            ],
        ),
        # Add scope FK to Tag (nullable)
        migrations.AddField(
            model_name='tag',
            name='scope',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='tags', to='experiments.tagscope',
            ),
        ),
        # Add value field to Tag (with temporary default)
        migrations.AddField(
            model_name='tag',
            name='value',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        # Increase name max_length to accommodate scope:value
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=150, unique=True),
        ),
        # Add tags M2M to TestfunctionSet
        migrations.AddField(
            model_name='testfunctionset',
            name='tags',
            field=models.ManyToManyField(blank=True, to='experiments.tag'),
        ),
        # Data migration: split existing tags
        migrations.RunPython(split_existing_tags, reverse_split),
        # Add unique constraint on (scope, value)
        migrations.AddConstraint(
            model_name='tag',
            constraint=models.UniqueConstraint(fields=['scope', 'value'], name='unique_scope_value'),
        ),
    ]
