# Estructura Propuesta de Blueprints

## **Estructura actual:**
```
mi_app/mi_app/
├── app.py (1113 líneas - TODOS los blueprints mezclados)
├── blueprints/
│   ├── __init__.py
│   ├── utilidades.py
│   └── margen.py
└── templates/
    ├── transferencias.html
    ├── pedidos.html
    ├── dashboard.html
    └── admin/
        └── *.html
```

## **Estructura propuesta:**
```
mi_app/mi_app/
├── app.py (solo configuración y registro de blueprints)
├── blueprints/
│   ├── __init__.py
│   ├── utilidades.py
│   ├── margen.py
│   ├── transferencias.py      ← NUEVO
│   ├── pedidos.py            ← NUEVO
│   ├── dashboard.py          ← NUEVO
│   └── admin.py              ← NUEVO
└── templates/
    ├── transferencias/
    │   ├── index.html
    │   ├── nuevo.html
    │   └── editar.html
    ├── pedidos/
    │   ├── index.html
    │   ├── nuevo.html
    │   └── editar.html
    ├── dashboard/
    │   ├── index.html
    │   └── detalle.html
    └── admin/
        └── *.html
```

## **Beneficios de la nueva estructura:**

### **1. Separación de responsabilidades**
- Cada blueprint maneja su propia lógica
- Código más organizado y mantenible
- Fácil de testear individualmente

### **2. Reutilización**
- Los blueprints pueden ser importados en otras aplicaciones
- Funcionalidades modulares

### **3. Escalabilidad**
- Fácil agregar nuevas funcionalidades
- Mejor gestión de dependencias

### **4. Mantenimiento**
- Cambios aislados por módulo
- Menor riesgo de conflictos

## **Plan de migración:**

### **Fase 1: Crear blueprints individuales**
1. `transferencias.py` - Gestión de transferencias
2. `pedidos.py` - Gestión de pedidos
3. `dashboard.py` - Dashboard y métricas
4. `admin.py` - Panel de administración

### **Fase 2: Reorganizar templates**
1. Crear subdirectorios por módulo
2. Mover templates a sus respectivos directorios

### **Fase 3: Limpiar app.py**
1. Eliminar código de blueprints
2. Mantener solo configuración y registro

### **Fase 4: Actualizar rutas**
1. Corregir referencias en templates
2. Actualizar imports

## **Archivos que se crearán:**

### **blueprints/transferencias.py**
- Rutas: `/transferencias/`, `/transferencias/nuevo`, `/transferencias/editar/<id>`
- Funciones: `index()`, `nuevo()`, `editar_transferencia()`
- Templates: `transferencias/index.html`, `transferencias/nuevo.html`, `transferencias/editar.html`

### **blueprints/pedidos.py**
- Rutas: `/pedidos/`, `/pedidos/nuevo`, `/pedidos/editar/<id>`
- Funciones: `index()`, `nuevo()`, `editar()`
- Templates: `pedidos/index.html`, `pedidos/nuevo.html`, `pedidos/editar.html`

### **blueprints/dashboard.py**
- Rutas: `/dashboard/`, `/dashboard/detalle/<cliente>`
- Funciones: `index()`, `detalle()`
- Templates: `dashboard/index.html`, `dashboard/detalle.html`

### **blueprints/admin.py**
- Rutas: `/admin/`, `/admin/tasa_compras`, `/admin/ingresar_usdt`, etc.
- Funciones: `index()`, `tasa_compras()`, `ingresar_usdt()`, etc.
- Templates: `admin/*.html` (mantener estructura actual) 