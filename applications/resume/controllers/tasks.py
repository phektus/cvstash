import random

def build_landingpage_users():
    # clean up the table
    db(db.landing_page_users.id>0).delete()
    MAX_USERS = 12

    users = db(db.auth_user.id>0).select().sort(lambda row: random.random())[0:MAX_USERS]

    for user in users:
        profile = db(db.userprofile.owner==user.id).select().first()
        settings = db(db.usersettings.owner==user.id).select().first()
        contactinfo = db(db.contactinfo.owner==user.id).select().first()

        if profile and settings and contactinfo:
            db.landing_page_users.insert(owner=user.id,
                first_name=profile.first_name or '',
                last_name=profile.last_name or '',
                resumeurl=settings.resumeurl or '',
                email=user.email or contactinfo.email or '',
                title=profile.title or '')

def build_landingpage_stats():
    db(db.landing_page_stats.id>0).delete()
    profile_count = db(db.userprofile.id > 0).count()
    db.landing_page_stats.insert(profile_count=profile_count)
