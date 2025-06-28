# DOCUMENTACION DEL PROYECTO

## 1. Resumen general del proyecto

Este proyecto es una aplicación web desarrollada en Flask para la gestión integral de pagos, pedidos, transferencias y utilidades financieras. Está diseñada para ser utilizada por operadores y administradores de una empresa que requiere llevar control detallado de transacciones, saldos de clientes, reportes y operaciones de backoffice.

El sistema permite:
- Registrar y consultar pagos realizados por clientes, con validaciones de duplicidad y advertencias para montos altos.
- Gestionar pedidos y su impacto en la deuda de cada cliente.
- Visualizar dashboards con saldos, deudas y movimientos diarios.
- Administrar transferencias y utilidades, incluyendo gráficos en tiempo real y reportes.
- Mantener un historial de cambios y auditoría en las operaciones clave.
- Integrarse con Supabase como backend de base de datos y autenticación.
- Ofrecer una experiencia de usuario moderna, con validaciones en tiempo real y flujos optimizados para el trabajo diario.

El código está modularizado en blueprints, con separación clara entre backend (lógica, rutas, validaciones) y frontend (templates, estáticos). Se han implementado buenas prácticas de seguridad, manejo de zona horaria de Chile y robustez ante errores comunes.

## 2. Estructura de carpetas y archivos

La estructura del proyecto está organizada para separar claramente la lógica del backend, los recursos del frontend y los scripts auxiliares. A continuación se muestra el árbol de directorios principal y la función de cada elemento relevante:

```
mi_app/
  ├── app.py                # Archivo principal de la aplicación Flask, inicialización y configuración global
  ├── blueprints/           # Módulos funcionales (pagos, pedidos, dashboard, transferencias, utilidades, admin)
  ├── templates/            # Plantillas HTML (Jinja2) para cada módulo y base.html
  ├── static/               # Archivos estáticos: CSS, JS, imágenes, favicon, logo
  ├── requirements.txt      # Dependencias del proyecto (paquetes Python)
  ├── create_tables.sql     # Script SQL para crear las tablas en Supabase
  ├── wsgi.py               # Entrada para despliegue en servidores WSGI (PythonAnywhere, Gunicorn, etc)
  ├── extensions.py         # Inicialización de extensiones (ej. cache)
  ├── usdt_ves.py           # Script auxiliar para tasas USDT/VES (si aplica)
  ├── total_compras_gilmar.py # Script auxiliar para reportes o cálculos específicos
  ├── lock_app.py           # Script de bloqueo de la app (mantenimiento, etc)
  ├── data_tasas.csv.*      # Archivos CSV de respaldo/histórico de tasas
  ├── keys/                 # Carpeta para llaves o archivos sensibles (no versionados)
  ├── app.log               # Archivo de logs de la aplicación
  └── ...                   # Otros archivos de configuración, backups, etc.
```

**Carpetas clave:**
- `blueprints/`: Cada archivo es un módulo funcional (pagos, pedidos, dashboard, etc.), implementado como blueprint de Flask.
- `templates/`: Subcarpetas por módulo, más `base.html` y otros templates compartidos.
- `static/`: Recursos estáticos organizados en subcarpetas (`css/`, `img/`, etc.).
- `keys/`: Para llaves/API keys, no debe subirse a control de versiones.

**Archivos clave:**
- `app.py`: Punto de entrada, configuración global, registro de blueprints y filtros.
- `requirements.txt`: Lista de dependencias para instalar el entorno.
- `create_tables.sql`: Estructura de la base de datos en Supabase.
- `wsgi.py`: Para despliegue en servidores compatibles con WSGI.

## 3. Backend (Flask, Blueprints, lógica principal)

El backend está construido sobre Flask, utilizando el patrón de blueprints para modularizar la lógica de cada área funcional. Esto permite mantener el código organizado, escalable y fácil de mantener.

