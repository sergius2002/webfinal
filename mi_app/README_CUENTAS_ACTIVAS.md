# Módulo de Cuentas Activas

Este módulo permite gestionar las cuentas bancarias activas del sistema, proporcionando control sobre múltiples cuentas asociadas a diferentes bancos.

## 🏗️ Estructura del Módulo

### Tabla de Base de Datos: `cuentas_activas`

**Campos:**
- `id` - Identificador único (SERIAL PRIMARY KEY)
- `banco` - Nombre del banco (VARCHAR(100))
- `numero_cuenta` - Número de cuenta bancaria (BIGINT)
- `cedula` - Cédula de identidad del titular (VARCHAR(20))
- `nombre_titular` - Nombre completo del titular (VARCHAR(200))
- `pais` - País donde está registrada la cuenta (VARCHAR(50), default: 'Venezuela')
- `activa` - Estado de la cuenta (BOOLEAN, default: TRUE)
- `usuario_creacion` - Email del usuario que creó el registro
- `usuario_modificacion` - Email del usuario que modificó el registro
- `created_at` - Timestamp de creación
- `updated_at` - Timestamp de última modificación

### Archivos Creados

1. **`CREATE_CUENTAS_ACTIVAS.sql`** - Script SQL para crear la tabla
2. **`mi_app/blueprints/cuentas_activas.py`** - Blueprint con la lógica del módulo
3. **`mi_app/templates/admin/cuentas_activas/`** - Plantillas HTML:
   - `index.html` - Lista de cuentas activas
   - `nuevo.html` - Formulario para crear nueva cuenta
   - `editar.html` - Formulario para editar cuenta existente
4. **`crear_tabla_cuentas_activas.py`** - Script para crear la tabla automáticamente

## 🚀 Instalación y Configuración

### Paso 1: Crear la Tabla en Supabase

**Opción A: Automática (Recomendada)**
```bash
cd mi_app
python crear_tabla_cuentas_activas.py
```

**Opción B: Manual**
1. Ve al panel de Supabase
2. Abre el SQL Editor
3. Ejecuta el contenido del archivo `CREATE_CUENTAS_ACTIVAS.sql`

### Paso 2: Verificar la Instalación

1. Reinicia la aplicación Flask
2. Accede al módulo de administración
3. Verifica que aparece "Cuentas Activas" en el menú lateral

## 📋 Funcionalidades

### ✅ Gestión Completa de Cuentas

- **Crear** nuevas cuentas activas
- **Editar** información de cuentas existentes
- **Desactivar** cuentas (marcar como inactivas)
- **Activar** cuentas previamente desactivadas
- **Visualizar** todas las cuentas en una tabla organizada

### 🔒 Seguridad

- Acceso restringido solo a usuarios administradores
- Validación de datos en frontend y backend
- Auditoría de cambios (usuario y timestamp)
- Prevención de duplicados de números de cuenta

### 📊 Información Mostrada

- **Resumen estadístico**: Total de cuentas, cuentas activas, bancos únicos
- **Tabla detallada** con todas las cuentas
- **Estado visual** (activa/inactiva) con badges
- **Acciones rápidas** (editar, activar/desactivar)

## 🎯 Uso del Módulo

### Acceso al Módulo

1. Inicia sesión como administrador
2. Ve al "Módulo Restringido"
3. Haz clic en "Cuentas Activas" en el menú lateral

### Agregar Nueva Cuenta

1. Haz clic en "Nueva Cuenta"
2. Completa el formulario:
   - **Banco**: Nombre del banco (ej: Banesco, Mercantil)
   - **Número de Cuenta**: Número completo de la cuenta
   - **Cédula**: Cédula del titular (formato: V-12345678)
   - **Nombre del Titular**: Nombre completo
   - **País**: País donde está registrada la cuenta
   - **Estado**: Marca si la cuenta está activa
3. Haz clic en "Guardar Cuenta"

### Editar Cuenta Existente

1. En la lista de cuentas, haz clic en el ícono de editar (✏️)
2. Modifica los campos necesarios
3. Haz clic en "Actualizar Cuenta"

### Desactivar/Activar Cuenta

- **Desactivar**: Haz clic en el ícono de ban (🚫)
- **Activar**: Haz clic en el ícono de check (✅)

## 🔧 Integración con Otros Módulos

### Futuras Mejoras

1. **Integración con Binance**: Asociar transacciones de Binance con cuentas específicas
2. **Filtros por banco**: Filtrar transacciones por cuenta bancaria
3. **Reportes**: Generar reportes por cuenta
4. **API**: Endpoint para obtener cuentas activas en formato JSON

### API Endpoint Disponible

```
GET /cuentas-activas/api/cuentas
```

Retorna todas las cuentas activas en formato JSON:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "banco": "Banesco",
      "numero_cuenta": 12345678901234567890,
      "cedula": "V-12345678",
      "nombre_titular": "Juan Pérez",
      "pais": "Venezuela",
      "activa": true
    }
  ]
}
```

## 🐛 Solución de Problemas

### Error: "No tienes permisos para acceder a esta sección"

- Verifica que tu usuario tenga rol de administrador
- Asegúrate de estar en la tabla `superusuarios` de Supabase

### Error: "Ya existe una cuenta con ese número"

- Verifica que el número de cuenta no esté duplicado
- Puedes buscar en la tabla para encontrar cuentas existentes

### Error: "Tabla cuentas_activas no existe"

- Ejecuta el script de creación de tabla
- Verifica que el SQL se ejecutó correctamente en Supabase

## 📝 Notas Técnicas

### Validaciones Implementadas

- **Número de cuenta**: Solo números, único en el sistema
- **Cédula**: Formato V-12345678 o solo números
- **Campos obligatorios**: Banco, número de cuenta, cédula, nombre del titular
- **Prevención de duplicados**: Verificación automática de números de cuenta

### Índices de Base de Datos

- `idx_cuentas_activas_banco` - Para búsquedas por banco
- `idx_cuentas_activas_cedula` - Para búsquedas por cédula
- `idx_cuentas_activas_activa` - Para filtrar por estado

### Triggers

- `update_cuentas_activas_updated_at` - Actualiza automáticamente el timestamp de modificación

## 🎉 ¡Listo!

El módulo de Cuentas Activas está completamente implementado y listo para usar. Ahora puedes gestionar múltiples cuentas bancarias desde tu aplicación de manera organizada y segura. 