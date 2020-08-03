## Social Context builder written in Python/Flask

## Introduction

The Social Context Builder is responsible for building and maintaining the social details of a user profile,
 by leveraging data within and wenet platform

### Social Relations Component

#### Description: 

The Social Relations component aims at analysing the social interactions of the users and specifies two pieces of information. 
The first concerns the relationships between them and the second is the tie strength of their friendship.

### Social Explanations Component

#### Description: 

The social explanations component is responsible for providing arguments to the user about the acceptance of each volunteer for a given task. 
It implements a knowledge- based methodology that relies on rules to provide explanations and the reasons about the inclusion of a given volunteer for the user’s task.  

### Social Ranking Component

#### Description: 

The social ranking component is responsible for ranking volunteers with respect to a specific task that a user poses. It analyzes the social and personal data of the volunteers, 
the characteristics of the task and the information of the user that set the task and performs a personalized ranking of the users and implements a knowledge-based methodology that utilizes rules to perform the user ranking. 

##Setup and configuration

### Docker instructions for deployment of the app to your environment:
In the directory of the DockerFile
---------------------------------------------
To create a docker image execute: 

`docker build . -t social-context-builder`

### Usage

To run the docker image execute:

`docker run -p 5000:5000 social-context-builder`

Visit with your browser: http://0.0.0.0:5000

### Required env variables

- APIKEY: apikey required for authenticating the incoming requests
- PROFILE_MANAGER_CONNECTOR_BASE_URL: base url for the profile manager connection
- TASK_MANAGER_CONNECTOR_BASE_URL: base url for the task manager endpoints

### Component Availability

social context builder: https://wenet.u-hopper.com/social_context_builder

### Deployed Endpoints


### Social Relations 
Description: The API accepts as minimum input the userID to return the social relationships of the user

#### /social/relations/{userID}

Example call:
`http://0.0.0.0:5000/social/relations/U100042`

### Social Preferences
Description: The API accepts a userID and taskID to return a ranked list of users based on the user’s social preferences.

#### /social/preferences/{userID}/{taskID}/

Example call:
`http://0.0.0.0:5000/social/preferences/U100042/T100095`

### Social Explanations 
Description: The API accepts a userID and taskID and returns an explanation of why a particular user is fit for the task

#### /social/explanations/{userID}/{taskID}/

Example call: 
`http://0.0.0.0:5000/social/explanations/U100047/T100093`

## Live environment OUC endpoints
### Social relations : 

`http://82.116.211.98:8081/social/relations/2`

### Social preferences:

`http://82.116.211.98:8081/social/preferences/2/5ebd800528b21a1bc194e2c8`

### Social explanations:

`http://82.116.211.98:8081/social/explanations/2/5ebd800528b21a1bc194e2c8`

### Documentation

The APIs documentation is available [here](http://swagger.u-hopper.com/?url=https://bitbucket.org/wenet/wenet-components-documentation/raw/master/sources/wenet-social_context_builder-openapi.json).

### Maintainers

Christos Michail (christos.michail@ouc.ac.cy)




