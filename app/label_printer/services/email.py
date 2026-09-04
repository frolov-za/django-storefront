import logging
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from email.utils import formatdate

from django.utils import timezone

from label_printer.models import EmailServerConfig


logger = logging.getLogger(__name__)


RU_MONTHS = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)


def send_email(
    config,
    subject,
    plain_body,
    recipients,
    *,
    html_body=None,
    attachment_path=None,
):
    logger.debug(
        "Подготовка отправки письма: получатели=%s, тема=%s",
        recipients,
        subject,
    )

    if config.smtp_use_ssl and config.smtp_use_tls:
        logger.error(
            "Ошибка настройки SMTP: одновременно включены SSL и STARTTLS"
        )
        raise ValueError(
            "Нельзя одновременно использовать SSL и STARTTLS"
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.from_email
    message["To"] = ", ".join(recipients)
    message["Date"] = formatdate(localtime=True)

    message.set_content(plain_body)

    if html_body:
        logger.debug("Добавлена HTML-версия письма")
        message.add_alternative(html_body, subtype="html")

    if attachment_path:
        logger.debug(
            "Добавлено вложение: %s",
            attachment_path,
        )

        with open(attachment_path, "rb") as attachment:
            message.add_attachment(
                attachment.read(),
                maintype="application",
                subtype="zip",
                filename=os.path.basename(attachment_path),
            )

    if config.smtp_use_ssl:
        server_class = smtplib.SMTP_SSL
        logger.debug("Используется SMTP через SSL")
    else:
        server_class = smtplib.SMTP
        logger.debug("Используется SMTP без SSL")

    logger.debug(
        "Подключение к SMTP-серверу: %s:%s",
        config.smtp_host,
        config.smtp_port,
    )

    with server_class(
        config.smtp_host,
        config.smtp_port,
        timeout=30,
    ) as server:

        if config.smtp_use_tls:
            logger.debug("Запуск STARTTLS")
            server.starttls()
            logger.debug("STARTTLS успешно запущен")

        logger.debug(
            "Авторизация на SMTP-сервере: пользователь=%s",
            config.smtp_username,
        )

        server.login(
            config.smtp_username,
            config.smtp_password,
        )

        logger.debug("SMTP-авторизация выполнена")

        server.send_message(message)

    logger.info(
        "Письмо успешно отправлено: тема=%s, получатели=%s",
        subject,
        recipients,
    )


def send_test_email(config_id):
    logger.debug(
        "Запуск отправки тестового письма: config_id=%s",
        config_id,
    )

    try:
        config = EmailServerConfig.objects.get(pk=config_id)

        recipients = (
            config.get_recipients_list()
            or [config.smtp_username]
        )

        logger.debug(
            "Получатели тестового письма: %s",
            recipients,
        )

        send_email(
            config,
            "Тестовое письмо",
            "Это тестовое письмо для проверки SMTP-настроек.",
            recipients,
        )

    except EmailServerConfig.DoesNotExist:
        logger.error(
            "SMTP-конфигурация не найдена: config_id=%s",
            config_id,
        )

        return {
            "success": False,
            "detail": "SMTP-конфигурация не найдена",
        }

    except Exception as error:
        logger.exception(
            "Ошибка при отправке тестового письма: config_id=%s",
            config_id,
        )

        return {
            "success": False,
            "detail": str(error),
        }

    logger.info(
        "Тестовое письмо успешно отправлено: config_id=%s, получатели=%s",
        config_id,
        recipients,
    )

    return {
        "success": True,
        "detail": ", ".join(recipients),
    }


def build_backup_email(
    backup_name,
    size_mb,
    backup_date,
    *,
    error_detail=None,
):
    logger.debug(
        "Формирование письма о бэкапе: файл=%s, размер=%.2f МБ, ошибка=%s",
        backup_name,
        size_mb,
        bool(error_detail),
    )

    date_text = (
        f"{backup_date.day} "
        f"{RU_MONTHS[backup_date.month - 1]} "
        f"{backup_date.year}"
    )
    time_text = backup_date.strftime("%H:%M:%S")

    if error_detail:
        status_color = "#ef4444"
        status_bg = "#fef2f2"
        status_text = "Ошибка при создании бэкапа"
        icon = "✕"
    else:
        status_color = "#22c55e"
        status_bg = "#f0fdf4"
        status_text = "Бэкап успешно создан"
        icon = "✓"

    error_block = ""

    if error_detail:
        error_block = f"""
        <tr>
          <td style="padding: 0 32px 24px 32px;">
            <div style="
                background-color: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 8px;
                padding: 16px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                color: #991b1b;
                word-break: break-all;
            ">
              {error_detail}
            </div>
          </td>
        </tr>
        """

    html = f"""\
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>

<body style="
    margin: 0;
    padding: 0;
    background-color: #f4f4f7;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                 Roboto, Helvetica, Arial, sans-serif;
">

  <table role="presentation"
         width="100%"
         cellpadding="0"
         cellspacing="0"
         style="background-color: #f4f4f7; padding: 40px 16px;">

    <tr>
      <td align="center">

        <table role="presentation"
               width="600"
               cellpadding="0"
               cellspacing="0"
               style="
                   max-width: 600px;
                   width: 100%;
                   background-color: #ffffff;
                   border-radius: 12px;
                   overflow: hidden;
                   box-shadow: 0 1px 3px rgba(0,0,0,0.08);
               ">

          <!-- Header -->
          <tr>
            <td style="
                background-color: #1e293b;
                padding: 32px;
                text-align: center;
            ">
              <div style="
                  width: 48px;
                  height: 48px;
                  background-color: #334155;
                  border-radius: 10px;
                  display: inline-block;
                  line-height: 48px;
                  text-align: center;
                  margin-bottom: 12px;
              ">
                <span style="font-size: 24px;">📦</span>
              </div>

              <div style="
                  color: #ffffff;
                  font-size: 20px;
                  font-weight: 600;
                  margin-top: 8px;
              ">
                StoreFront
              </div>

              <div style="
                  color: #94a3b8;
                  font-size: 13px;
                  margin-top: 4px;
              ">
                Резервное копирование
              </div>
            </td>
          </tr>

          <!-- Status -->
          <tr>
            <td style="padding: 32px 32px 0 32px;">

              <table role="presentation"
                     cellpadding="0"
                     cellspacing="0"
                     style="
                         background-color: {status_bg};
                         border-radius: 8px;
                         width: 100%;
                     ">

                <tr>
                  <td style="padding: 16px 20px;">

                    <table role="presentation"
                           cellpadding="0"
                           cellspacing="0">

                      <tr>
                        <td style="
                            width: 32px;
                            height: 32px;
                            background-color: {status_color};
                            border-radius: 50%;
                            text-align: center;
                            vertical-align: middle;
                        ">
                          <span style="
                              color: #ffffff;
                              font-size: 16px;
                              font-weight: bold;
                              line-height: 32px;
                          ">
                            {icon}
                          </span>
                        </td>

                        <td style="
                            padding-left: 12px;
                            color: {status_color};
                            font-size: 15px;
                            font-weight: 600;
                        ">
                          {status_text}
                        </td>
                      </tr>

                    </table>

                  </td>
                </tr>

              </table>

            </td>
          </tr>

          <!-- Backup information -->
          <tr>
            <td style="padding: 24px 32px;">

              <table role="presentation"
                     width="100%"
                     cellpadding="0"
                     cellspacing="0"
                     style="border-collapse: collapse;">

                <tr>
                  <td style="
                      padding: 12px 0;
                      border-bottom: 1px solid #e2e8f0;
                      color: #64748b;
                      font-size: 13px;
                  ">
                    Имя файла
                  </td>

                  <td style="
                      padding: 12px 0;
                      border-bottom: 1px solid #e2e8f0;
                      color: #1e293b;
                      font-size: 13px;
                      font-weight: 500;
                      text-align: right;
                  ">
                    {backup_name}
                  </td>
                </tr>

                <tr>
                  <td style="
                      padding: 12px 0;
                      border-bottom: 1px solid #e2e8f0;
                      color: #64748b;
                      font-size: 13px;
                  ">
                    Дата
                  </td>

                  <td style="
                      padding: 12px 0;
                      border-bottom: 1px solid #e2e8f0;
                      color: #1e293b;
                      font-size: 13px;
                      font-weight: 500;
                      text-align: right;
                  ">
                    {date_text}
                  </td>
                </tr>

                <tr>
                  <td style="
                      padding: 12px 0;
                      border-bottom: 1px solid #e2e8f0;
                      color: #64748b;
                      font-size: 13px;
                  ">
                    Время
                  </td>

                  <td style="
                      padding: 12px 0;
                      border-bottom: 1px solid #e2e8f0;
                      color: #1e293b;
                      font-size: 13px;
                      font-weight: 500;
                      text-align: right;
                  ">
                    {time_text}
                  </td>
                </tr>

                <tr>
                  <td style="
                      padding: 12px 0;
                      color: #64748b;
                      font-size: 13px;
                  ">
                    Размер архива
                  </td>

                  <td style="
                      padding: 12px 0;
                      color: #1e293b;
                      font-size: 13px;
                      font-weight: 500;
                      text-align: right;
                  ">
                    {size_mb:.2f} МБ
                  </td>
                </tr>

              </table>

            </td>
          </tr>

          <!-- Error -->
          {error_block}

          <!-- Footer -->
          <tr>
            <td style="
                padding: 24px 32px 32px 32px;
                border-top: 1px solid #e2e8f0;
            ">
              <p style="
                  margin: 0;
                  color: #94a3b8;
                  font-size: 12px;
                  line-height: 1.5;
                  text-align: center;
              ">
                Автоматическое уведомление системы резервного копирования
                StoreFront.<br>
                Не отвечайте на это письмо.
              </p>
            </td>
          </tr>

        </table>

      </td>
    </tr>

  </table>

</body>
</html>
"""

    plain_text = (
        f"{status_text}\n\n"
        f"Имя файла: {backup_name}\n"
        f"Дата: {date_text}\n"
        f"Время: {time_text}\n"
        f"Размер: {size_mb:.2f} МБ\n"
    )

    if error_detail:
        plain_text += f"\nОшибка: {error_detail}\n"

    return html, plain_text
