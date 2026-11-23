from django.db import migrations, models


def publier_films_existants(apps, schema_editor):
    Film = apps.get_model("cinema", "Film")
    Film.objects.using(schema_editor.connection.alias).all().update(
        est_publie=True
    )


class Migration(migrations.Migration):
    dependencies = [
        ("cinema", "0005_billet"),
    ]

    operations = [
        migrations.AddField(
            model_name="film",
            name="est_publie",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            publier_films_existants,
            migrations.RunPython.noop,
        ),
    ]
