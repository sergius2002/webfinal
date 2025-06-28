# Documentación: Validación de CLP Máximo por Cliente

## Resumen
Se ha implementado un sistema completo de validación y monitoreo para controlar el límite máximo de CLP que puede tener cada cliente al crear nuevos pedidos. Esto ayuda a prevenir errores tipográficos, establecer límites de crédito por cliente y monitorear el estado de los límites en tiempo real.

## Funcionalidades Implementadas

### 1. Base de Datos
- **Nueva columna**: `clp_maximo` en la tabla `clientes`
- **Tipo**: `DECIMAL(15,2)` - Permite montos grandes con 2 decimales
- **Valor por defecto**: `0.00` (sin límite)
- **Índice**: Creado para optimizar consultas

### 2. Formulario de Nuevo Pedido
- **Cálculo automático**: CLP = BRS / Tasa
- **Validación en tiempo real**: Muestra advertencia si se excede el límite
- **Modal de confirmación**: Permite continuar o cancelar si hay exceso
- **Información visual**: Muestra el límite del cliente seleccionado

### 3. Gestión de Clientes
- **Formulario de nuevo cliente**: Campo para establecer CLP máximo
- **Formulario de edición**: Permite modificar el CLP máximo
- **Tabla de clientes**: Muestra el CLP máximo de cada cliente
- **Valor 0**: Se interpreta como "Sin límite"

### 4. Monitoreo de Límites (NUEVO)
- **Panel de resumen**: Estadísticas generales de límites
- **Tabla mejorada**: Columnas de CLP Total y Estado
- **Advertencias visuales**: Filas en rojo para clientes que superan límite
- **Filtros avanzados**: Filtrar por estado de límites
- **Cálculo automático**: CLP total acumulado por cliente

### 5. API Backend
- **Nueva ruta**: `/pedidos/clp_maximo/<cliente>` 
- **Método**: GET
- **Respuesta**: JSON con el CLP máximo del cliente
- **Autenticación**: Requiere login

## Flujo de Validación

### 1. Selección de Cliente
```
Usuario selecciona cliente → Sistema obtiene CLP máximo → Muestra límite en interfaz
```

### 2. Ingreso de BRS y Tasa
```
Usuario ingresa BRS y Tasa → Sistema calcula CLP automáticamente → Valida contra límite
```

### 3. Validación de Límite
```
Si CLP > CLP máximo:
  - Muestra advertencia en tiempo real
  - Al enviar formulario, muestra modal de confirmación
  - Usuario puede continuar o cancelar
```

### 4. Modal de Confirmación
```
Modal muestra:
- CLP Calculado
- Límite del Cliente  
- Exceso (diferencia)
- Botones: Cancelar / Continuar de todas formas
```

## Monitoreo de Límites (NUEVO)

### Panel de Resumen
```
Muestra estadísticas en tiempo real:
- Clientes con Límite (total)
- Dentro del Límite (verde)
- Límite Superado (rojo)
```

### Tabla de Clientes Mejorada
```
Nuevas columnas:
- CLP Máximo: Límite establecido
- CLP Total: Suma de todos los pedidos
- Estado: Badge con estado actual
  - 🟢 Dentro del límite + disponible
  - 🔴 ¡LÍMITE SUPERADO! + exceso
  - ⚪ Sin límite
```

### Filtros Avanzados
```
Botones de filtro:
- Todos los clientes
- Solo clientes con límite
- Solo clientes que han superado límite
- Solo clientes dentro del límite
```

## Archivos Modificados

### Backend
- `mi_app/mi_app/blueprints/pedidos.py`
  - Nueva ruta `/clp_maximo/<cliente>`
  - Función `obtener_clp_maximo()`

- `mi_app/mi_app/blueprints/clientes.py`
  - Actualizada función `nuevo()` para manejar `clp_maximo`
  - Actualizada función `editar()` para manejar `clp_maximo`
  - Actualizada función `index()` para calcular CLP total y estado
  - Cálculo automático de límites superados

