# Checklist de Pruebas Manuales - Sistema de Pedidos

## 1. Pruebas de Formularios
- [ ] Intentar enviar formulario de nuevo pedido con todos los campos vacíos
- [ ] Ingresar letras en campos numéricos (BRS, tasa)
- [ ] Ingresar números negativos en BRS y tasa
- [ ] Ingresar valores extremadamente grandes y pequeños
- [ ] Ingresar tasas en formatos raros (p.ej. 1,000.50, 1.000,50, 1,000, etc.)
- [ ] Pegar valores con espacios, símbolos o caracteres extraños
- [ ] Seleccionar un cliente inexistente (manipulando el HTML)
- [ ] Ingresar fechas en formato incorrecto (15-01-2025, 2025/01/15, etc.)
- [ ] Usar fechas futuras y pasadas
- [ ] Doble click en "Guardar" para simular doble envío
- [ ] Cerrar sesión a mitad de una operación y luego intentar guardar

## 2. Pruebas de Navegación
- [ ] Acceder a rutas protegidas sin estar logueado
- [ ] Intentar editar/eliminar pedidos inexistentes (cambiando el ID en la URL)
- [ ] Usar el navegador hacia atrás y adelante tras operaciones
- [ ] Refrescar la página tras enviar un formulario

## 3. Pruebas de Seguridad
- [ ] Modificar datos desde el inspector del navegador y enviar valores no permitidos
- [ ] Probar inyecciones simples en campos de texto (ej: ' OR 1=1 --)
- [ ] Acceder a funciones de admin sin permisos
- [ ] Manipular el HTML para enviar campos ocultos o adicionales

## 4. Pruebas de Usabilidad
- [ ] Probar en diferentes navegadores (Chrome, Firefox, Edge, móvil)
- [ ] Probar en dispositivos móviles
- [ ] Pegar datos desde Excel/Word
- [ ] Probar accesibilidad (tabulación, lectores de pantalla)

## 5. Pruebas de Integridad de Datos
- [ ] Crear, editar y eliminar pedidos y verificar en la base de datos
- [ ] Verificar que los límites de CLP y validaciones de tasa funcionan
- [ ] Verificar que los mensajes de error y éxito sean claros

---

**Marca cada casilla tras realizar la prueba.** 