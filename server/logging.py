#!/usr/bin/env python
# -*- coding:utf-8 -*-
# project : xadmin-server
# filename : logging
# author : ly_13
# date : 10/18/2024
import logging
import os
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler

from server.utils import get_current_request


class DailyTimedRotatingFileHandler(TimedRotatingFileHandler):
    @staticmethod
    def rotator(source, dest):
        """ Override the original method to rotate the log file daily."""
        # Get the destination filename based on yesterday's date
        date_yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        path = [os.path.dirname(source), date_yesterday, os.path.basename(source)]
        dest_filename = os.path.join(*path)
        os.makedirs(os.path.dirname(dest_filename), exist_ok=True)
        
        if os.path.exists(source) and not os.path.exists(dest_filename):
            try:
                # 存在多个服务进程时, 保证只有一个进程成功 rotate
                os.rename(source, dest_filename)
            except (PermissionError, OSError) as e:
                # Handle case when file is in use by another process
                try:
                    # Try to copy content and truncate instead
                    with open(source, 'rb') as src_file:
                        content = src_file.read()
                    
                    with open(dest_filename, 'wb') as dst_file:
                        dst_file.write(content)
                    
                    # Truncate the original file
                    with open(source, 'w') as src_file:
                        pass
                        
                    logging.info(f"Log rotation completed by copy method: {source} -> {dest_filename}")
                except Exception as copy_err:
                    logging.error(f"Failed to rotate log by copy method: {copy_err}")
    
    # Remove the _get_rotate_dest_filename method as it's now integrated into rotator


class ServerFormatter(logging.Formatter):
    def format(self, record):
        current_request = get_current_request()
        record.requestUser = str(current_request.user if current_request else 'SYSTEM')[:16]
        record.requestUuid = str(getattr(current_request, 'request_uuid', ""))
        return super().format(record)


class ColorHandler(logging.StreamHandler):
    WHITE = "0"
    RED = "31"
    GREEN = "32"
    YELLOW = "33"
    BLUE = "34"
    PURPLE = "35"

    def emit(self, record):
        try:
            msg = self.format(record)
            level_color_map = {
                logging.DEBUG: self.BLUE,
                logging.INFO: self.GREEN,
                logging.WARNING: self.YELLOW,
                logging.ERROR: self.RED,
                logging.CRITICAL: self.PURPLE
            }

            csi = f"{chr(27)}["  # 控制序列引入符
            color = level_color_map.get(record.levelno, self.WHITE)

            self.stream.write(f"{csi}{color}m{msg}{csi}m\n")
            self.flush()
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)