### **3.1 app.py: núcleo de la aplicación**
- Inicializa la aplicación Flask y configura la zona horaria de Chile.
- Carga variables de entorno y configura el logging.
- Inicializa y configura el sistema de caché (`flask_caching`).
- Registra todos los blueprints (pagos, pedidos, dashboard, transferencias, utilidades, admin).
- Define filtros personalizados para Jinja2 (formateo de fechas, montos, etc).
- Implementa decoradores de seguridad (`login_required`, `user_allowed`).
- Gestiona la conexión con Supabase (base de datos y autenticación).

### **3.2 Blueprints principales**
Cada blueprint es un archivo Python en la carpeta `blueprints/` y representa un módulo funcional independiente:

- **pagos.py**: Gestión de pagos (registro, edición, eliminación, validaciones, historial).
- **pedidos.py**: Gestión de pedidos (registro, edición, eliminación, cálculo de deuda, historial).
- **dashboard.py**: Lógica del dashboard principal, cálculo de saldos, deudas y resumen diario por cliente.
- **transferencias.py**: Gestión de transferencias entre cuentas, filtros y reportes.
- **utilidades.py**: Funciones auxiliares, reportes, gráficos en tiempo real, lógica de reinicio y actualización de datos.
- **admin.py**: Funciones administrativas, gestión de usuarios, tasas, compras/ventas USDT, reportes avanzados.
- **clientes.py**: Gestión de clientes (CRUD básico, visualización de pagadores asociados).

Cada blueprint define sus propias rutas (`@route`), lógica de validación, acceso a la base de datos y renderizado de templates.

### **3.3 Organización de la lógica**
- **Validaciones y seguridad:**
  - Decoradores para login y permisos de usuario.
  - Validaciones de datos en formularios y en el backend.
- **Gestión de zona horaria:**
  - Todas las operaciones de fecha/hora usan la zona de Chile (`pytz.timezone('America/Santiago')`).
- **Historial y auditoría:**
  - Cambios relevantes (pagos, pedidos) quedan registrados en tablas de historial.
- **Caché:**
  - Se utiliza `flask_caching` para optimizar el rendimiento en vistas de dashboard y reportes.
- **Integración con Supabase:**
  - Todas las operaciones CRUD se realizan a través del cliente Supabase.

## 4. Frontend (Jinja2, Bootstrap, UX, modales, alertas, feedback visual, scripts)

El frontend utiliza Jinja2 como motor de templates, Bootstrap 5 para el diseño responsivo y componentes interactivos, y JavaScript para la funcionalidad dinámica.

### **4.1 Estructura de templates**
- **base.html**: Template base con la estructura HTML común, incluye Bootstrap, CSS personalizado y scripts.
- **Templates específicos por módulo:**
  - `pagos/`: index.html, nuevo.html, editar.html
  - `pedidos/`: index.html, nuevo.html, editar.html
  - `transferencias/`: index.html, nuevo.html, editar.html
  - `dashboard/`: index.html
  - `utilidades/`: utilidades.html, grafico.html, compras_resultado.html
  - `admin/`: admin.html, compras_utilidades.html, etc.

### **4.2 Componentes visuales principales**
- **Navbar responsivo**: Navegación principal con menú desplegable para móviles.
- **Tablas con filtros**: Tablas Bootstrap con filtros de búsqueda y ordenamiento.
- **Formularios**: Formularios con validación HTML5 y feedback visual.
- **Modales Bootstrap**: Para confirmaciones, advertencias y formularios dinámicos.
- **Alertas**: Sistema de alertas para mostrar mensajes de éxito, error o advertencia.
- **Cards informativas**: Para mostrar resúmenes y estadísticas en el dashboard.

### **4.3 Interacciones y UX**
- **Validación en tiempo real**: Los formularios validan datos mientras el usuario escribe.
- **Confirmaciones**: Modales de confirmación para acciones críticas (eliminar, pagos altos, duplicados).
- **Feedback visual**: Indicadores de carga, estados de botones, mensajes de confirmación.
- **Persistencia de datos**: Los formularios mantienen los datos tras advertencias o errores.
- **Responsive design**: La interfaz se adapta a diferentes tamaños de pantalla.

