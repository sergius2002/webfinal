-- Agregar columna descripcion a la tabla flujo_capital
ALTER TABLE flujo_capital 
ADD COLUMN IF NOT EXISTS descripcion TEXT DEFAULT '';

-- Agregar comentario a la columna
COMMENT ON COLUMN flujo_capital.descripcion IS 'Descripción del gasto o movimiento de capital';

-- Actualizar registros existentes con descripción por defecto
UPDATE flujo_capital 
SET descripcion = CONCAT('Flujo de capital del ', fecha)
WHERE descripcion IS NULL OR descripcion = ''; 