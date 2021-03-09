from FlaskApp import db
import json
import requests

COMP_AUTH_KEY = 'zJ9fwKb1CzeJT7zik_2VYpIBc_yclwX4Vd7_lO9sDlo'
PROFILE_MANAGER_API = 'https://wenet.u-hopper.com/dev/profile_manager'
class SocialProfile(db.Model):
    userId = db.Column(db.String(80), primary_key=True) #wenetid
    source = db.Column(db.String(50), nullable=False)
    sourceId = db.Column(db.String(80), primary_key=True, unique=True, nullable=False)
    gender = db.Column(db.String(20), nullable=True)
    hometown = db.Column(db.String(80), nullable=True)
    ts = db.Column(db.Integer, nullable=True)


    def __repr__(self):
        return '<User %r>' % self.userId

    def get_userId_from_sourceId(self, sourceId):
        print('searching for', sourceId)
        user = SocialProfile.query.filter(SocialProfile.sourceId == sourceId).first()
        if user:
            return user.userId
        else:
            return False
    @staticmethod
    def parse(streamdata):
        try:
            profile = streamdata['socialprofile']
            social_profile = SocialProfile(userId=profile['userId'], source=profile['payload']['source'],
                                           sourceId=profile['payload']['sourceid'], gender=profile['payload']['gender'],
                                           hometown=profile['payload']['hometown'], ts=int(profile['ts']))
            try:
                profile_already_in_db = SocialProfile.query.filter((SocialProfile.userId == social_profile.userId)
                                                                   & (SocialProfile.sourceId == social_profile.sourceId)).first()
                if not profile_already_in_db:
                    db.session.add(social_profile)
            except Exception as error:
                print('exception while trying to add to db session ', error)
            db.session.commit()
        except Exception as error:
            print('exception in parsing social profile in db commit!!! ', error)

        return {}


class SocialRelations(db.Model):
    userId = db.Column(db.String(80), primary_key=True)  # wenetid
    source = db.Column(db.String(50), nullable=False, primary_key=True)
    userDestinationId = db.Column(db.String(80), primary_key=True, unique=True, nullable=False)
    eventType = db.Column(db.String(20), primary_key=True)
    value = db.Column(db.String(200), primary_key=True)
    ts = db.Column(db.Integer)

    def __repr__(self):
        return '<User %r>' % self.userId

    def weigh_social_relations(self, userId):
        social_relations = SocialRelations.query.filter((SocialRelations.userId == userId)
                                                              & (SocialRelations.eventType == 'friend')).all()
        relationships=[]
        sp = SocialProfile()
        for social_relation in social_relations:
            user_id_from_destination_id = sp.get_userId_from_sourceId(social_relation.userDestinationId)
            relationships.append({'userId': user_id_from_destination_id, 'type': social_relation.eventType, 'weight': 0.5})
        for relationship in relationships:
            try:
                data = json.dumps(relationship)
                headers = {'connection': 'keep-alive',
                           'x-wenet-component-apikey': COMP_AUTH_KEY,
                           'Content-Type': 'application/json'}
                r = requests.post(PROFILE_MANAGER_API + '/profiles/' + str(userId) + '/relationships', data=data, headers=headers)
            except requests.exceptions.HTTPError as e:
                print('Issue with Profile manager', r.status_code)
        return {}

    @staticmethod
    def parse(streamdata):
        try:
            social_relation = streamdata['socialrelations']
            social_relation = SocialRelations(userId=social_relation['userId'],
                                           source=social_relation['payload']['source'],
                                           userDestinationId=social_relation['payload']['content']['userdestinationid'],
                                           eventType=social_relation['payload']['content']['eventtype'],
                                           value=social_relation['payload']['content']['value'],
                                           ts=int(social_relation['ts']))
            try:
                relation_already_in_db = SocialRelations.query.filter((SocialRelations.userId == social_relation.userId)
                                                                      &(SocialRelations.userDestinationId == social_relation.userDestinationId)
                                                                      & (SocialRelations.source == social_relation.source)).first()
                if not relation_already_in_db:
                    db.session.add(social_relation)
            except Exception as error:
                print('exception while trying to add to db ', error)
            db.session.commit()
        except Exception as error:
            print('exception !!! ', error )
        return {}
