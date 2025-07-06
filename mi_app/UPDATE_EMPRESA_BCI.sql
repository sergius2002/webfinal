-- Script para actualizar el nombre de la empresa en la tabla transferencias
-- Cambia "ST CRISTOBAL SPA" por "ST CRISTOBAL BCI"

-- Verificar cuántos registros se van a actualizar
SELECT 
    empresa,
    COUNT(*) as cantidad_registros
FROM transferencias 
WHERE empresa = 'ST CRISTOBAL SPA'
GROUP BY empresa;

-- Actualizar los registros
UPDATE transferencias 
SET empresa = 'ST CRISTOBAL BCI'
WHERE empresa = 'ST CRISTOBAL SPA';

-- Verificar que la actualización fue exitosa
SELECT 
    empresa,
    COUNT(*) as cantidad_registros
FROM transferencias 
WHERE empresa = 'ST CRISTOBAL BCI'
GROUP BY empresa;

-- Mostrar un resumen de todas las empresas en la tabla
SELECT 
    empresa,
    COUNT(*) as total_registros
FROM transferencias 
GROUP BY empresa
ORDER BY total_registros DESC; 