### Frontend
- `mi_app/mi_app/templates/pedidos/nuevo.html`
  - Campo de CLP calculado automáticamente
  - Validación en tiempo real
  - Modal de advertencia por exceso
  - Cálculo automático: CLP = BRS / Tasa

- `mi_app/mi_app/templates/clientes/nuevo.html`
  - Campo para establecer CLP máximo

- `mi_app/mi_app/templates/clientes/editar.html`
  - Campo para modificar CLP máximo

- `mi_app/mi_app/templates/clientes/index.html`
  - Panel de resumen con estadísticas
  - Nuevas columnas: CLP Total y Estado
  - Filtros avanzados por estado
  - Advertencias visuales (filas rojas)
  - JavaScript para filtros interactivos

### Base de Datos
- `mi_app/agregar_clp_maximo_clientes.sql`
  - Script para agregar columna `clp_maximo`
  - Índice para optimización
  - Comentarios explicativos

## Ejemplo de Uso

### Escenario 1: Cliente con Límite
```
Cliente: "Empresa ABC"
CLP Máximo: 1,000,000 CLP
CLP Total Actual: 800,000 CLP
Estado: 🟢 Dentro del límite (200,000 CLP disponible)

Si usuario ingresa pedido de 300,000 CLP:
- CLP total sería: 1,100,000 CLP
- Exceso: 100,000 CLP
- Sistema muestra advertencia y modal de confirmación
```

### Escenario 2: Cliente que ya Superó Límite
```
Cliente: "Empresa XYZ"
CLP Máximo: 500,000 CLP
CLP Total Actual: 600,000 CLP
Estado: 🔴 ¡LÍMITE SUPERADO! (100,000 CLP de exceso)

En la tabla aparece:
- Fila en color rojo
- Badge rojo con advertencia
- Exceso mostrado claramente
```

### Escenario 3: Cliente Sin Límite
```
Cliente: "Empresa DEF"
CLP Máximo: 0 (sin límite)
CLP Total Actual: 2,500,000 CLP
Estado: ⚪ Sin límite

Usuario puede ingresar cualquier monto sin restricciones
```

## Beneficios

1. **Prevención de errores**: Evita errores tipográficos en montos grandes
2. **Control de crédito**: Permite establecer límites por cliente
3. **Transparencia**: Muestra claramente los límites y cálculos
4. **Flexibilidad**: Permite continuar si es necesario (con confirmación)
5. **Experiencia de usuario**: Validación en tiempo real sin recargar página
6. **Monitoreo en tiempo real**: Vista general del estado de todos los límites
7. **Filtros inteligentes**: Fácil identificación de clientes problemáticos
8. **Advertencias visuales**: Identificación inmediata de límites superados

## Instalación

1. **Ejecutar script SQL**:
   ```sql
   -- Conectarse a Supabase y ejecutar:
   mi_app/agregar_clp_maximo_clientes.sql
   ```

2. **Reiniciar aplicación**:
   ```bash
   # Los cambios en el código se aplican automáticamente
   ```

3. **Configurar límites**:
   - Ir a Clientes → Editar cada cliente
   - Establecer CLP máximo según necesidades

4. **Monitorear estado**:
   - Ver panel de resumen en la página de clientes
   - Usar filtros para identificar clientes problemáticos
   - Revisar advertencias visuales en la tabla

## Notas Técnicas

- **Cálculo**: CLP = BRS / Tasa (división, no multiplicación)
- **Validación**: Se ejecuta tanto en frontend como backend
- **Persistencia**: Los límites se guardan en la base de datos
- **Rendimiento**: Índice creado para consultas rápidas
- **Compatibilidad**: Funciona con clientes existentes (CLP máximo = 0)
- **Cálculo de totales**: Suma automática de todos los pedidos no eliminados
- **Filtros**: Funcionan en combinación con búsqueda por nombre
- **Responsive**: Interfaz adaptada para móviles y desktop 