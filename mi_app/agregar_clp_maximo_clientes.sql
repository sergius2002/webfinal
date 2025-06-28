-- =====================================================
-- AGREGAR COLUMNA CLP_MAXIMO A LA TABLA CLIENTES
-- =====================================================

-- Agregar la columna clp_maximo a la tabla clientes
ALTER TABLE clientes 
ADD COLUMN clp_maximo DECIMAL(15,2) DEFAULT 0.00;

-- Agregar comentario a la columna
COMMENT ON COLUMN clientes.clp_maximo IS 'Monto máximo en CLP que puede tener el cliente (equivalente en BRS para nuevos pedidos)';

-- Crear índice para optimizar consultas por clp_maximo
CREATE INDEX idx_clientes_clp_maximo ON clientes(clp_maximo);

-- =====================================================
-- COMENTARIOS Y EXPLICACIÓN
-- =====================================================

/*
ESTA MODIFICACIÓN AGREGA UNA COLUMNA PARA CONTROLAR EL LÍMITE DE CLP POR CLIENTE:

1. clp_maximo: 
   - Tipo: DECIMAL(15,2) - Permite montos grandes con 2 decimales
   - Valor por defecto: 0.00 - Sin límite inicial
   - Propósito: Establecer el máximo CLP que puede tener un cliente

2. USO:
   - Al crear un nuevo pedido, se calcula: CLP = BRS / Tasa
   - Se valida que el CLP del pedido no exceda el clp_maximo del cliente
   - Si se excede, se muestra una advertencia

3. EJEMPLO:
   - Cliente tiene clp_maximo = 1000000 (1 millón CLP)
   - Tasa actual = 0.000123
   - BRS máximo permitido = 1000000 * 0.000123 = 123 BRS

PARA EJECUTAR:
1. Conectarse a la base de datos Supabase
2. Ejecutar este script completo
3. La columna estará disponible inmediatamente

NOTA: Los clientes existentes tendrán clp_maximo = 0.00 (sin límite)
*/ 