-- Script: Permitir Pagos Negativos para Puesta en Marcha
-- Fecha: 2025-01-09
-- Descripción: Modificaciones para permitir el ingreso de pagos negativos
--              para compensar saldos negativos iniciales de clientes

-- ============================================================================
-- CAMBIOS REALIZADOS
-- ============================================================================

-- 1. BACKEND (mi_app/blueprints/pagos.py)
--    - Modificada función nuevo() para permitir montos negativos
--    - Modificada función editar() para permitir montos negativos
--    - Validación de duplicados solo para montos positivos
--    - Mensajes diferenciados para pagos negativos
--    - Validación: solo bloquea montos cero, permite negativos

-- 2. FRONTEND - NUEVO PAGO (mi_app/templates/pagos/nuevo.html)
--    - Placeholder actualizado: "Ingrese el monto (puede ser negativo)"
--    - Texto explicativo sobre pagos negativos para puesta en marcha
--    - Indicador visual con badges diferenciados:
--      * ⚠️ Pago Negativo (amarillo)
--      * ✅ Pago Positivo (verde)
--    - JavaScript modificado para manejar signo negativo
--    - Validación actualizada para permitir montos negativos

-- 3. FRONTEND - EDITAR PAGO (mi_app/templates/pagos/editar.html)
--    - Mismas modificaciones que nuevo pago
--    - Indicador inicial que muestra el estado del pago existente
--    - Manejo de montos negativos en edición

-- 4. FRONTEND - ÍNDICE DE PAGOS (mi_app/templates/pagos/index.html)
--    - Indicadores visuales diferenciados en la tabla:
--      * Pagos negativos: rojo con icono de advertencia
--      * Pagos positivos: verde con icono de plus
--    - Etiqueta "Pago Negativo" para mayor claridad

-- ============================================================================
-- COMPORTAMIENTO ACTUAL
-- ============================================================================

-- ✅ PAGOS POSITIVOS:
--    - Se procesan normalmente
--    - Se muestran en verde con icono +
--    - Validación de duplicados activa
--    - Mensaje: "Pago registrado correctamente"

-- ⚠️ PAGOS NEGATIVOS:
--    - Se procesan sin restricciones
--    - Se muestran en amarillo/rojo con icono de advertencia
--    - NO hay validación de duplicados
--    - Mensaje: "Pago negativo registrado correctamente: -X CLP"
--    - Indicadores visuales claros en toda la interfaz

-- ❌ MONTO CERO:
--    - Se bloquea con mensaje: "El monto no puede ser cero"

-- ============================================================================
-- EJEMPLO DE USO
-- ============================================================================

-- Escenario: Cliente con saldo negativo inicial de -500,000 CLP
-- 
-- ANTES:
-- - No se podía ingresar pago negativo
-- - El saldo negativo permanecía sin compensar
-- 
-- AHORA:
-- - Se puede ingresar pago de -500,000 CLP
-- - Se muestra advertencia visual durante el ingreso
-- - Se registra como "Pago Negativo" en la tabla
-- - El saldo del cliente se compensa correctamente

-- ============================================================================
-- BENEFICIOS PARA PUESTA EN MARCHA
-- ============================================================================

-- 1. Flexibilidad operativa: Permite compensar saldos negativos iniciales
-- 2. Transparencia: Muestra claramente cuando un pago es negativo
-- 3. Control: El usuario puede decidir cuándo usar pagos negativos
-- 4. Auditoría: Todos los pagos negativos quedan registrados
-- 5. Recuperación: Permite ajustar saldos históricos
-- 6. UX mejorada: Indicadores visuales claros en toda la interfaz

-- ============================================================================
-- CASOS DE USO TÍPICOS
-- ============================================================================

-- 1. COMPENSACIÓN DE SALDOS NEGATIVOS INICIALES:
--    - Cliente inicia con deuda de -1,000,000 CLP
--    - Se ingresa pago de -1,000,000 CLP
--    - Resultado: Saldo queda en 0 CLP

-- 2. AJUSTE DE SALDOS HISTÓRICOS:
--    - Se descubre error en saldo anterior
--    - Se ingresa pago negativo para corregir
--    - Se mantiene trazabilidad completa

-- 3. COMPENSACIÓN DE PEDIDOS SIN PAGO:
--    - Pedido procesado sin pago previo
--    - Se ingresa pago negativo equivalente
--    - Saldo queda balanceado

-- ============================================================================
-- NOTAS IMPORTANTES
-- ============================================================================

-- - Los pagos negativos NO tienen validación de duplicados
-- - Se mantiene la integridad de los datos
-- - Las advertencias son claras y visibles
-- - El sistema sigue siendo seguro y auditable
-- - Se puede revertir fácilmente si es necesario
-- - Solo está disponible para puesta en marcha

-- ============================================================================
-- VERIFICACIÓN
-- ============================================================================

-- Para verificar que funciona correctamente:
-- 1. Intentar ingresar un pago negativo
-- 2. Verificar que se muestra advertencia amarilla
-- 3. Verificar que se procesa sin bloquear
-- 4. Verificar que aparece en la tabla con indicador rojo
-- 5. Verificar que el saldo del cliente se ajusta correctamente
-- 6. Verificar que no hay validación de duplicados para negativos 