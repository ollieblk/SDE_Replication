############################### SDE Replication - Copy #################################

#Geodatabase replication script - Copy
#Created by Ollie - Corporate GIS - 28/04/2023 for both 10.5 & 10.9 Enterprise environments
#The aim of this process is to copy assets, dynamic, vector, version into geodatabases locally (D drive)

########################################################################################

import time, os, datetime, sys, logging, logging.handlers, shutil
import arcpy

def getDatabaseItemCount(workspace):
    log = logging.getLogger("script_log")
    """returns the item count in provided database"""
    arcpy.env.workspace = workspace
    feature_classes = []
    log.info("Compiling a list of items in {0} and getting count.".format(workspace))
    for dirpath, dirnames, filenames in arcpy.da.Walk(workspace,datatype="Any",type="Any"):
        for filename in filenames:
            feature_classes.append(os.path.join(dirpath, filename))
    log.info("There are a total of {0} items in the database".format(len(feature_classes)))
    return feature_classes, len(feature_classes)

def replicateDatabase(dbConnection, targetGDB):
    log = logging.getLogger("script_log")
    startTime = time.time()

    if arcpy.Exists(dbConnection):
        featSDE,cntSDE = getDatabaseItemCount(dbConnection)
        log.info("Geodatabase being copied: %s -- Feature Count: %s" %(dbConnection, cntSDE))
        if arcpy.Exists(targetGDB):
            featGDB,cntGDB = getDatabaseItemCount(targetGDB)
            log.info("Old Target Geodatabase: %s -- Feature Count: %s" %(targetGDB, cntGDB))
            try:
                shutil.rmtree(targetGDB)
                log.info("Deleted Old %s" %(os.path.split(targetGDB)[-1]))
            except Exception as e:
                log.info(e)

        GDB_Path, GDB_Name = os.path.split(targetGDB)
        log.info("Now Creating New %s" %(GDB_Name))
        arcpy.CreateFileGDB_management(GDB_Path, GDB_Name)

        arcpy.env.workspace = dbConnection

        try:
            datasetList = [arcpy.Describe(a).name for a in arcpy.ListDatasets()]
        except Exception as e:
            datasetList = []
            log.info(e)
        try:
            featureClasses = [arcpy.Describe(a).name for a in arcpy.ListFeatureClasses()]
        except Exception as e:
            featureClasses = []
            log.info(e)
        try:
            tables = [arcpy.Describe(a).name for a in arcpy.ListTables()]
        except Exception as e:
            tables = []
            log.info(e)

        #Compiles a list of the previous three lists to iterate over
        allDbData = datasetList + featureClasses + tables
        
        #Remove this data - Temporary to reduce the run time of copying Version
        allDbData.remove("wcc_version.sdeadmin.confirm_fresh_master_vw")
        #This data needs to be indexed for the process to improve----
        
        for sourcePath in allDbData:
            targetName = sourcePath.split('.')[-1]
            targetPath = os.path.join(targetGDB, targetName)
            if not arcpy.Exists(targetPath):
                try:
                    log.info("Attempt 1: Attempting to Copy Feature %s to %s" %(targetName, targetPath))
                    arcpy.management.CopyFeatures(sourcePath, targetPath)
                    log.info("Finished copying Feature %s to %s" %(targetName, targetPath))
                except Exception as e:
                    try:
                        log.info("Attempt 2: Attempting to Copy %s to %s" %(targetName, targetPath))
                        arcpy.Copy_management(sourcePath, targetPath)
                        log.info("Finished Copying %s to %s" %(targetName, targetPath))
                    except Exception as e:
                            log.info("Unable to copy %s to %s" %(targetName, targetPath))
                            log.info(e)
            else:
                log.info("%s already exists....skipping....." %(targetName))

        featGDB,cntGDB = getDatabaseItemCount(targetGDB)
        log.info("Completed replication of %s -- Feature Count: %s" %(dbConnection, cntGDB))
        
    else:
        log.info("{0} does not exist or is not supported! \
        Please check the database path and try again.".format(dbConnection))

def formatTime(x):
    minutes, seconds_rem = divmod(x, 60)
    if minutes >= 60:
        hours, minutes_rem = divmod(minutes, 60)
        return "%02d:%02d:%02d" % (hours, minutes_rem, seconds_rem)
    else:
        minutes, seconds_rem = divmod(x, 60)
        return "00:%02d:%02d" % (minutes, seconds_rem)

if __name__ == "__main__":
    startTime = time.time()
    now = datetime.datetime.now()

    ############################### user variables #################################

    logPath = sys.argv[1]
    databaseConnection = sys.argv[2]
    targetGDB = sys.argv[3]
    
    ############################### logging items ###################################
    # Make a global logging object.
    logName = os.path.join(logPath,(now.strftime("GeodatabaseReplication.log")))

    log = logging.getLogger("script_log")
    log.setLevel(logging.INFO)

    h1 = logging.FileHandler(logName, mode="a")
    h2 = logging.StreamHandler()

    f = logging.Formatter("[%(levelname)s] [%(asctime)s] [%(lineno)d] - %(message)s",'%m/%d/%Y %I:%M:%S %p')

    h1.setFormatter(f)
    h2.setFormatter(f)

    h1.setLevel(logging.INFO)
    h2.setLevel(logging.INFO)

    log.addHandler(h1)
    log.addHandler(h2)

    log.info('Script: {0}'.format(os.path.basename(sys.argv[0])))

    try:
        ########################## function calls ######################################

        replicateDatabase(databaseConnection, targetGDB)
        
        ################################################################################
    except Exception as e:
        log.exception(e)

    totalTime = formatTime((time.time() - startTime))
    log.info('--------------------------------------------------')
    log.info("Script Completed After: {0}".format(totalTime))
    log.info('--------------------------------------------------')
