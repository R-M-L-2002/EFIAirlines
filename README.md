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

# 8. Poblar la base de datos (Seed)
Este comando cargará datos iniciales.
python scripts/seed_database.py

# 8. Levantar el servidor de desarrollo
python manage.py runserver

```

---

## 🏛️ Arquitectura del Backend
El backend sigue un patrón de diseño estructurado para separar responsabilidades, inspirado en la arquitectura por capas. Esto promueve un código desacoplado, más fácil de testear y de mantener.

► Model: Define las entidades y la estructura de la base de datos (la fuente de verdad).

► Repository: Abstrae el acceso a los datos. Centraliza todas las consultas a la base de datos.

► Service: Contiene la lógica de negocio pura (reglas, validaciones complejas, orquestación).

► View (API/Web): Expone los servicios a través de endpoints de API (usando ViewSet) o plantillas de Django.

► Serializer: Define la representación de los datos (JSON) para la API y maneja la validación de entrada.

► URL: Mapea las rutas a las vistas correspondientes.

---

## 🗄️ Modelos de Datos Principales
El núcleo del sistema se compone de los siguientes modelos:

► Airplane: Almacena las aeronaves, con su capacidad, modelo y distribución (filas/columnas).

► Flight: Representa los vuelos programados (origen, destino, fechas, precio base) y se vincula a un Airplane.

► Seat: Asientos individuales generados para cada avión (tipo, estado, precio extra).

► Passenger: Perfil de los clientes que compran pasajes (datos personales, contacto).

► Reservation: El vínculo central entre un Passenger, un Flight y un Seat. Contiene el estado (pendiente, pagada, cancelada).

► Ticket: El boleto final emitido (con código de barras) una vez que una reserva es confirmada y pagada.

► User: Cuentas de Django para la autenticación y administración (Staff/Superusuario).

---

## 💻 Stack Tecnológico

► Backend: Django

► API: Django REST Framework

► Documentación API: drf-spectacular (Swagger/ReDoc)

► Base de Datos: SQLite (en desarrollo)

► Frontend (Admin/UI): Bootstrap, HTML5, CSS3

---

## 👨‍💻 Desarrolladores

► Pinatti, Alejo

► López, Rebeca