### **4.4 Scripts JavaScript**
- **scripts.html**: Archivo con funciones JavaScript comunes:
  - Validación de formularios
  - Manejo de modales
  - Filtros de tablas
  - Confirmaciones de acciones
  - Actualización dinámica de datos
- **Funciones específicas por módulo:**
  - Dashboard: Actualización automática de datos
  - Utilidades: Gráficos en tiempo real
  - Pagos: Validación de montos y fechas
  - Pedidos: Cálculo automático de totales

### **4.5 CSS personalizado**
- **styles.css**: Estilos personalizados para:
  - Colores y temas de la aplicación
  - Animaciones y transiciones
  - Responsive design
  - Componentes específicos (tablas, formularios, modales)

### Nota importante sobre la actualización del gráfico

A partir de la última mejora, el endpoint `/grafico_datos` recarga el archivo CSV desde disco en cada petición. Esto garantiza que el gráfico de precios USDT/VES siempre muestre los datos más recientes, incluso si el archivo se modifica por fuera o el proceso Flask lleva mucho tiempo corriendo. Así se evita cualquier problema de visualización causado por desincronización entre la memoria del proceso y el archivo de datos.

Esta lógica asegura que:
- El gráfico siempre refleja el estado real del archivo de datos.
- No es necesario reiniciar el proceso Flask para ver los datos nuevos.
- Se soluciona el problema de que el gráfico no se actualizaba tras el reinicio diario o cambios externos en el CSV.

## 5. Base de datos (Supabase, tablas, relaciones, índices, triggers)

La aplicación utiliza Supabase como backend de base de datos, que proporciona una capa de abstracción sobre PostgreSQL con funcionalidades adicionales como autenticación, almacenamiento de archivos y APIs en tiempo real.

### **5.1 Configuración de Supabase**
- **URL y API Key**: Configuradas en variables de entorno (`SUPABASE_URL`, `SUPABASE_KEY`).
- **Cliente Python**: Utiliza la librería `supabase` para todas las operaciones CRUD.
- **Autenticación**: Integrada con el sistema de login de la aplicación.
- **Zona horaria**: Configurada para Chile (`America/Santiago`).

### **5.2 Tablas principales**

#### **pagos**
- **Propósito**: Almacena todos los pagos realizados por los clientes.
- **Campos principales**:
  - `id`: Identificador único (serial)
  - `cliente_id`: Referencia al cliente
  - `monto`: Cantidad del pago
  - `fecha`: Fecha y hora del pago
  - `metodo_pago`: Método utilizado (efectivo, transferencia, etc.)
  - `observaciones`: Notas adicionales
  - `created_at`: Timestamp de creación
  - `updated_at`: Timestamp de última modificación

#### **pedidos**
- **Propósito**: Registra los pedidos realizados por los clientes.
- **Campos principales**:
  - `id`: Identificador único
  - `cliente_id`: Referencia al cliente
  - `descripcion`: Descripción del pedido
  - `monto`: Monto total del pedido
  - `fecha`: Fecha del pedido
  - `estado`: Estado del pedido (pendiente, completado, etc.)
  - `created_at`, `updated_at`: Timestamps

#### **clientes**
- **Propósito**: Información de los clientes del sistema, poblada desde la tabla pagadores.
- **Campos principales**:
  - `id`: Identificador único
  - `nombre`: Nombre del cliente (extraído del campo 'cliente' de pagadores)
  - `created_at`: Timestamp de creación
- **Nota**: Esta tabla se puebla automáticamente con los clientes únicos de la tabla `pagadores` mediante el script `poblar_clientes.py`.

#### **pagadores**
- **Propósito**: Información detallada de los pagadores asociados a cada cliente.
- **Campos principales**:
  - `id`: Identificador único
  - `cliente`: Nombre del cliente (relacionado con tabla clientes)
  - `nombre`: Nombre del pagador
  - `rut`: RUT del pagador
  - `email`: Email del pagador

