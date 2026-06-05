from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('responsaveis', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='responsavel',
            name='autorizacao_imagem',
            field=models.BooleanField(default=True),
        ),
    ]
