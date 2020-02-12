## Social Context builder written in Python/Flask


## Docker instructions for deployment of the app to your environment:
In the directory of the DockerFile
---------------------------------------------
To create a docker image execute: 

`docker build . -t social-context-builder`

To run the docker image execute:

`docker run -p 5000:5000 social-context-builder` and visit with your browser http://0.0.0.0:5000
## Deployed Endpoints
Social Relations 
Description: The API accepts as minimum input the userID to return the social relationships of the user

/social/relations/{userID}

Example call:
http://0.0.0.0:5000/social/relations/U100042

Social Preferences
Description: The API accepts a userID and taskID to return a ranked list of users based on the user’s social preferences.

/social/preferences/{userID}/{taskID}/

Example call:
http://0.0.0.0:5000/social/preferences/U100042/T100095/

Social Explanations 
Description: The API accepts a userID and taskID and returns an explanation of why a particular user is fit for the task

/social/explanations/{userID}/{taskID}/

Example call: 
http://0.0.0.0:5000/social/explanations/U100047/T100093/

## Live environment OUC endpoints
Social relations : 

http://82.116.211.130/social/relations/U100047

Social preferences:

http://82.116.211.130/social/preferences/U100042/T100095/

Social explanations:

http://82.116.211.130/social/explanations/U100047/T100093/




