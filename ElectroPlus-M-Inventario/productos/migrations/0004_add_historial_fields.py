from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0003_create_reporting_models'),
    ]

    operations = [
        migrations.RunSQL(
            """
            ALTER TABLE `HistorialInventario` 
            ADD COLUMN `usuario` INT NULL AFTER `fecha`,
            ADD COLUMN `request_id` VARCHAR(50) NULL AFTER `usuario`;
            """,
            """
            ALTER TABLE `HistorialInventario` 
            DROP COLUMN `request_id`,
            DROP COLUMN `usuario`;
            """
        ),
    ]