# Import necessary libraries
import socket

# Existing imports and setup
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import pytz
import sys
import logging

_logger = logging.getLogger(__name__)

# Your existing functions and model definitions...
# ... (functions like get_time_from_float, convert_date_to_utc, convert_date_to_local, etc.)

class biometric_machine(models.Model):
    _name = 'biometric.machine'

    # Cron job to check the connection
    @api.model
    def _cron_check_connection(self):
        _logger.info("Running cron job to check biometric machine connections")
        for mc in self.search([('state', '=', 'active')]):
            mc.check_notification()

    # Method to check notification with IP connection verification
    def check_notification(self):
        for mc in self:
            now = datetime.strftime(datetime.now(), DATETIME_FORMAT)
            yesterday = datetime.strftime(datetime.now() - timedelta(days=1), DATETIME_FORMAT)
            _logger.info(f'Checking notifications for machine {mc.name} between {yesterday} and {now}')

            # Check the IP connection first
            if not self._check_ip_connection(mc.ip_address, mc.port):
                _logger.error(f'Cannot connect to machine {mc.name} at {mc.ip_address}:{mc.port}')
                self._send_connection_error_notification(mc)
                continue

            # Fetch records from the biometric.record model
            records = self.env['biometric.record'].search(
                [('machine', '=', mc.id), ('name', '>=', yesterday), ('name', '<=', now)]
            )
            _logger.info(f'Found {len(records)} records for machine {mc.name}')

            if any(r.state != 'failed' for r in records):
                _logger.info(f'Machine {mc.name} has successful records, skipping notification')
                continue

            if mc.state != 'active':
                _logger.info(f'Machine {mc.name} is not active, skipping notification')
                continue

            self._send_connection_error_notification(mc)

    # Method to check if the IP address is reachable
    def _check_ip_connection(self, ip_address, port):
        try:
            socket.create_connection((ip_address, port), timeout=10)
            return True
        except (socket.timeout, socket.error) as e:
            _logger.error(f'Error connecting to {ip_address}:{port} - {str(e)}')
            return False

    # Method to send a connection error notification
    def _send_connection_error_notification(self, mc):
        partners = self.env['res.users'].search([
            ('groups_id', 'in', self.env.ref('hr_bio_attendance.group_check_bio_attendance').id)
        ]).mapped('partner_id')

        if partners:
            mail_content = _(
                'Dear Sir, <br> Attendance Biometric Machine:%s has a connection error. Please check.<br> '
                'Regards<br>') % (mc.name)
            main_content = {
                'subject': _('Connection Error for Biometric Machine: %s ') % (mc.name),
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'recipient_ids': [(4, pid) for pid in partners.ids],
            }
            self.env['mail.mail'].sudo().create(main_content).send()
            _logger.info(f'Notification sent for machine {mc.name}')

    # Other methods (e.g., download_attendancenew, action_create_log, etc.) remain the same...
