===============================================
        RECORDATORIO DE PAGOS PRO - MANUAL
===============================================

Descripción:
------------
Aplicación para gestionar pagos pendientes y enviar recordatorios por correo electrónico. 
Permite registrar servicios/deudas con fechas límite y montos, generar recordatorios visuales 
y enviarlos por email automáticamente.

Requisitos del sistema:
-----------------------
- Python 3.8 o superior
- Conexión a internet para envío de emails
- Cuenta de Gmail con verificación en dos pasos habilitada

Instalación:
------------
1. Instalar Python desde python.org (si no está instalado)
2. Instalar las dependencias necesarias:


Primeros pasos:
---------------
1. Ejecutar la aplicación:


2. Configurar cuenta de Gmail:
- Ir a "Configuración" > "Configuración de Correo"
- Ingresar correo emisor (Gmail)
- Generar una "Contraseña de aplicación" (ver sección Ayuda)
- Ingresar correo receptor

3. Agregar servicios/pagos:
- Ir a pestaña "Servicios"
- Completar: Servicio, Fecha límite (usar calendario), Monto
- Clic en "Agregar Servicio"

4. Generar y enviar recordatorio:
- Ir a pestaña "Recordatorio"
- Clic en "Generar Recordatorio" para previsualizar
- Clic en "Enviar por Email" para enviar el recordatorio

Configuración de correo:
------------------------
⚠️ IMPORTANTE: No usar tu contraseña normal de Gmail ⚠️

1. Activar verificación en dos pasos:
- Ir a: https://myaccount.google.com/security
- Activar "Verificación en dos pasos"

2. Generar contraseña de aplicación:
- Misma sección > "Contraseñas de aplicación"
- Seleccionar aplicación: "Correo"
- Seleccionar dispositivo: "Otro (Personalizado)"
- Nombre: "RecordatorioPagos"
- Clic en "Generar"
- Copiar la contraseña de 16 dígitos

3. Pegar en la aplicación:
- En campo "Contraseña / App Password"

Características principales:
----------------------------
1. Gestión de servicios:
- Agregar/eliminar servicios con fechas y montos
- Visualización en tabla con colores para pagos vencidos
- Limpiar todos los servicios con confirmación

2. Generación de recordatorios:
- Listado detallado de pagos pendientes
- Cálculo de días restantes y total adeudado
- Indicadores visuales de urgencia (🟢/🟠/🔴)

3. Envío por email:
- Envío directo a través de Gmail
- Diálogo de progreso durante el envío
- Validación de configuración previa
- Prueba de configuración de correo

4. Personalización:
- Cambio entre tema claro/oscuro (Menú > Tema)
- Guardado automático de configuración
- Registro de actividades con timestamp

5. Exportación:
- Guardar recordatorio como archivo TXT
- Formato: recordatorio_pagos_AAAAMMDD_HHMMSS.txt

Menú de temas:
--------------
- Acceder a "Tema" en la barra superior
- Opciones:
- "Tema Claro": Interfaz con colores claros
- "Tema Oscuro": Interfaz con colores oscuros (predeterminado)

Solución de problemas:
----------------------
1. Error al enviar correo:
- Verificar conexión a internet
- Confirmar contraseña de aplicación (no contraseña normal)
- Probar configuración con "Probar Configuración"
- Verificar que el correo emisor sea Gmail

2. Validación de emails falla:
- Asegurar formato correcto: usuario@dominio.com
- No incluir espacios antes/después

3. Servicios no aparecen:
- Verificar que se hayan agregado en pestaña "Servicios"
- Clic en "Generar Recordatorio" después de agregar

4. Problemas visuales:
- Reiniciar la aplicación
- Cambiar tema (puede resolver problemas de renderizado)

Notas importantes:
------------------
- La configuración se guarda automáticamente en "payment_reminder_config.json"
- Los servicios agregados persisten entre sesiones
- Para desinstalar: eliminar los archivos .py y .json
- La aplicación no almacena información en la nube

Soporte técnico:
----------------
Para problemas no resueltos:
- Contactar: soporte@ejemplo.com
- Incluir captura del registro de actividades

===============================================
        FIN DEL MANUAL - v1.0
===============================================