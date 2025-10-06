from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0002_alter_categoria_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Auditoria',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('tabla_afectada', models.CharField(max_length=50)),
                ('id_registro', models.IntegerField()),
                ('tipo_accion', models.CharField(choices=[('INSERT', 'Inserción'), ('UPDATE', 'Actualización'), ('DELETE', 'Eliminación')], max_length=6)),
                ('fecha_accion', models.DateTimeField()),
                ('id_usuario', models.IntegerField()),
                ('detalles', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Auditoría',
                'verbose_name_plural': 'Auditorías',
                'db_table': 'Auditoria',
            },
        ),
        migrations.CreateModel(
            name='Cupon',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('codigo', models.CharField(max_length=20, unique=True)),
                ('tipo_descuento', models.CharField(choices=[('Porcentaje', 'Porcentaje'), ('Cantidad Fija', 'Cantidad Fija')], max_length=15)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fecha_inicio', models.DateTimeField()),
                ('fecha_fin', models.DateTimeField()),
                ('valido_para_producto', models.ForeignKey(blank=True, db_column='valido_para_producto_id', null=True, on_delete=models.deletion.SET_NULL, to='productos.producto')),
            ],
            options={
                'verbose_name': 'Cupón',
                'verbose_name_plural': 'Cupones',
                'db_table': 'Cupones',
            },
        ),
        migrations.CreateModel(
            name='ReporteMensualProductos',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('anio', models.IntegerField()),
                ('mes', models.IntegerField()),
                ('cantidad_vendida', models.IntegerField()),
                ('producto', models.ForeignKey(db_column='id_producto', on_delete=models.deletion.PROTECT, to='productos.producto')),
            ],
            options={
                'verbose_name': 'Reporte Mensual de Producto',
                'verbose_name_plural': 'Reportes Mensuales de Productos',
                'db_table': 'ReporteMensualProductos',
                'unique_together': {('anio', 'mes', 'producto')},
            },
        ),
        migrations.AddField(
            model_name='historialinventario',
            name='request_id',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='historialinventario',
            name='usuario',
            field=models.IntegerField(null=True),
        ),
    ]