#### **transferencias**
- **Propósito**: Registra transferencias entre cuentas o entidades.
- **Campos principales**:
  - `id`: Identificador único
  - `origen`: Cuenta de origen
  - `destino`: Cuenta de destino
  - `monto`: Cantidad transferida
  - `fecha`: Fecha de la transferencia
  - `descripcion`: Descripción de la transferencia

#### **historial_pagos**
- **Propósito**: Auditoría de cambios en pagos.
- **Campos principales**:
  - `id`: Identificador único
  - `pago_id`: Referencia al pago modificado
  - `accion`: Tipo de acción (crear, editar, eliminar)
  - `datos_anteriores`: JSON con datos previos
  - `datos_nuevos`: JSON con datos nuevos
  - `usuario_id`: Usuario que realizó el cambio
  - `fecha`: Timestamp del cambio

#### **historial_pedidos**
- **Propósito**: Auditoría de cambios en pedidos.
- **Estructura similar a historial_pagos**

### **5.3 Relaciones entre tablas**
- **pagos → clientes**: Relación muchos a uno (un cliente puede tener múltiples pagos).
- **pedidos → clientes**: Relación muchos a uno (un cliente puede tener múltiples pedidos).
- **pagadores → clientes**: Relación muchos a uno (un cliente puede tener múltiples pagadores).
- **historial_pagos → pagos**: Relación muchos a uno (un pago puede tener múltiples entradas de historial).
- **historial_pedidos → pedidos**: Relación muchos a uno.

### **5.4 Índices y optimización**
- **Índices principales**:
  - `pagos(cliente_id, fecha)`: Para consultas de pagos por cliente y período.
  - `pedidos(cliente_id, fecha)`: Para consultas de pedidos por cliente y período.
  - `pagos(fecha)`: Para consultas de pagos por fecha.
  - `pedidos(fecha)`: Para consultas de pedidos por fecha.
- **Índices de auditoría**:
  - `historial_pagos(pago_id, fecha)`: Para consultas de historial.
  - `historial_pedidos(pedido_id, fecha)`: Para consultas de historial.

### **5.5 Triggers y funciones**
- **Triggers de auditoría**: Se ejecutan automáticamente para registrar cambios en pagos y pedidos.
- **Función de cálculo de saldo**: Calcula el saldo actual de un cliente basado en pagos y pedidos.
- **Función de validación**: Valida la integridad de los datos antes de insertar/actualizar.
- **Triggers de sincronización clientes-pagadores**: Mantienen sincronizadas las tablas `clientes` y `pagadores`:
  - Al crear un cliente → se crea automáticamente un pagador
  - Al crear un pagador → se crea automáticamente el cliente si no existe
  - Al actualizar un cliente → se actualizan todos sus pagadores
  - Al eliminar un cliente → se eliminan todos sus pagadores

### **5.6 Archivo create_tables.sql**
Contiene la definición completa de todas las tablas, índices, triggers y funciones necesarias para el funcionamiento del sistema.

## 6. Relaciones, funciones y flujos (cómo se conectan los módulos, flujos de datos, validaciones cruzadas)

### **6.1 Flujo principal de datos**
1. **Registro de pedidos** → **Cálculo de deuda** → **Dashboard actualizado**
2. **Registro de pagos** → **Reducción de deuda** → **Dashboard actualizado**
3. **Transferencias** → **Ajuste de saldos** → **Reportes actualizados**

### **6.2 Conexiones entre módulos**

#### **Dashboard ↔ Pagos/Pedidos**
- El dashboard calcula saldos en tiempo real basándose en pagos y pedidos.
- Los cambios en pagos o pedidos actualizan automáticamente las métricas del dashboard.
- Sistema de caché para optimizar el rendimiento de consultas frecuentes.

#### **Pagos ↔ Historial**
- Cada modificación en pagos genera una entrada en `historial_pagos`.
- El historial permite auditoría completa de cambios.
- Validaciones para prevenir duplicados y pagos sospechosos.

