-- Tabla para almacenar transacciones individuales del flujo de capital
CREATE TABLE IF NOT EXISTS transacciones_flujo (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('ENTRADA', 'SALIDA')),
    monto NUMERIC(15,2) NOT NULL,
    descripcion TEXT NOT NULL,
    categoria VARCHAR(50),
    capital_anterior NUMERIC(15,2) NOT NULL,
    capital_posterior NUMERIC(15,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_transacciones_flujo_fecha ON transacciones_flujo(fecha);
CREATE INDEX IF NOT EXISTS idx_transacciones_flujo_tipo ON transacciones_flujo(tipo);
CREATE INDEX IF NOT EXISTS idx_transacciones_flujo_categoria ON transacciones_flujo(categoria);

-- Función para actualizar el timestamp de updated_at
CREATE OR REPLACE FUNCTION update_transacciones_flujo_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER update_transacciones_flujo_updated_at 
    BEFORE UPDATE ON transacciones_flujo 
    FOR EACH ROW 
    EXECUTE FUNCTION update_transacciones_flujo_updated_at();

-- Insertar transacciones iniciales basadas en datos existentes
-- Esto es opcional, para migrar datos existentes
INSERT INTO transacciones_flujo (fecha, tipo, monto, descripcion, categoria, capital_anterior, capital_posterior)
SELECT 
    fecha,
    'ENTRADA' as tipo,
    ganancias as monto,
    COALESCE(descripcion, 'Ganancias del día') as descripcion,
    'GANANCIAS' as categoria,
    capital_inicial as capital_anterior,
    capital_final as capital_posterior
FROM flujo_capital 
WHERE ganancias > 0
ON CONFLICT DO NOTHING;

-- Insertar gastos como transacciones separadas
INSERT INTO transacciones_flujo (fecha, tipo, monto, descripcion, categoria, capital_anterior, capital_posterior)
SELECT 
    fecha,
    'SALIDA' as tipo,
    costo_gastos as monto,
    'Gastos Venezuela' as descripcion,
    'GASTOS_VENEZUELA' as categoria,
    capital_inicial as capital_anterior,
    capital_inicial + ganancias - costo_gastos as capital_posterior
FROM flujo_capital 
WHERE costo_gastos > 0
ON CONFLICT DO NOTHING;

-- Insertar gastos manuales como transacciones separadas
INSERT INTO transacciones_flujo (fecha, tipo, monto, descripcion, categoria, capital_anterior, capital_posterior)
SELECT 
    fecha,
    'SALIDA' as tipo,
    gastos_manuales as monto,
    'Gastos Chile' as descripcion,
    'GASTOS_CHILE' as categoria,
    capital_inicial + ganancias - costo_gastos as capital_anterior,
    capital_final as capital_posterior
FROM flujo_capital 
WHERE gastos_manuales > 0
ON CONFLICT DO NOTHING; 