###################################################################
# Original author: Ryan Cho
# encoding: utf-8
# purpose: Delete unnecessary files periodically via python program
# config file path : ./filesystemClean.conf
###################################################################

import os
import sys
import time
import logging
import re
from datetime import datetime
import gzip
import shutil

# setting Configuration File
CONFIG_FILE = "./filesystem_clean.conf"


# setting Logging configuration
LOGDIR = "/tmp/filesystem_clean"
LOG_EXPIRED_DATE = 10  # integer : days
LOGDATE = datetime.today().strftime("%Y%m%d")
LOG_FILENAME = LOGDIR + "/filesystem_clean_" + LOGDATE + ".log"

if os.path.exists(LOGDIR) is False:
    os.mkdir(LOGDIR)

logger = logging.getLogger("filesystem_clean")
logger.setLevel(logging.INFO)

# create console handle and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create file handler and set level to debug
fh = logging.FileHandler(LOG_FILENAME)
fh.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter(
    fmt="%(asctime)s %(name)s [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
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
        cf = open(CONFIG_FILE, "r", encoding="UTF-8")
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
                    condition = str(lineList[3])
                    target_date = int(lineList[4])
                    # target_time = target_date * 24 * 60 * 60  # 1 day
                    method = str(lineList[5].rstrip())
                    CONF_ERROR_MESSAGE = "-----> Configuration file error"

                    if mode == "RUN":
                        logger.info("Files will be deleted/initialized in real. RUNNING mode : actually delete!!")
                    elif mode == "DEBUG":
                        logger.info("Files are not deleted/initialized. DEBUG mode : log only!!.")
                    else:
                        logger.error("Please check mode in configuration file.")
                        sys.exit(CONF_ERROR_MESSAGE)

                    if os.path.isdir(work_dir):
                        logger.info("Direcotory is [%s]", work_dir)
                    else:
                        logger.error("Please check the Directory in configuration file.")
                        sys.exit(CONF_ERROR_MESSAGE)

                    if scope == "ALL":
                        logger.info("All files are subject to delete/initialize.")
                    elif scope == "SPECIFIC":
                        logger.info(
                            "Files that start with [%s] are subject to delete/initialize.",
                            condition,
                        )
                    else:
                        logger.error("Please check the scope in configuration file.")
                        sys.exit(CONF_ERROR_MESSAGE)

                    logger.info("Target Date is [%i]", target_date)

                    if method == "DELETE":
                        logger.info("method is [%s]", method)
                    elif method == "NULL":
                        logger.info("method is [%s]", method)
                    elif method == "GZIP":
                        logger.info("method is [%s]", method)
                    else:
                        logger.error("Please check the method in configuration file.")
                        sys.exit(CONF_ERROR_MESSAGE)
                else:
                    logger.error("Please check the configuration file - num(entity) is wrong.!!")
                    sys.exit(CONF_ERROR_MESSAGE)
        logger.info("-" * 70)
        cf.close()


def automethod(running_mode, method_type, target_file):
    if method_type == "DELETE" and "filesystem_clean" not in target_file:
        if running_mode == "RUN":
            logging.info("[RUNNING] Deleted File : %s", target_file)
            os.remove(target_file)
        else:
            logger.info("[DEBUGE] Deleted file : %s", target_file)
    elif method_type == "NULL" and os.path.getsize(target_file) != 0 and "filesystem_clean" not in target_file:
        if running_mode == "RUN":
            logger.info("[RUNNING] Initialized File : %s", target_file)
            nf = open(target_file, "w", encoding="UTF-8")
            nf.close()
        else:
            logger.info("[DEBUG] Initialized File : %s", target_file)
    elif method_type == "GZIP" and os.path.getsize(target_file) != 0:
        if running_mode == "RUN":
            logger.info("[RUNNING] gzip File : %s", target_file)
            with open(target_file, "rb") as f_in:
                gzip_file = target_file + ".gz"
                with gzip.open(gzip_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    if os.path.isfile(gzip_file):
                        os.remove(target_file)
        else:
            logger.info("[DEBUG] gzip File : %s", target_file)


def autodelete(mode, work_dir, scope, condition, target_time, method):
    for (root, path, files) in os.walk(work_dir):
        for filename in files:
            file_mtime = os.stat(os.path.join(root, filename)).st_mtime
            file_fullpath = os.path.join(root, filename)
            if (current_time - file_mtime) > target_time:
                if scope == "ALL":
                    automethod(mode, method, file_fullpath)
                elif scope == "SPECIFIC":
                    condition_list = condition.split(",")
                    if len(condition_list) > 1:
                        if filename.startswith(condition_list[0]) and condition_list[1] in filename:
                            automethod(mode, method, file_fullpath)
                    else:
                        if filename.startswith(condition):
                            automethod(mode, method, file_fullpath)
                else:
                    logger.error("Please check the scope in configuration file.")
                    break


def find_empty_dirs(running_mode, work_dir, scope, method):
    if scope == "ALL" and method == "DELETE":
        logger.info("start deleting empty directories.")
        logger.info("-" * 70)
        for (path, dir, files) in os.walk(work_dir):
            if len(dir) == 0 and len(files) == 0 and (re.compile("/([2]\d{3}(0[1-9]|1[0-2]))|([2]\d{3}/(0[1-9]|1[0-2]))")).search(path) != None:
                if running_mode == "RUN":
                    logger.info("[RUNNING] Deleted directory: %s", path)
                    os.rmdir(path)
                else:
                    logger.info("[DEBUG] Deleted directory: %s", path)


def own_log_delete(logdir, log_expired_date):
    for (root, path, files) in os.walk(logdir):
        for filename in files:
            file_mtime = os.stat(os.path.join(root, filename)).st_mtime
            if (current_time - file_mtime) > log_expired_date * 24 * 60 * 60:
                file_fullpath = os.path.join(root, filename)
                logger.info("filesystem_clean logs deleted : %s", file_fullpath)
                os.remove(file_fullpath)


if __name__ == "__main__":

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
    with open(CONFIG_FILE, "r", encoding="UTF-8") as conf:
        for condition in conf:
            if condition.startswith("#") or condition.lstrip() == "":
                continue
            else:
                conditionList = condition.split(":")
                MODE = str(conditionList[0])
                WORK_DIR = str(conditionList[1])
                SCOPE = str(conditionList[2])
                CONDITION = str(conditionList[3])
                TARGET_DATE = int(conditionList[4])
                TARGET_TIME = TARGET_DATE * 24 * 60 * 60
                METHOD = str(conditionList[5].rstrip())
                logger.info(
                    "[MODE:%s] [DIR:%s] [SCOPE:%s] [CONDITION:%s] [TARGET TIME:%i days] [METHOD:%s]",
                    MODE,
                    WORK_DIR,
                    SCOPE,
                    CONDITION,
                    TARGET_DATE,
                    METHOD,
                )
                logger.info("-" * 70)
                autodelete(MODE, WORK_DIR, SCOPE, CONDITION, TARGET_TIME, METHOD)
                logger.info("-" * 70)
                find_empty_dirs(MODE, WORK_DIR, SCOPE, METHOD)
                logger.info("-" * 70)

    logger.info("start deleting %s logs", LOGDIR)
    logger.info("-" * 70)

    own_log_delete(LOGDIR, LOG_EXPIRED_DATE)

    logger.info("-" * 70)
    logger.info("filesystem_clean.py is successfully completed.")
    logger.info("-" * 70)