#### **Pedidos ↔ Historial**
- Similar al sistema de pagos, cada cambio genera entrada en `historial_pedidos`.
- Permite rastrear modificaciones en pedidos y sus justificaciones.

#### **Utilidades ↔ Dashboard**
- Las utilidades pueden generar reportes basados en datos del dashboard.
- Gráficos en tiempo real que se actualizan con cambios en pagos/pedidos.

#### **Clientes ↔ Pagadores**
- El módulo de clientes muestra la lista de clientes únicos extraídos de la tabla pagadores.
- Permite visualizar los pagadores asociados a cada cliente.
- Proporciona funcionalidad CRUD básica para gestión de clientes.

### **6.3 Validaciones cruzadas**
- **Validación de saldo**: No se permite registrar pagos que excedan la deuda total.
- **Validación de fechas**: Los pagos no pueden ser anteriores a los pedidos.
- **Validación de duplicados**: Sistema de detección de pagos duplicados por monto y fecha.
- **Validación de montos**: Alertas para pagos inusualmente altos.

### **6.4 Funciones compartidas**
- **Cálculo de saldo**: Función común utilizada por dashboard y reportes.
- **Formateo de fechas**: Filtros Jinja2 para mostrar fechas en formato chileno.
- **Validación de permisos**: Decoradores reutilizables para control de acceso.

## 7. Puntos críticos y consideraciones importantes

### **7.1 Gestión de zona horaria**
- **Crítico**: Todas las operaciones de fecha/hora deben usar zona horaria de Chile.
- **Implementación**: Uso de `pytz.timezone('America/Santiago')` en todas las operaciones.
- **Consideración**: Cambios de horario de verano/invierno pueden afectar cálculos.

### **7.2 Integridad de datos**
- **Validaciones**: Doble validación (frontend y backend) para datos críticos.
- **Transacciones**: Uso de transacciones de base de datos para operaciones complejas.
- **Backup**: Sistema de respaldo automático de datos críticos.

### **7.3 Seguridad**
- **Autenticación**: Sistema de login requerido para todas las operaciones.
- **Autorización**: Control de acceso basado en roles de usuario.
- **Validación de entrada**: Sanitización de datos de entrada para prevenir inyecciones.

### **7.4 Rendimiento**
- **Caché**: Implementación de caché para consultas frecuentes (dashboard, reportes).
- **Índices**: Índices optimizados en base de datos para consultas rápidas.
- **Paginación**: Paginación en listas largas para evitar sobrecarga.

### **7.5 Manejo de errores**
- **Logging**: Sistema de logging para rastrear errores y operaciones críticas.
- **Mensajes de usuario**: Mensajes claros y útiles para el usuario final.
- **Recuperación**: Mecanismos de recuperación ante fallos del sistema.

### **7.6 Escalabilidad**
- **Arquitectura modular**: Diseño que permite agregar nuevos módulos fácilmente.
- **Base de datos**: Diseño que soporta crecimiento en volumen de datos.
- **Código mantenible**: Estructura clara y documentada para facilitar mantenimiento.

### **7.7 Consideraciones de negocio**
- **Auditoría**: Sistema completo de auditoría para cumplimiento regulatorio.
- **Reportes**: Capacidad de generar reportes detallados para análisis de negocio.
- **Flexibilidad**: Sistema adaptable a cambios en procesos de negocio.

## 8. Despliegue (configuración, variables de entorno, PythonAnywhere, mantenimiento)

### **8.1 Configuración de entorno**
- **Python 3.9+**: Versión requerida para el proyecto.
- **Dependencias**: Instaladas via `pip install -r requirements.txt`.
- **Entorno virtual**: Uso de `venv` para aislar dependencias del proyecto.

### **8.2 Variables de entorno**
Archivo `.env` con las siguientes variables:
```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-api-key-secreta
SECRET_KEY=clave-secreta-flask
FLASK_ENV=production
TZ=America/Santiago
```

