# -*- coding: utf-8 -*-
#
# Copyright 2014 Telefonica Investigación y Desarrollo, S.A.U
#
# This file is part of fiware-connectors (FI-WARE project).
#
# fiware-connectors is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
# later version.
# fiware-connectors is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License along with fiware-connectors. If not, see
# http://www.gnu.org/licenses/.
#
# For those usages not covered by the GNU Affero General Public License please contact with Francisco Romero
# francisco.romerobueno@telefonica.com
#
#     Author: Ivan Arias
#

from lettuce import world
import time
import http_utils
import general_utils
from myTools.constants import *

class Ckan:
    world.dictTemp = None
    # --------------- Configuration ------------------------
    def __init__(self, ckan_version, ckan_url, ckan_authorization, dataset_default):
        """
        constructor
        :param ckan_version:
        :param ckan_url:
        :param ckan_authorization:
        """
        world.ckan_version    = ckan_version
        world.ckan_url        = ckan_url
        world.authorization   = ckan_authorization
        world.dataset_default = dataset_default

    def __createUrl(self, operation, element = None, offset = None):
        """
        create the url for different operations
        :param element:
        :param offset: used in resource search
        :param operation: operation type (dataset, etc)
        :return: request url
        """
        if operation == VERSION:
            value = "%s/%s" % (world.ckan_url, PATH_VERSION_CKAN)
        if operation ==PACKAGE_SHOW:
            value = "%s/%s%s" % (world.ckan_url, PATH_PACKAGE_SHOW, element) # datasetName
        if operation == DATASTORE_SEARCH:
            value = "%s/%s%s" % (world.ckan_url, PATH_DATASTORE_SEARCH, element)  # resourceId
        if operation == DATASTORE_SEARCH_OFFSET:
            value = "%s/%s%s%s%s" % (world.ckan_url, PATH_DATASTORE_SEARCH, element, OFFSET, offset)  # resourceId
        if operation == ORGANIZATION_CREATE or operation == PACKAGE_CREATE or operation == RESOURCE_CREATE or operation == DATASTORE_CREATE or operation == ORGANIZATION_LIST:
            value = "%s/%s/%s" % (world.ckan_url, PATH_API_CREATE, operation)
        if operation ==ORGANIZATION_SHOW:
             value = "%s/%s/%s?id=%s" % (world.ckan_url, PATH_API_CREATE, ORGANIZATION_SHOW, element) # organization Name
        return value

    def __createHeaders(self, operation, content="xml"):
        """
        create the header for different requests
        :param operation: different request
        :param content: "xml" or "json"
        :return:
        """
        if operation == CKAN_HEADER:
            return {AUTHORIZATION: world.authorization, CONTENT_TYPE: APPLICATION_CONTENT + content}#, ACCEPT: APPLICATION_CONTENT + content}

    def __getResourceId (self, error = None):
        """
        get Resource Id from ckan by API
        :return: resource_Id
        """
        self.resp = None
        world.dataset = world.organization[world.cygnus_type].lower()+"_"+world.dataset_default
        self.resp= http_utils.request3(GET, self.__createUrl(PACKAGE_SHOW, world.dataset), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)
        if error and self.resp.status_code == status_codes ["Not Found"]:
            return NOT_FOUND
        assert self.resp.status_code != status_codes ["Not Found"], VALIDATE_DATASET_MSG+" %s \n" % (world.dataset)
        dictBody = general_utils.convertStrToDict(self.resp.text, JSON)[RESULT][RESOURCE]
        for i in range(len (dictBody)):
            if dictBody[i][NAME] == world.resource:
                resource_id = dictBody[i][ID]
                break
            else:
                resource_id = VALIDATE_RESOURCE_MSG
        assert resource_id != VALIDATE_RESOURCE_MSG, VALIDATE_RESOURCE_MSG+" %s \n" % (world.resource)
        return resource_id

    #----------------- Verification ---------------------
    def versionCKAN (self):
        """
        Verify if ckan is installed and that version is the expected
        """
        resp= http_utils.request3(GET, self.__createUrl(VERSION), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)
        bodyDict = general_utils.convertStrToDict(resp.text, JSON)
        assert  world.ckan_version == str(bodyDict[VERSION]), \
        "Wrong ckan version verified: %s. Expected: %s. \n\nBody content: %s" \
        % (str(bodyDict[VERSION]), str(world.ckan_version), str(resp.text))

    def verifyDatasetSearch_valuesAndType (self, content):
        """
        Verify that the attribute contents (type and value) are stored in ckan
        :param content: xml or json
        """
        world.dictTemp = None
        self.body = None
        self.offset = 0
        outMsg = "Names are missing"
        resourceId = self.__getResourceId()
        if content == XML:
            valueTemp = CONTENT_VALUE
        else:
             valueTemp = VALUE_JSON

        resp = http_utils.request3(GET, self.__createUrl(DATASTORE_SEARCH, resourceId), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)
        world.dictTemp = general_utils.convertStrToDict(resp.text, JSON)
        self.offset = (world.dictTemp[RESULT][TOTAL]/100)*100
        if self.offset != 0:
            resp = http_utils.request3(GET, self.__createUrl(DATASTORE_SEARCH_OFFSET, resourceId, self.offset), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)
            world.dictTemp = general_utils.convertStrToDict(resp.text, JSON)

        for i in range(world.attrsNumber):                                                                      # loops through all our  attributes
            for j in range(len(world.dictTemp[RESULT][RECORDS])):                                                     # loops through all ckan data in the resource

                if world.dictTemp[RESULT][RECORDS][j][ATTR_NAME] == world.attrs[i][NAME]:                             # if find the name, begin the verifications
                    if world.compoundNumber == 0:

                        if world.dictTemp[RESULT][RECORDS][j][ATTR_VALUE] != world.attrs[i][valueTemp]:                  # verify the value
                            return "The "+world.attrs[i][NAME]+" value does not match..."
                    else:
                        for l in range(world.compoundNumber):
                            if world.dictTemp[RESULT][RECORDS][j][ATTR_VALUE][ITEM+str(l)] != world.attrs[i][valueTemp][ITEM+str(l)]:   # verify the compound values
                                return "The "+world.attrs[i][NAME][ITEM+str(l)]+" compound values does not match..."
                    if world.dictTemp[RESULT][RECORDS][j][ATTR_TYPE] != world.attrs[i][TYPE]:                        # verify the type
                        return "The "+world.attrs[i][NAME]+" type does not match..."
                    outMsg = "OK"
                    break

        return outMsg

    def verifyDatasetSearch_metadatas (self, content):
        """
        Verify that the attribute contents (metadatas) are stored in ckan in row mode
        :param content: xml or json
        """
        if world.metadatasNumber <= 0: return "does not has metadata.."
        outMsg = "Names are missing"
        for i in range(world.attrsNumber):                                                                      # loops through all our  attributes
            for j in range(len(world.dictTemp[RESULT][RECORDS])):                                                    # loops through all ckan data in the resource
                if world.dictTemp[RESULT][RECORDS][j][ATTR_NAME] == world.attrs[i][NAME]:                             # if find the name, begin the verification
                    if world.dictTemp[RESULT][RECORDS][j][ATTR_MD] != None:                                        # verify if it has metadatas
                        for k in range(len(world.dictTemp[RESULT][RECORDS][j][ATTR_MD])):
                            if content == XML:
                                if world.dictTemp[RESULT][RECORDS][j][ATTR_MD][k][TYPE] != world.attrs[i][METADATA][CONTEXT_METADATA][k][TYPE]:
                                     return "The "+world.attrs[i][NAME]+" metatada type does not match..."
                            else:
                                if world.dictTemp[RESULT][RECORDS][j][ATTR_MD][k][TYPE] != world.attrs[i][METADATAS_JSON][k][TYPE]:
                                     return "The "+world.attrs[i][NAME]+" metatada type does not match..."
                outMsg = "OK"
                break
        return outMsg

    def verifyIfDatasetExist (self):
        """
        verify if
        """
        resp =  self.__getResourceId(TRUE) # TRUE is for error operation
        assert resp == NOT_FOUND, \
            VALIDATE_DATASET_MSG+" %s \n" % (world.dataset)

    def validateResponse (self, response):
        """
        assert the response obtained after content verifications
        :param response:
        """
        assert response == "OK", \
        "...Wrong data stored in ckan: %s \n" % (response)

    #---------------- Column -------------------------
    def __organizationNotExist (self, orgName):
        """
        Verify if the organization exist
        :param orgName: org
        :return: return True if de organization does not exist, False if it does exist
        """
        resp = http_utils.request3(GET, self.__createUrl(ORGANIZATION_LIST), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)
        return (resp.text.find(orgName) < 0)

        #resp, body = http_utils.request2(GET, self.__createUrl(ORGANIZATION_LIST), self.__createHeaders(CKAN_HEADER, JSON), TRUE, TRUE, ERROR[NOT])
        #return (body.find(orgName) < 0)

    def __datasetNotExist (self):
        """
        Verify if the dataset exist
        :return:  return Not found if de dataset does not exist, if it does exist returns the datasetId
        """
        resp = http_utils.request3(GET, self.__createUrl(PACKAGE_SHOW, world.dataset), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)
        if resp.status_code == status_codes["Not Found"]:
            return NOT_FOUND
        else:
            bodyDict=general_utils.convertStrToDict(resp.text,JSON)
            return bodyDict[RESULT][ID]

    def __createDataset (self):
        """
        create a new dataset if does not exist
        Name: organization_defaultPackage
        """
        dataset = self.__datasetNotExist()
        if dataset == NOT_FOUND:
            payloadDict = {NAME:  world.dataset,
                           OWNER_ORG: world.organization[world.cygnus_type]}
            payload = general_utils.convertDictToStr(payloadDict, JSON)
            resp = http_utils.request3(POST, self.__createUrl(PACKAGE_CREATE), self.__createHeaders(CKAN_HEADER, JSON), payload, EMPTY, True, False)
            bodyDict=general_utils.convertStrToDict(resp.text,JSON)
            return bodyDict[RESULT][ID]
        else:
            return dataset

    def createOrganization (self, orgName):
        """
        Create a new organization and a dataset associated if they do not exist
        :param orgName:
        """
        world.datasetId = None
        if orgName == ORGANIZATION_WITHOUT_DATASET:
            world.dataset = world.organization[world.cygnus_type]+"_"+world.dataset_default+"error"
        else:
            if orgName != DEFAULT: world.organization[world.cygnus_type] = orgName
            world.dataset = world.organization[world.cygnus_type]+"_"+world.dataset_default

        if orgName != ORGANIZATION_MISSING:
            if self.__organizationNotExist(world.organization[world.cygnus_type]):
                payload = general_utils.convertDictToStr({NAME: world.organization[world.cygnus_type]}, JSON)
                self.resp = http_utils.request3(POST, self.__createUrl(ORGANIZATION_CREATE), self.__createHeaders(CKAN_HEADER, JSON), payload, EMPTY, True, False)
                assert self.resp.status_code != status_codes ["Not Found"], VALIDATE_ORGA_MSG+" %s \n" % (world.organization[world.cygnus_type])
            if orgName != ORGANIZATION_WITHOUT_DATASET:
                world.datasetId = self.__createDataset()

    def __resourceNotExist (self):
        """
        Verify if the resource exist
        :return:  return Not found if de resource does not exist, if it does exist returns the resourceId
        """
        resp = http_utils.request3(GET, self.__createUrl(PACKAGE_SHOW, world.dataset), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)
        if resp.text.find( world.resource) < 0:
            return NOT_FOUND
        else:
            bodyDict=general_utils.convertStrToDict(resp.text,JSON)
            for i in range(0, bodyDict[RESULT][NUM_RESOURCE]):
                if bodyDict [RESULT][RESOURCE][i][NAME] == world.resource:
                    return bodyDict[RESULT][RESOURCE][i][ID]

    def __generateField (self, attrQuantity, attrValueType, metadataType):
        """
        generate fields to datastore request
        :param attrQuantity:
        :param attrValueType:
        :param metadataType:
        :return: fields list
        """
        field = []
        field.append({ID:RECVTIME, TYPE: TIMESTAMP})
        for i in range(int(attrQuantity)):
            field.append({ID:ATTR_NAME+"_"+str(i), TYPE: attrValueType})
            if metadataType != WITHOUT_METADATA_FIELD:
                field.append({ID:ATTR_NAME+"_"+str(i)+"_md", TYPE: metadataType})
        return field

    def __createDataStore (self, attrQuantity, attrValueType, metadataType):
        """
        create a datastore in a resource
        :param attrQuantity:
        :param attrValueType:
        :param metadataType:
        """
        payloadDict = {RESOURCE_ID:  world.resourceId,
                       FIELD:  self.__generateField (attrQuantity, attrValueType, metadataType),
                       FORCE: TRUE}
        payload = general_utils.convertDictToStr(payloadDict, JSON)
        self.resp = http_utils.request3(POST, self.__createUrl(DATASTORE_CREATE), self.__createHeaders(CKAN_HEADER, JSON), payload, EMPTY, True, False)
        assert self.resp.status_code == status_codes ["OK"], "...ERROR creating Datastore in resource Id: %s ..." % (world.resourceId)

    def createResource (self, resourceName, attrQuantity, attrValueType, metadataType):
        """
        create  a new resource if it does not exists
        :param resourceName:
        :param attrQuantity:
        :param attrValueType:
        :param metadataType:
        """
        if resourceName != DEFAULT: world.resource = resourceName
        if attrQuantity != DEFAULT: world.attrsNumber = attrQuantity
        resp = self.__resourceNotExist()
        if resp == NOT_FOUND and world.organization[world.cygnus_type] != ORGANIZATION_MISSING and world.datasetId != None and resourceName != RESOURCE_MISSING:
            payloadDict = {NAME:  world.resource,
                           URL: URL_EXAMPLE,
                           PACKAGE_ID: world.datasetId}
            payload = general_utils.convertDictToStr(payloadDict, JSON)

            resp = http_utils.request3(POST, self.__createUrl(RESOURCE_CREATE), self.__createHeaders(CKAN_HEADER, JSON), payload, EMPTY, True, False)
            assert self.resp.status_code == status_codes ["OK"], "...ERROR creating resource: %s ..." % (world.resource)

            bodyDict=general_utils.convertStrToDict(resp.text,JSON)
            world.resourceId = str(bodyDict[RESULT][ID])
            self.__createDataStore(attrQuantity, attrValueType, metadataType)

    def verifyDatasetSearch_values_column (self, content):
        delayTimeForAttributeVerify = 0.5
        world.totalElement = None
        self.lastElement = None
        world.dictTemp = None
        self.offset = None
        self.resp = None

        if content == XML:
            valueTemp = CONTENT_VALUE
        else:
             valueTemp = VALUE_JSON
        resourceId = self.__getResourceId()

        self.resp = http_utils.request3(GET, self.__createUrl(DATASTORE_SEARCH, resourceId), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)

        #resp, self.body = http_utils.request2(GET, self.__createUrl(DATASTORE_SEARCH, resourceId), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, TRUE, ERROR[NOT])
        world.dictTemp = general_utils.convertStrToDict(self.resp.text, JSON)

        self.offset = (world.dictTemp[RESULT][TOTAL]/100)*100
        if self.offset != 0:
            self.resp = None

            self.resp = http_utils.request3(GET, self.__createUrl(DATASTORE_SEARCH_OFFSET, resourceId, self.offset), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)

            #resp, self.body = http_utils.request2(GET, self.__createUrl(DATASTORE_SEARCH_OFFSET, resourceId, self.offset), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, TRUE, ERROR[NOT])
            world.dictTemp = general_utils.convertStrToDict(self.resp.text, JSON)
        world.totalElement = world.dictTemp[RESULT][TOTAL]
        self.lastElement = world.dictTemp[RESULT][RECORDS][world.totalElement-1]
        for i in range(int(world.attrsNumber)):

            if str(self.lastElement[ATTR_NAME+"_"+str(i)]) != str(world.attrs[i][valueTemp]):                  # verify the value
                return "The "+world.attrs[i][NAME]+" value does not match..."
            time.sleep(delayTimeForAttributeVerify)
        return "OK"

    def verifyIfResourceIsEmpty (self):
        """
        verify if the resource is empty
        """
        resourceId = self.__getResourceId()

        resp = http_utils.request3(GET, self.__createUrl(DATASTORE_SEARCH, resourceId), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)
        world.dictTemp = general_utils.convertStrToDict(resp.text, JSON)
        assert len(world.dictTemp[RESULT][RECORDS]) == 0,\
            " %s %s \n" % (VALIDATE_RESOURCE_IS_NOT_EMPTY_MSG, world.resource)

    def verifyDatasetSearch_metadata_column (self, content):
        """
        Verify that the attribute contents (metadatas) are stored in ckan in column mode
        :param content: xml or json
        """
        self.lastElement = None
        delayTimeForMetadataVerify = 0.50
        self.lastElement = world.dictTemp[RESULT][RECORDS][world.totalElement-1]
        if world.metadataValue == TRUE:
            for i in range(int(world.attrsNumber)):
                if content == XML:
                    if self.lastElement[ATTR_NAME+"_"+str(i)+"_md"][0][VALUE_JSON] != world.attrs[i][METADATA][CONTEXT_METADATA][0][VALUE_JSON]:
                        return "The "+world.attrs[i][NAME]+" metatada value does not match..."
                else:
                    if self.lastElement[ATTR_NAME+"_"+str(i)+"_md"][0][VALUE_JSON] != world.attrs[i][METADATAS_JSON][0][VALUE_JSON]:
                        return "The "+world.attrs[i][NAME]+" metatada value does not match..."
                time.sleep(delayTimeForMetadataVerify)
        return "OK"

    def verifyOrganizationNotExist (self):
        """
        Validate that the organization is  not created in ckan per column
        """
        if world.organizationOperation != ORGANIZATION_WITHOUT_DATASET and world.resourceOperation != RESOURCE_MISSING:
            self.resp = None
            self.resp = http_utils.request3(GET, self.__createUrl(ORGANIZATION_SHOW, world.organization[world.cygnus_type]), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)
            assert self.resp.text.find(NOT_FOUND)> 0, \
                '\n...Organization \"%s\", is created by cygnus in ckan: \n\n body: %s' % (world.organization[world.cygnus_type], self.resp.text)

    def verifyDatasetNotExist (self):
        """
        Validate that the dataset is not created in ckan per column
        """
        if world.resourceOperation != RESOURCE_MISSING:
            self.resp = None
            self.resp = http_utils.request3(GET, self.__createUrl(PACKAGE_SHOW, world.dataset), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)
            assert self.resp.text.find(NOT_FOUND)> 0, \
                '\n...dataset \"%s\", is created by cygnus in ckan: \n\n body: %s' % (world.dataset, self.resp.text)

    def verifyResourceNotExist (self):
        """
        Validate that the resource is not created in ckan per column
        """
        if world.organizationOperation != ORGANIZATION_WITHOUT_DATASET:
            self.resp = None
            self.dictTemp = None
            self.resp = http_utils.request3(GET, self.__createUrl(PACKAGE_SHOW, world.dataset), self.__createHeaders(CKAN_HEADER, JSON), EMPTY, EMPTY, True, False)
            self.dictTemp = general_utils.convertStrToDict(self.resp.text, JSON)
            assert self.dictTemp[RESULT][RESOURCE] != None, \
                '\n...resource \"%s\", is created by cygnus in ckan: \n\n body: %s' % (world.resource, self.resp.text)
