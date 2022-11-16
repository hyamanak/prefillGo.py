import json
import os
import re
import sys
from os.path import exists
import requests

time_stamp = 'time_stamp.txt'
global_url = "https://cloud.memsource.com/web/api2/"
auth_url = global_url + "v1/auth/login"
mtrans_id = "1189032"
net_rate_scheme = "xCE7Cf9Ckuqx6ZAkyvwuS1"


class PrefillGo:
     def __init__(self, url_file, user_id, password):
          self.url_file = url_file
          self.user_id = user_id
          self.password = password
          self.project_uids = self.get_project_uids()
          self.time_stamp_file = open('time_stamp.txt', 'a+')
          self.token = self.__authentication()
          self.puid_juids_dict = self.__get_puid_juids_dict()
          
     def __get_response(self, api_type, url, headers, data):
          return requests.request(api_type, url, headers=headers, data=data)

     def __get_puid_juids_dict(self):
          #{
          # 'project_uid':['XXXX', 'YYYY', 'ZZZZ'],
          # 'project_uid1':['XXXX', 'YYYY', 'ZZZZ']
          #...
          # }
          project_jobs = {}
          for puid in self.project_uids:
               project_jobs[puid] = self.__get_job_uids(puid)
          return project_jobs

     def __authentication(self):
          self.payload = json.dumps({
               "password": self.password,
               "userName": self.user_id,
               "code": ""
               })
          self.headers = {
               'Content-Type': 'application/json',
               'Accept': 'application/json'
               }
          response = self.__get_response("POST", auth_url, self.headers, self.payload)
          json_auth = response.json()
          api_token = "ApiToken " + json_auth['token']
          return api_token
     
     def __job_list2dict(self, job_uids): ##takes job_uids list ['xxxxx', 'yyyyyy', 'zzzzzz']
          job_entry = []
          temp_job = {}

          for job_uid in job_uids:
               temp_job['uid'] = job_uid
               job_entry.append(temp_job)
               temp_job = {}
          return job_entry

     def get_project_uids(self):
          project_uids = []
          with open(self.url_file, 'r') as file:
               uid_regex = r"(?<=/show/).*?(?=/)"

               for url in file:
                    uid = re.search(uid_regex, url)
                    if uid.group() is None:
                         raise TypeError(url,"is not a valid URL")
                    if uid.group() not in project_uids:
                         project_uids.append(uid.group())              
               return project_uids
          
     def __get_job_uids(self, project_uid) -> list: ##jobuid
          job_uids = []
          get_job_url = global_url + "v2/projects/" + project_uid + "/jobs"
          self.payload = {}
          self.headers = {
               'Accept': 'application/json',
               'Authorization': self.token
               }
          jobs_info = self.__get_response("GET", get_job_url, self.headers, self.payload)
          jobs_info = jobs_info.json()
          for job_detail in jobs_info["content"]:
               for key in job_detail.keys():
                    if key == 'uid':
                         job_uids.append(job_detail[key])
          return job_uids

     def __change_mt2mtrans_g(self, project_uid):
          url = global_url + "v1/projects/" + project_uid + "/mtSettings"
          self.payload = json.dumps({
               "machineTranslateSettings": {
               "id": mtrans_id
               }
               })
          self.headers = {
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': self.token
               }
          response = self.__get_response("PUT", url, self.headers, self.payload)
          print(response.text)
          
     
     def change2mtrans_project(self):
          for project_uid in self.project_uids:
               self.__change_mt2mtrans_g(project_uid)
          

     def __delete_all_translations(self, job_uids, project_uid):
          self.url = global_url + "v1/projects/" + project_uid + "/jobs/translations"
          job_dict = self.__job_list2dict(job_uids)
          #print(job_dict)

          self.payload = json.dumps({
               "jobs": job_dict,
               "getParts": {}
               })
          self.headers = {
               'Content-Type': 'application/json',
               'Authorization': self.token
               }
          #print(self.payload)
          response = self.__get_response("DELETE", self.url, self.headers, self.payload)
          print(response.text)
          #return job_entr

     def del_all_in_projects(self): #it does not delete files or projects, only translation files' contents
          for puid, job_uids in self.puid_juids_dict.items():
               self.__delete_all_translations(job_uids, puid)

     def __pre_translate_jobs(self, job_uids, project_uid):
          ## pre-translate jobs
          self.url = global_url + "v2/projects/" + project_uid + "/jobs/preTranslate"
          job_dict = self.__job_list2dict(job_uids)

          self.payload = json.dumps({
          "jobs": job_dict,
          "segmentFilters": [
          "LOCKED",
          "NOT_LOCKED"
          ],
          "useProjectPreTranslateSettings": False,
          "callbackUrl": "",
          "preTranslateSettings": {
          "autoPropagateRepetitions": False,
          "confirmRepetitions": True,
          "setJobStatusCompleted": False,
          "setJobStatusCompletedWhenConfirmed": False,
          "setProjectStatusCompleted": False,
          "overwriteExistingTranslations": True,
          "translationMemorySettings": {
               "useTranslationMemory": True,
               "translationMemoryThreshold": 0,
               "confirm100PercentMatches": True,
               "confirm101PercentMatches": True,
               "lock100PercentMatches": False,
               "lock101PercentMatches": False
          },
          "machineTranslationSettings": {
               "useMachineTranslation": True,
               "lock100PercentMatches": False,
               "confirm100PercentMatches": True,
               "useAltTransOnly": False
          },
          "nonTranslatableSettings": {
               "preTranslateNonTranslatables": False,
               "confirm100PercentMatches": False,
               "lock100PercentMatches": False
          }
          }
          })
          
          self.headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': self.token
          }

          response = self.__get_response("POST", self.url, self.headers, self.payload)
          print(response.text)
     
     def pre_translate_projects(self):
          for project_uid, job_uids in self.puid_juids_dict.items():
               #print(project_uid, job_uids)
               self.__pre_translate_jobs(job_uids, project_uid)
               

     def create_analyses(self, job_uids):
          self.url = global_url + "v2/analyses"
          job_dict = self.__job_list2dict(job_uids) ##this convert{'uid': 'xxxxxx'} format

          self.payload = json.dumps({
          "jobs": job_dict,
          "includeNumbers": True,
          "includeNonTranslatables": False,
          "includeFuzzyRepetitions": True,
          "type": "PreAnalyse",
          "namingPattern": "PrefillGo",
          "includeConfirmedSegments": True,
          "countSourceUnits": True,
          "analyzeByLanguage": False,
          "analyzeByProvider": False,
          "includeMachineTranslationMatches": False,
          "includeLockedSegments": True,
          "includeTransMemory": True,
          "allowAutomaticPostAnalysis": False,
          "netRateScheme": {
          "id": net_rate_scheme
          }
          })
          self.headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': self.token
          }

          response = self.__get_response("POST", self.url, self.headers, self.payload)
          print(response.text)
     
     def create_project_analyses(self):
          for puid, job_uid_list in self.puid_juids_dict.items():
               self.create_analyses(job_uid_list)


prefill = PrefillGo('url_list.txt', sys.argv[1], sys.argv[2])


##-- change mt setting to mtrans google
prefill.change2mtrans_project()

##-- delete all translation contents for jobs
prefill.del_all_in_projects()

##-- pre-translate jobs 
prefill.pre_translate_projects()

##-- create analysis for jobs
prefill.create_project_analyses()


