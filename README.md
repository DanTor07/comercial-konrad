# Comercial Konrad - Plataforma de E-Commerce

Plataforma integral de comercio electrónico diseñada para la comunidad de la Konrad Lorenz, que permite a vendedores gestionar sus suscripciones y productos, y a compradores realizar transacciones seguras con diversos métodos de pago.

## 🚀 Configuración del Proyecto

A continuación se describen los pasos necesarios para la puesta en marcha del proyecto en un entorno local:

### 1. Requisitos Previos
*   Python 3.10 o superior
*   Pip (gestor de paquetes de Python)

### 2. Preparación del Entorno
Se requiere la creación de un entorno virtual para el aislamiento de las dependencias:

```bash
# Creación del entorno virtual
python -m venv .venv

# Activación en Windows
.venv\Scripts\activate

# Activación en Linux/Mac
source .venv/bin/activate
```

### 3. Instalación de Dependencias
Ejecución de la instalación de los paquetes requeridos:

```bash
pip install django pillow
```

### 4. Configuración de Base de Datos
Ejecución de migraciones para el establecimiento de la estructura en SQLite:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Ejecución del Servidor
Inicio del servidor de desarrollo:

```bash
python manage.py runserver
```

La aplicación queda disponible en la dirección: `http://127.0.0.1:8000/`.

---

## 🛠️ Tecnologías y Arquitectura
*   **Backend:** Django 5.x (Python)
*   **Base de Datos:** SQLite3
*   **Arquitectura:** Se sigue el paradigma de **Arquitectura Limpia (Clean Architecture)** utilizando el enfoque de **Puertos y Adaptadores**, separando las reglas de negocio (Dominio) de los detalles tecnológicos (Infraestructura).

### 📐 Patrones de Diseño Implementados
El sistema integra diversos patrones de diseño para garantizar la escalabilidad y el desacoplamiento:

*   **Facade:** Utilizado en `RegistrationFacade` y `CheckoutFacade` para simplificar procesos complejos, ofreciendo una interfaz única a las vistas.
*   **Factory Method:** Implementado en la validación de perfiles de vendedores para instanciar diversos validadores según el tipo de persona.
*   **Strategy:** Aplicado en el procesamiento de pagos, permitiendo alternar dinámicamente entre PSE, Tarjeta de Crédito y Consignación Bancaria.
*   **Singleton:** Empleado en el `BAMService` para garantizar una única instancia del monitor de KPIs y en la configuración global del sistema.
*   **Observer:** Utilizado para notificar automáticamente a diversos servicios (Email, Auditoría) cuando ocurren cambios en el estado de las suscripciones.
*   **Proxy:** Implementado para interceptar y auditar la creación de productos, asegurando que solo vendedores con suscripción activa puedan publicar.
*   **Transactional Client:** Asegura la atomicidad en la persistencia de pedidos complejos y sus ítems relacionados.

---

## 🌟 Características Principales

### Funcionalidades para Vendedores
*   **Registro y Validación:** Sistema de registro con validación de antecedentes y score crediticio.
*   **Gestión de Suscripciones:** Disponibilidad de planes con pasarela integrada y actualización automática de estados.
*   **Gestión de Productos:** Catálogo con soporte para múltiples imágenes y especificaciones técnicas.

### Funcionalidades para Compradores
*   **Catálogo Dinámico:** Filtros avanzados por categoría, precio, marca y características.
*   **Pasarela Multimodal:** Procesamiento de pagos en línea, tarjetas y conciliación de archivos planos para consignaciones.
*   **Sistema de Feedback:** Registro de calificaciones (1-10) y comentarios públicos en el detalle del producto.

### Funcionalidades Administrativas (Director Comercial)
*   **BAM Dashboard:** Tablero de control con KPIs en tiempo real (Top ventas, tendencias y crecimiento semestral).
*   **Gestión de Solicitudes:** Interfaz para el procesamiento de nuevas solicitudes de vendedores.
*   **Auditoría Institucional:** Registro centralizado de acciones y errores para garantizar la transparencia.

---

## 📁 Estructura del Proyecto
*   `core/domain`: Entidades y lógica de negocio pura.
*   `core/application`: Casos de uso y coordinadores (Facades).
*   `core/infrastructure`: Adaptadores para base de datos, servicios de correo y pasarelas.
*   `core/management`: Comandos de automatización del sistema.
