-- Script: Permitir Saldos Negativos en Flujo de Caja
-- Fecha: 2025-01-09
-- Descripción: Modificaciones para permitir que los pedidos se procesen incluso cuando
--              la cuenta no tiene saldo suficiente, reflejando saldos negativos

-- ============================================================================
-- CAMBIOS REALIZADOS
-- ============================================================================

-- 1. FUNCIÓN validar_saldo_suficiente (mi_app/blueprints/pedidos.py)
--    - Modificada para siempre retornar True (permitir procesamiento)
--    - Cambia el mensaje cuando hay saldo insuficiente para mostrar advertencia
--    - Antes: bloqueaba el pedido si saldo_restante < 0
--    - Ahora: permite el pedido pero muestra advertencia

-- 2. FUNCIÓN nuevo() en pedidos.py
--    - Agregada lógica para mostrar advertencia cuando habrá saldo negativo
--    - El pedido se procesa de todas maneras
--    - Se muestra flash message con advertencia

-- 3. FUNCIÓN validar_saldo_pedido_ajax
--    - Agregado campo "tendencia_saldo" en la respuesta JSON
--    - Permite al frontend distinguir entre saldo negativo y errores reales

-- 4. FRONTEND (mi_app/templates/pedidos/nuevo.html)
--    - Modificada función validarSaldoPedido() para mostrar advertencias en lugar de bloquear
--    - Cambio de alert-danger a alert-warning para saldos negativos
--    - Modificada función validarFormulario() para no bloquear el botón con saldo negativo

-- ============================================================================
-- COMPORTAMIENTO ACTUAL
-- ============================================================================

-- ✅ PEDIDOS CON SALDO SUFICIENTE:
--    - Se procesan normalmente
--    - No se muestran advertencias
--    - Saldo se descuenta normalmente

-- ⚠️ PEDIDOS CON SALDO INSUFICIENTE:
--    - Se procesan de todas maneras
--    - Se muestra advertencia visual (amarilla)
--    - Se registra el movimiento PEDIDO
--    - La cuenta queda con saldo negativo
--    - Se muestra mensaje flash de advertencia

-- ❌ ERRORES REALES:
--    - Solo se bloquean errores de conexión o validación
--    - Se muestran alertas rojas (alert-danger)

-- ============================================================================
-- EJEMPLO DE USO
-- ============================================================================

-- Escenario: Cuenta con 1,000 BRS, pedido de 1,500 BRS
-- 
-- ANTES:
-- - Pedido bloqueado
-- - Mensaje: "Saldo insuficiente. Faltan: 500 BRS"
-- - No se registra movimiento
-- 
-- AHORA:
-- - Pedido procesado
-- - Advertencia: "⚠️ ADVERTENCIA: Saldo insuficiente. Saldo actual: 1,000 BRS, Saldo resultante: -500 BRS (NEGATIVO)"
-- - Se registra movimiento PEDIDO de 1,500 BRS
-- - Cuenta queda con saldo de -500 BRS

-- ============================================================================
-- BENEFICIOS
-- ============================================================================

-- 1. Flexibilidad operativa: Permite procesar pedidos urgentes
-- 2. Transparencia: Muestra claramente cuando hay saldo negativo
-- 3. Control: El usuario puede decidir si proceder o no
-- 4. Auditoría: Todos los movimientos quedan registrados
-- 5. Recuperación: Se puede compensar con depósitos posteriores

-- ============================================================================
-- NOTAS IMPORTANTES
-- ============================================================================

-- - Los saldos negativos se reflejan correctamente en el flujo de caja
-- - Se mantiene la integridad de los datos
-- - Las advertencias son claras y visibles
-- - El sistema sigue siendo seguro y auditable
-- - Se puede revertir fácilmente si es necesario

-- ============================================================================
-- VERIFICACIÓN
-- ============================================================================

-- Para verificar que funciona correctamente:
-- 1. Crear un pedido con monto mayor al saldo disponible
-- 2. Verificar que se procesa sin bloquear
-- 3. Verificar que se muestra advertencia amarilla
-- 4. Verificar que el saldo queda negativo en flujo de caja
-- 5. Verificar que el movimiento se registra correctamente 