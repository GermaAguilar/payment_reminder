# Recordatorio de pagos

Aplicación de escritorio para llevar el control de pagos pendientes y enviarte el recordatorio por correo. Registras cada servicio o deuda con su fecha límite y su monto; la aplicación calcula los días que faltan, marca lo vencido y lo urgente, suma el total y envía el resumen por Gmail.

Hecha con Python y Tkinter.

## Qué hace

- **Servicios:** agrega y elimina pagos con fecha límite (calendario) y monto. La tabla resalta los vencidos.
- **Recordatorio:** genera el listado con los días restantes de cada pago y el total pendiente.
  - 🟢 faltan más de 3 días · 🟠 vence hoy o en 3 días o menos · 🔴 vencido
- **Correo:** envía el recordatorio por Gmail y permite probar la configuración antes de enviar.
- **Exportar:** guarda el recordatorio como archivo de texto (`recordatorio_pagos_AAAAMMDD_HHMMSS.txt`).
- **Tema claro u oscuro**, desde el menú **Tema**.

Los servicios y la configuración se guardan solos y se mantienen entre sesiones.

## Instalación

Necesitas Python 3.8 o superior.

```bash
git clone https://github.com/GermaAguilar/payment_reminder.git
cd payment_reminder
pip install -r requirements.txt
python payment_reminder.py
```

En Linux, Tkinter se instala aparte: `sudo apt install python3-tk`.

## Configurar el correo

La aplicación envía desde una cuenta de Gmail usando una **contraseña de aplicación**, no tu contraseña normal.

1. Activa la verificación en dos pasos en <https://myaccount.google.com/security>.
2. En esa misma sección, entra en **Contraseñas de aplicación** y genera una (por ejemplo, con el nombre "RecordatorioPagos").
3. En la pestaña **Configuración** de la aplicación, escribe el correo emisor, pega la contraseña de 16 caracteres y escribe el correo receptor.
4. Pulsa **Probar Configuración**.

## Dónde se guardan los datos

Todo queda en tu equipo, en el archivo `payment_reminder_config.json`, junto al script. Nada se sube a la nube.

> [!WARNING]
> La contraseña de aplicación se guarda en ese archivo **sin cifrar**. No lo compartas ni lo subas a un repositorio (ya está en `.gitignore`). Si crees que alguien lo vio, revoca la contraseña desde tu cuenta de Google y genera otra.

## Si algo falla

| Problema | Qué revisar |
|---|---|
| No envía el correo | Conexión a internet; que el emisor sea Gmail; que uses la contraseña de aplicación y no la normal. |
| "Correo inválido" | Formato `usuario@dominio.com`, sin espacios antes ni después. |
| El recordatorio sale vacío | Agrega los pagos en **Servicios** y pulsa **Generar Recordatorio**. |

## Estructura del código

`payment_reminder.py` está organizado en capas:

- `DataManager`: lee y guarda la configuración y los servicios.
- `EmailService`: conexión y envío por SMTP.
- `ReminderGenerator`: arma el texto del recordatorio.
- `ModernRecordatorioApp`: la interfaz.
