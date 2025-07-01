-- =====================================================
-- TABLA DE CIERRE DE CAJA PARA SUPABASE
-- EJECUTAR EN EL SQL EDITOR DE SUPABASE
-- =====================================================

-- Crear tabla de cierre de caja
CREATE TABLE IF NOT EXISTS cierre_caja (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL UNIQUE,
    
    -- Valores automáticos (calculados desde otras tablas)
    saldo_inicial DECIMAL(15,2) DEFAULT 0,
    ingresos_binance DECIMAL(15,2) NOT NULL,
    ingresos_extra DECIMAL(15,2) DEFAULT 0,
    total_ingresos DECIMAL(15,2) NOT NULL,
    egresos_pedidos DECIMAL(15,2) NOT NULL,
    
    -- Valores manuales (editables por el usuario)
    egresos_detal DECIMAL(15,2) DEFAULT 0,
    gastos DECIMAL(15,2) DEFAULT 0,
    pago_movil DECIMAL(15,2) DEFAULT 0,
    cierre_detal DECIMAL(15,2) DEFAULT 0,
    saldo_bancos DECIMAL(15,2) DEFAULT 0,
    
    -- Valores calculados
    total_egresos DECIMAL(15,2) NOT NULL,
    cierre_mayor DECIMAL(15,2) NOT NULL,
    cierre_final DECIMAL(15,2) NOT NULL,
    diferencia DECIMAL(15,2) DEFAULT 0,
    
    -- Campos adicionales para ingresos extra
    ingresos_extra_detalle JSONB DEFAULT '[]'::jsonb,
    
    -- Metadatos
    usuario_creacion VARCHAR(255),
    usuario_modificacion VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índice en fecha para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_cierre_caja_fecha ON cierre_caja(fecha);

-- Crear función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION actualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger para actualizar updated_at
DROP TRIGGER IF EXISTS trigger_actualizar_updated_at_cierre ON cierre_caja;
CREATE TRIGGER trigger_actualizar_updated_at_cierre
    BEFORE UPDATE ON cierre_caja
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_updated_at();

-- Comentarios para documentar la tabla
COMMENT ON TABLE cierre_caja IS 'Tabla para almacenar los cierres de caja diarios';
COMMENT ON COLUMN cierre_caja.fecha IS 'Fecha del cierre (única por día)';
COMMENT ON COLUMN cierre_caja.saldo_inicial IS 'Saldo inicial del día (recursivo del día anterior)';
COMMENT ON COLUMN cierre_caja.ingresos_binance IS 'Total BRS cambiados por USDT en Binance';
COMMENT ON COLUMN cierre_caja.ingresos_extra IS 'Ingresos adicionales del día';
COMMENT ON COLUMN cierre_caja.total_ingresos IS 'Saldo inicial + ingresos totales';
COMMENT ON COLUMN cierre_caja.egresos_pedidos IS 'Total BRS de pedidos del día';
COMMENT ON COLUMN cierre_caja.egresos_detal IS 'Egresos de detalle (manual)';
COMMENT ON COLUMN cierre_caja.gastos IS 'Gastos del día (manual)';
COMMENT ON COLUMN cierre_caja.pago_movil IS 'Pagos móviles (manual)';
COMMENT ON COLUMN cierre_caja.cierre_detal IS 'Cierre de detalle (manual)';
COMMENT ON COLUMN cierre_caja.saldo_bancos IS 'Saldo actual en bancos (manual)';
COMMENT ON COLUMN cierre_caja.total_egresos IS 'Suma de todos los egresos';
COMMENT ON COLUMN cierre_caja.cierre_mayor IS 'Total ingresos - Total egresos';
COMMENT ON COLUMN cierre_caja.cierre_final IS 'Cierre mayor + Cierre detal';
COMMENT ON COLUMN cierre_caja.diferencia IS 'Cierre final - Saldo bancos';
COMMENT ON COLUMN cierre_caja.ingresos_extra_detalle IS 'Detalle de ingresos extra en formato JSON'; 