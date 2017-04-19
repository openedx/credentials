import csv

BOEING_UUID = '588cef66-70c8-450b-a1b2-e5ebd70ee1fe'
MITPE_UUID = '57a18492-8ea8-4295-ba1f-d25b46a2d218'

"""
# Boeing
SELECT
  u.username,
  u.email,
  p.name
FROM
  certificates_generatedcertificate gc
  JOIN auth_user u ON gc.user_id = u.id
  JOIN auth_userprofile p ON u.id = p.user_id
WHERE
  gc.status = 'downloadable'
  AND course_id IN ('course-v1:MITProfessionalX+SysEngxB1+3T2016', 'course-v1:MITProfessionalX+SysEngxB2+3T2016', 'course-v1:MITProfessionalX+SysEngxB3+3T2016', 'course-v1:MITProfessionalX+SysEngxB4+3T2016')
GROUP BY
  username
HAVING
  COUNT(1) >=4;

# MIT
SELECT
  u.username,
  u.email,
  p.name
FROM
  certificates_generatedcertificate gc
  JOIN auth_user u ON gc.user_id = u.id
  JOIN auth_userprofile p ON u.id = p.user_id
WHERE
  gc.status = 'downloadable'
  AND course_id IN ('course-v1:MITProfessionalX+SysEngx1+3T2016', 'course-v1:MITProfessionalX+SysEngx2+3T2016', 'course-v1:MITProfessionalX+SysEngx3+3T2016', 'course-v1:MITProfessionalX+SysEngx4+3T2016')
GROUP BY
  username
HAVING
  COUNT(1) >=4;


# Pull credentials
SELECT
  username,
  uuid,
  pc.program_uuid
FROM
  credentials_usercredential uc
  JOIN credentials_programcertificate pc ON pc.id = uc.credential_id
WHERE
  pc.program_uuid IN ('588cef6670c8450ba1b2e5ebd70ee1fe', '57a184928ea84295ba1fd25b46a2d218')

"""

from edx_rest_api_client.client import EdxRestApiClient

access_token_url = 'https://api.edx.org/oauth2/v1/access_token'
# TODO Pull OAuth credentials for the credentials app
client_id = None
client_secret = None

# Retrieve JWT access token
access_token, __ = EdxRestApiClient.get_oauth_access_token(access_token_url, client_id, client_secret, token_type='jwt')
api_client = EdxRestApiClient('https://credentials.edx.org/api/v2/', jwt=access_token)

with open('mitpe.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # api_client.credentials.post({
        #     'username': row['username'],
        #     'credential': {'program_uuid': MITPE_UUID},
        #     'attributes': []
        # })
