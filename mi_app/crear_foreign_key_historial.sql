-- PASO 3: Agregar foreign key (ejecutar después de que exista la tabla cierre_caja)
ALTER TABLE cierre_caja_historial 
ADD CONSTRAINT fk_historial_cierre 
FOREIGN KEY (cierre_id) REFERENCES cierre_caja(id) ON DELETE CASCADE; 