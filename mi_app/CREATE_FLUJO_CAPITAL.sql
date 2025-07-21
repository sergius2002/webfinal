-- Script para crear la tabla flujo_capital en Supabase
-- Ejecutar en Supabase SQL Editor

-- Tabla para almacenar el flujo de capital día a día
CREATE TABLE IF NOT EXISTS flujo_capital (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL UNIQUE,
    capital_inicial NUMERIC(15,2) NOT NULL DEFAULT 0,
    ganancias NUMERIC(15,2) NOT NULL DEFAULT 0,
    costo_gastos NUMERIC(15,2) NOT NULL DEFAULT 0,
    gastos_manuales NUMERIC(15,2) NOT NULL DEFAULT 0,
    capital_final NUMERIC(15,2) NOT NULL DEFAULT 0,
    margen_neto NUMERIC(15,2) NOT NULL DEFAULT 0,
    ponderado_ves_clp NUMERIC(10,5) NOT NULL DEFAULT 0,
    gastos_brs NUMERIC(15,2) NOT NULL DEFAULT 0,
    pago_movil_brs NUMERIC(15,2) NOT NULL DEFAULT 0,
    envios_al_detal_brs NUMERIC(15,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_flujo_capital_fecha ON flujo_capital(fecha);
CREATE INDEX IF NOT EXISTS idx_flujo_capital_capital_final ON flujo_capital(capital_final);

-- Insertar capital inicial para el 16-07-2025
INSERT INTO flujo_capital (fecha, capital_inicial, capital_final) 
VALUES ('2025-07-16', 32000000, 32000000)
ON CONFLICT (fecha) DO NOTHING;

-- Función para actualizar el timestamp de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER update_flujo_capital_updated_at 
    BEFORE UPDATE ON flujo_capital 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios para documentar la tabla
COMMENT ON TABLE flujo_capital IS 'Tabla para almacenar el flujo de capital día a día';
COMMENT ON COLUMN flujo_capital.fecha IS 'Fecha del flujo de capital';
COMMENT ON COLUMN flujo_capital.capital_inicial IS 'Capital al inicio del día';
COMMENT ON COLUMN flujo_capital.ganancias IS 'Ganancias del día (Margen Neto)';
COMMENT ON COLUMN flujo_capital.costo_gastos IS 'Costo de gastos en CLP (gastos/ponderado_ves_clp)';
COMMENT ON COLUMN flujo_capital.gastos_manuales IS 'Gastos ingresados manualmente en CLP';
COMMENT ON COLUMN flujo_capital.capital_final IS 'Capital al final del día';
COMMENT ON COLUMN flujo_capital.margen_neto IS 'Margen neto del día desde el módulo Márgenes';
COMMENT ON COLUMN flujo_capital.ponderado_ves_clp IS 'Ponderado VES/CLP del día';
COMMENT ON COLUMN flujo_capital.gastos_brs IS 'Gastos en BRS del día';
COMMENT ON COLUMN flujo_capital.pago_movil_brs IS 'Pago móvil en BRS del día';
COMMENT ON COLUMN flujo_capital.envios_al_detal_brs IS 'Envíos al detal en BRS del día'; 