### **8.3 Despliegue en PythonAnywhere**
1. **Crear cuenta**: Registro en PythonAnywhere.com
2. **Subir código**: Git clone o upload del proyecto
3. **Configurar entorno virtual**:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.9 mi_app_env
   pip install -r requirements.txt
   ```
4. **Configurar WSGI**: Editar archivo WSGI para apuntar a la aplicación
5. **Configurar variables de entorno**: En la configuración de PythonAnywhere
6. **Configurar dominio**: Asignar dominio personalizado si es necesario

### **8.4 Archivos de configuración**
- **wsgi.py**: Configuración para servidores WSGI
- **requirements.txt**: Lista de dependencias Python
- **.env**: Variables de entorno (no subir a Git)
- **app.log**: Archivo de logs de la aplicación
- **triggers_para_supabase.sql**: Script SQL con triggers de sincronización entre clientes y pagadores

### **8.5 Mantenimiento**
- **Logs**: Revisión periódica de `app.log` para errores
- **Backups**: Respaldos automáticos de la base de datos Supabase
- **Actualizaciones**: Actualización regular de dependencias
- **Monitoreo**: Verificación de rendimiento y disponibilidad

### **8.6 Scripts de mantenimiento**
- **grafico_updater.py**: Script para actualización automática de datos
- **poblar_clientes.py**: Script para poblar la tabla clientes con datos únicos de pagadores
- **Reinicio diario**: Configuración de cron jobs para reinicio automático
- **Limpieza de caché**: Limpieza periódica de archivos temporales

### Actualización automática del gráfico y configuración en PythonAnywhere

El gráfico de precios USDT/VES se actualiza automáticamente en la web gracias a dos mecanismos:

1. **Actualización periódica en el frontend:**
   - El navegador consulta el endpoint `/utilidades/grafico_datos` cada X segundos (configurable en la interfaz) para obtener los datos más recientes.
   - Esto se refleja en los logs del servidor como múltiples peticiones GET a `/utilidades/grafico_datos`.
   - Si el archivo CSV cambia, el gráfico se actualiza en tiempo real.

2. **Actualización automática del CSV en segundo plano:**
   - El script `grafico_updater.py` debe estar corriendo siempre en el servidor para consultar Binance y guardar los datos en el CSV, sin depender de que alguien esté en la web.
   - Si el script no está activo, el CSV solo se actualiza cuando alguien visita la página del gráfico.

#### Procedimiento para configurar el script como Always-on task en PythonAnywhere

1. **Sube tu código a PythonAnywhere** y asegúrate de que el entorno virtual y las dependencias estén instaladas.
2. **Edita el import en `grafico_updater.py`** (si es necesario) para que funcione en el entorno de producción:
   ```python
   from mi_app.blueprints.utilidades import actualizar_datos
   ```
3. **Accede al panel de PythonAnywhere** y ve a la sección "Tasks" o "Always-on tasks".
4. **Agrega una nueva tarea Always-on** con el siguiente comando (ajusta la ruta según tu estructura):
   ```bash
   /home/tu_usuario/.virtualenvs/tu_venv/bin/python /home/tu_usuario/tu_proyecto/mi_app/grafico_updater.py
   ```
   - Cambia `tu_usuario`, `tu_venv` y `tu_proyecto` por los nombres correspondientes a tu cuenta y proyecto.
5. **Guarda la tarea y actívala.** PythonAnywhere se encargará de reiniciarla automáticamente si se detiene.
6. **Verifica que el CSV se actualiza periódicamente** y que el gráfico en la web muestra datos en tiempo real.

## 9. Glosario

### **9.1 Términos técnicos**
- **Blueprint**: Módulo de Flask que organiza rutas y lógica relacionada
- **Supabase**: Backend-as-a-Service que proporciona base de datos PostgreSQL
- **WSGI**: Interfaz estándar entre servidores web y aplicaciones Python
- **Jinja2**: Motor de templates para Python
- **CRUD**: Create, Read, Update, Delete (operaciones básicas de base de datos)
- **API**: Interfaz de programación de aplicaciones
- **Caché**: Almacenamiento temporal para mejorar rendimiento
- **Trigger**: Función que se ejecuta automáticamente en la base de datos

### **9.2 Términos de negocio**
- **Pago**: Transacción donde un cliente abona dinero por servicios/productos
- **Pedido**: Solicitud de productos o servicios por parte de un cliente
- **Deuda**: Monto pendiente de pago por pedidos realizados
- **Saldo**: Diferencia entre pagos realizados y deuda total
- **Transferencia**: Movimiento de dinero entre cuentas o entidades
- **Cliente**: Persona o entidad que realiza pedidos y pagos
- **Historial**: Registro de cambios y modificaciones en transacciones
- **Dashboard**: Panel principal con resumen de métricas y estado del negocio

### **9.3 Términos de la aplicación**
- **Módulo**: Área funcional específica (pagos, pedidos, dashboard, etc.)
- **Template**: Archivo HTML con estructura y diseño de una página
- **Ruta**: URL que accede a una funcionalidad específica
- **Formulario**: Interfaz para ingresar o modificar datos
- **Modal**: Ventana emergente para confirmaciones o formularios
- **Validación**: Verificación de datos antes de procesarlos
- **Auditoría**: Registro de cambios para trazabilidad
- **Reporte**: Documento con información resumida del negocio

### Selector de clientes con búsqueda avanzada (Select2)

En el módulo de transferencias, el selector de clientes utiliza la librería [Select2](https://select2.org/getting-started/basic-usage) para ofrecer una experiencia moderna y eficiente:

- **Campo de búsqueda siempre visible:** Al abrir el selector, aparece un input para buscar clientes de forma instantánea.
- **Búsqueda local:** El filtrado se realiza en tiempo real sobre los clientes activos mostrados en la lista.
- **Diseño limpio y profesional:** El selector replica la experiencia del ejemplo oficial de Select2, facilitando la selección incluso con listas largas.
- **Solo clientes activos:** Para evitar saturar la interfaz, solo se muestran los clientes activos o relevantes en la lista desplegable.

**Configuración técnica:**
- El `<select>` tiene la clase `js-example-basic-single`.
- Se inicializa con:
  ```js
  $('.js-example-basic-single').select2({
    minimumResultsForSearch: 0,
    width: '100%',
    placeholder: 'Buscar cliente...'
  });
  ```
- Se incluyen los archivos CSS y JS de Select2 desde CDN.

Esto garantiza una experiencia de usuario ágil, moderna y escalable para la gestión de transferencias y asignación de pagos.

## Foco automático en campos Select2 (Transferencias)

**¿Qué hace esta mejora?**
- Cuando abres el filtro de cliente o cualquier selector de cliente en la tabla de transferencias, el campo de búsqueda de Select2 recibe el foco automáticamente.
- Así puedes empezar a escribir el nombre del cliente sin tener que hacer un clic extra en el campo de búsqueda.

**¿Dónde se aplica?**
- En el filtro de cliente del panel de filtros (arriba de la tabla).
- En todos los selectores de cliente de la columna "Acciones" de la tabla de transferencias (para asignar pago).

**¿Cómo funciona?**
Se añadió el siguiente código JavaScript en el template `transferencias/index.html`:

```javascript
// Foco automático en el campo de búsqueda al abrir cualquier select2 de cliente
$(document).on('select2:open', function(e) {
  setTimeout(function() {
    document.querySelector('.select2-container--open .select2-search__field').focus();
  }, 0);
});
```

- Este código escucha el evento `select2:open` en cualquier select2 de la página.
- Cuando se abre un select2, automáticamente pone el foco en el campo de búsqueda interno de Select2.

**Ventajas para el usuario**
- Ahorra clics: No necesitas hacer clic extra para empezar a escribir.
- Más rápido: Puedes filtrar clientes de inmediato, tanto en el filtro principal como en la tabla.
- Consistente: Funciona en todos los select2 de clientes de la sección de transferencias.

--- 