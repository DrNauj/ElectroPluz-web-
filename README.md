# ElectroPlus — Microservicios

Repositorio de los microservicios para la evidencia: M-Inventario, M-Ventas y API Gateway.

Resumen rápido:
- M-Inventario: http://localhost:8001/
- M-Ventas: http://localhost:8002/
- API Gateway: http://localhost:8000/

Documentación principal:
- `documentacion_unificada.md` (maestro)

Archivos de documentación (apuntadores a la versión unificada):
 - `documentacion-implementacion.md`
 - `documentacion-pruebas.md`
 - `documentacion-problemas.md`
 - `documentacion-seguridad.md`
 - `documentacion-estado-actual.md`
 - `documentacion ElectroPluz.txt`

Quick start (Windows PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Ejecutar servicios en 3 terminales
cd .\ElectroPlus-M-Inventario
python manage.py migrate; python manage.py runserver 8001

cd ..\ElectroPlus-M-Ventas
python manage.py migrate; python manage.py runserver 8002

cd ..\ElectroPlus-Gateway
python manage.py migrate; python manage.py runserver 8000
```

Checklist para entrega:
- [ ] `documentacion_unificada.md` completada
- [ ] README con instrucciones (este archivo)
- [ ] Swagger para cada microservicio
- [ ] Pruebas unitarias e integración

Si quieres, puedo generar un `requirements.txt` consolidado y pruebas básicas (pytest) en la rama actual.