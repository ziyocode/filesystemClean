###################################################################
# Original author: Ryan Cho
# encoding: utf-8
# purpose: Delete unnecessary files periodically via python program
# config file path : ~/filesystemClean/filesystemClean.conf
###################################################################

import os
import sys
import time
import logging
import re
from datetime import datetime

# setting Configuration File
configFile = "/Users/ziyocode/Documents/workspaces/python/filesystemClean/filesystem_clean.conf"

# setting Logging configuration
logdir = "/var/log/filesystem_clean"
log_expired_date = 10  # integer : days
logdate = datetime.today().strftime("%Y%m%d")
log_filename = logdir + "/filesystem_clean_" + logdate + ".log"

if os.path.exists(logdir) == "False":
    os.mkdir(logdir)

logger = logging.getLogger("filesystem_clean")
logger.setLevel(logging.INFO)

# create console handle and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create file handler and set level to debug
fh = logging.FileHandler(log_filename)
fh.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter(
    fmt="%(asctime)s %(name)s [%(levelname)s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
)

# add formatter to ch, fh
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# add ch, fh to logger
logger.addHandler(ch)
logger.addHandler(fh)

# setting current Time
current_time = time.time()


# start input-check
def input_checker():
    try:
        cf = open(configFile, "r")
    except OSError as e:
        logger.info(e)
    else:
        for line in cf:
            if line.startswith("#") or line.lstrip() == "":
                continue
            else:
                lineList = line.split(":")

                ##### input_check #####
                if len(lineList) == 6:
                    mode = str(lineList[0])
                    work_dir = str(lineList[1])
                    scope = str(lineList[2])
                    prefix = str(lineList[3])
                    target_date = int(lineList[4])
                    # target_time = target_date * 24 * 60 * 60  # 1 day
                    method = str(lineList[5].rstrip())

                    if mode == "RUN":
                        logger.info(
                            "Files will be deleted/initialized in real. RUNNING mode : actually delete!!"
                        )
                    elif mode == "DEBUG":
                        logger.info("Files are not deleted/initialized. DEBUG mode : log only!!.")
                    else:
                        logger.error("Please check mode in configuration file.")
                        sys.exit("-----> Configuration file error")

                    if os.path.isdir(work_dir):
                        logger.info("Direcotory is [%s]", work_dir)
                    else:
                        logger.error("Please check the Directory in configuration file.")
                        sys.exit("-----> Configuration file error")

                    if scope == "ALL":
                        logger.info("All files are subject to delete/initialize.")
                    elif scope == "SPECIFIC":
                        logger.info(
                            "Files that start with [%s] are subject to delete/initialize.", prefix,
                        )
                    else:
                        logger.error("Please check the scope in configuration file.")
                        sys.exit("-----> Configuration file error")

                    logger.info("Target Date is [%i]", target_date)

                    if method == "DELETE":
                        logger.info("method is [%s]", method)
                    elif method == "NULL":
                        logger.info("method is [%s]", method)
                    else:
                        logger.error("Please check the method in configuration file.")
                        sys.exit("-----> Configuration file error")
                else:
                    logger.error("Please check the configuration file - num(entity) is wrong.!!")
                    sys.exit("-----> Configuration file error")
        logger.info("-" * 70)
        cf.close()


def _automethod(running_mode, method_type, target_file):
    if method_type == "DELETE" and "filesystem_clean" not in target_file:
        if running_mode == "RUN":
            logging.info("[RUNNING] Deleted File : %s", target_file)
            os.remove(target_file)
        else:
            logger.info("[DEBUGE] Deleted file : %s", target_file)
    elif (
        method_type == "NULL"
        and os.path.getsize(target_file) != 0
        and "filesystem_clean" not in target_file
    ):
        if running_mode == "RUN":
            logger.info("[RUNNING] Initialized File : %s", target_file)
            nf = open(target_file, "w")
            nf.close()
        else:
            logger.info("[DEBUG] Initialized File : %s", target_file)


def autodelete(mode, work_dir, scope, prefix, target_time, method):
    for (path, files) in os.walk(work_dir):
        for filename in files:
            file_mtime = os.stat(os.path.join(path, filename)).st_mtime
            file_fullpath = os.path.join(path, filename)
            if (current_time - file_mtime) > target_time:
                if scope == "ALL":
                    _automethod(mode, method, file_fullpath)
                elif scope == "SPECIFIC":
                    if filename.startswith(prefix):
                        _automethod(mode, method, file_fullpath)
                    else:
                        continue
                else:
                    logger.error("Please check the scope in configuration file.")
                    break


def find_empty_dirs(running_mode, work_dir, scope, method):
    monthFormat = re.compile("/([2]\d{3}(0[1-9]|1[0-2]))|([2]\d{3}/(0[1-9]|1[0-2]))")
    if scope == "ALL" and method == "DELETE":
        logger.info("start deleting empty directories.")
        logger.info("-" * 70)
        for (path, dir, files) in os.walk(work_dir):
            if len(dir) == 0 and len(files) == 0 and monthFormat.search(path) != None:
                if running_mode == "RUN":
                    logger.info("[RUNNING] Deleted directory: %s", path)
                    os.rmdir(path)
                else:
                    logger.info("[DEBUG] Deleted directory: %s", path)


def own_log_delete(logdir, log_expired_date):
    for (path, files) in os.walk(logdir):
        for filename in files:
            file_mtime = os.stat(os.path.join(path, filename)).st_mtime
            if (current_time - file_mtime) > log_expired_date * 24 * 60 * 60:
                file_fullpath = os.path.join(path, filename)
                logger.info("filesystem_clean logs deleted : %s", file_fullpath)
                os.remove(file_fullpath)


# configuration file check
logger.info("-" * 70)
logger.info("filesystem_clean.py start!!")
logger.info("-" * 70)
logger.info("-" * 70)
logger.info("Configuration file : filesystem_clean.conf file check")
logger.info("-" * 70)
input_checker()
logger.info("Configuration file check is successfully completed.")
logger.info("-" * 70)

# main fuction start
with open(configFile, "r") as cf:
    for line in cf:
        if line.startswith("#") or line.lstrip() == "":
            continue
        else:
            lineList = line.split(":")
            mode = str(lineList[0])
            work_dir = str(lineList[1])
            scope = str(lineList[2])
            prefix = str(lineList[3])
            target_date = int(lineList[4])
            target_time = target_date * 24 * 60 * 60
            method = str(lineList[5].rstrip())
            logger.info(
                "[MODE:%s] [DIR:%s] [SCOPE:%s] [PREFIX:%s] [TARGET TIME:%i days] [METHOD:%s]",
                mode,
                work_dir,
                scope,
                prefix,
                target_date,
                method,
            )
            logger.info("-" * 70)
            autodelete(mode, work_dir, scope, prefix, target_time, method)
            logger.info("-" * 70)
            find_empty_dirs(mode, work_dir, scope, method)
            logger.info("-" * 70)

logger.info("start deleting %s logs", logdir)
logger.info("-" * 70)

own_log_delete(logdir, log_expired_date)

logger.info("-" * 70)
logger.info("filesystem_clean.py is successfully completed.")
logger.info("-" * 70)
