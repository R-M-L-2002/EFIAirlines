# ✈️ EFIAirlines  

Proyecto desarrollado en **Django** que simula la gestión de una aerolínea.  
Incluye autenticación, administración, y un panel para manejar vuelos, pasajeros y más.  

---

## 🚀 Instalación y configuración  

Sigue estos pasos para levantar el proyecto en tu máquina local:  

```bash
# 1. Clonar el repositorio
git clone https://github.com/R-M-L-2002/EFIAirlines.git

# 2. Entrar al directorio del proyecto
cd EFIAirlines/airlines

# 3. Crear un entorno virtual
python3 -m venv venv 

# 4. Activar el entorno virtual
# En Linux / Mac
source venv/bin/activate  
# En Windows
venv\Scripts\activate      

# 5. Instalar dependencias
pip install -r requirements.txt

# 6. Aplicar migraciones
python manage.py migrate

# 7. Crear un superusuario (para acceder al panel de admin)
python manage.py createsuperuser

# 8. Levantar el servidor de desarrollo
python manage.py runserver
