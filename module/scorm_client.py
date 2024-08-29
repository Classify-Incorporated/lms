import requests
from django.conf import settings
from requests.exceptions import HTTPError
import base64
import logging
import os
logger = logging.getLogger(__name__)

class ScormCloud:
    def __init__(self):
        self.appid = settings.SCORMCLOUD_APP_ID
        self.secretkey = settings.SCORMCLOUD_SECRET_KEY
        self.serviceurl = settings.SCORMCLOUD_SERVICE_URL

    def get_headers(self):
        credentials = f"{self.appid}:{self.secretkey}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        return {
            'Authorization': f'Basic {encoded_credentials}',
        }

    def import_uploaded_course(self, courseid, path, title=None, may_create_new_version=True, postback_url=None):
        url = f"{self.serviceurl}/courses/importJobs/upload"
        try:
            with open(path, 'rb') as file:
                files = {
                    'file': ('scorm_package.zip', file, 'application/zip')
                }
                params = {
                    'courseId': courseid,
                    'mayCreateNewVersion': str(may_create_new_version).lower(),
                    'title': title  # Include the title parameter
                }

                if postback_url:
                    params['postbackUrl'] = postback_url

                headers = self.get_headers()
                response = requests.post(url, headers=headers, files=files, params=params)

                response.raise_for_status()
                response_data = response.json()

                if 'result' in response_data:
                    result = response_data['result']
                    print(f"Upload result: {result}")
                    return response_data
                else:
                    return {'error': 'Unexpected response format from SCORM Cloud'}

        except HTTPError as http_err:
            return {'error': f'HTTP error occurred: {http_err}'}
        except Exception as err:
            return {'error': f'An error occurred: {err}'}

    def create_registration(self, registration_id, courseid, learnerid, learnername):
        url = f"{self.serviceurl}/registrations"
        data = {
            'registrationId': registration_id,
            'courseId': courseid,
            'learner': {
                'id': str(learnerid),
                'firstName': learnername.split()[0],  # Assuming firstName is the first part of learnername
                'lastName': ' '.join(learnername.split()[1:]) if len(learnername.split()) > 1 else ''
            }
        }
        
        try:
            headers = self.get_headers()
            response = requests.post(url, headers=headers, json=data)

            response.raise_for_status()
            return response.json()
        except HTTPError as http_err:
            if response.status_code == 400 and "already exists" in response.text:
                return {'status': 'exists'}
            else:
                return {'error': f'HTTP error occurred: {http_err}'}
        except ValueError as val_err:
            return {'error': f'JSON decoding error occurred: {val_err}'}
        except Exception as err:
            return {'error': f'An error occurred: {err}'}

    def launch_course(self, registration_id, redirect_url):
        url = f"{self.serviceurl}/registrations/{registration_id}/launchLink"
        data = {
            'redirectOnExitUrl': redirect_url
        }
        try:
            response = requests.post(url, headers=self.get_headers(), json=data)
            response.raise_for_status()
            return response.json()
        except HTTPError as http_err:
            return {'error': f'HTTP error occurred: {http_err}'}
        except Exception as err:
            return {'error': f'An error occurred: {err}'}

    def get_course_info(self, courseid):
        url = f"{self.serviceurl}/courses/{courseid}"
        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            return response.json()
        except HTTPError as http_err:
            return {'error': f'HTTP error occurred: {http_err}'}
        except Exception as err:
            return {'error': f'An error occurred: {err}'}
        
    def get_registration(self, registration_id):
        url = f"{self.serviceurl}/registrations/{registration_id}"
        try:
            headers = self.get_headers()
            response = requests.get(url, headers=headers)

            # Print the request and response for debugging
            print(f"Request URL: {url}")
            print(f"Request Headers: {headers}")
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")

            response.raise_for_status()
            return response.json()
        except HTTPError as http_err:
            return {'error': f'HTTP error occurred: {http_err}'}
        except Exception as err:
            return {'error': f'An error occurred: {err}'}
        
    def list_registrations(self):
        url = f"{self.serviceurl}/registrations"
        try:
            headers = self.get_headers()
            response = requests.get(url, headers=headers)

            # Print the request and response for debugging
            print(f"Request URL: {url}")
            print(f"Request Headers: {headers}")
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")

            response.raise_for_status()
            response_data = response.json()

            # Print the entire response data for debugging
            print(f"Response Data: {response_data}")

            if 'registrations' in response_data:
                return response_data['registrations']
            else:
                return {'error': 'Unexpected response format from SCORM Cloud'}
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return {'error': f'HTTP error occurred: {http_err}'}
        except Exception as err:
            print(f"An error occurred: {err}")
            return {'error': f'An error occurred: {err}'}

    def list_courses(self):
        url = f"{self.serviceurl}/courses"
        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            response_data = response.json()

            if 'courses' in response_data:
                return response_data
            else:
                return {'courses': []}
        except HTTPError as http_err:
            return {'error': f'HTTP error occurred: {http_err}'}
        except Exception as err:
            return {'error': f'An error occurred: {err}'}
        
    def delete_course(self, courseid):
        url = f"{self.serviceurl}/courses/{courseid}"
        try:
            headers = self.get_headers()
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            return {'status': 'success'}
        except HTTPError as http_err:
            return {'error': f'HTTP error occurred: {http_err}'}
        except Exception as err:
            return {'error': f'An error occurred: {err}'}


        

