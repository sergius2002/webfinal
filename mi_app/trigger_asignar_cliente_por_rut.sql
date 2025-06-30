-- Trigger para asignar cliente en transferencias según RUT de pagador
-- Si no encuentra coincidencia, asigna 'Desconocido'

CREATE OR REPLACE FUNCTION asignar_cliente_por_rut()
RETURNS TRIGGER AS $$
DECLARE
    cliente TEXT;
    i       INTEGER;
    columna TEXT;
BEGIN
    FOR i IN 1..200 LOOP
        columna := format('pagador%s', i);
        EXECUTE format(
            'SELECT cliente FROM pagadores WHERE %I = $1 LIMIT 1',
            columna
        )
        INTO cliente
        USING NEW.rut;

        IF cliente IS NOT NULL THEN
            NEW.cliente := cliente;
            RETURN NEW;  -- Salimos en cuanto lo encontramos
        END IF;
    END LOOP;

    -- Si no halló ningún pagador, asigna valor por defecto
    NEW.cliente := 'Desconocido';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_asignar_cliente_por_rut ON transferencias;

CREATE TRIGGER trigger_asignar_cliente_por_rut
  BEFORE INSERT
  ON transferencias
  FOR EACH ROW
  EXECUTE FUNCTION asignar_cliente_por_rut(); 